from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count
import json
import time
import concurrent.futures
from .models import Patient, DiagnosticInput, DiagnosticReport
from .forms import UploadFilesForm
from graph.pipeline import build_pipeline
from agents.extraction_agent import extract_patient_data
from agents.ecg_agent import analyze_ecg
from agents.imaging_agent import analyze_echo
from agents.biomarker_agent import analyze_biomarkers


def _serialize_dashboard_data():
    """Serialize dashboard data for React frontend."""
    recent_reports = DiagnosticReport.objects.select_related(
        "patient"
    ).order_by("-created_at")[:20]

    reports_data = []
    for r in recent_reports:
        reports_data.append({
            "id": r.id,
            "patient_name": r.patient.name or "Unknown Patient",
            "patient_age": r.patient.age,
            "patient_sex": r.patient.sex or "—",
            "risk_level": r.risk_level,
            "confidence_score": round(r.confidence_score, 1) if r.confidence_score else 0,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "doctor_confirmed": r.doctor_confirmed,
            "final_report": r.final_report or "",
            "ecg_findings": r.ecg_findings or {},
            "biomarker_findings": r.biomarker_findings or {},
            "imaging_findings": r.imaging_findings or {},
            "recommended_actions": r.recommended_actions or [],
            "processing_time_seconds": round(r.processing_time_seconds, 1) if r.processing_time_seconds else None,
            "loop_count": r.loop_count,
            "agent_agreement": r.agent_agreement,
        })

    # Aggregate stats
    agg = DiagnosticReport.objects.aggregate(
        avg_confidence=Avg("confidence_score"),
        avg_processing=Avg("processing_time_seconds"),
        total=Count("id"),
    )

    critical_count = DiagnosticReport.objects.filter(
        risk_level="CRITICAL", doctor_confirmed=False
    ).count()

    # Risk distribution
    risk_counts = dict(
        DiagnosticReport.objects.values_list("risk_level")
        .annotate(c=Count("id"))
        .values_list("risk_level", "c")
    )

    return {
        "reports": reports_data,
        "stats": {
            "critical_count": critical_count,
            "total_reports": agg["total"] or 0,
            "avg_confidence": round(agg["avg_confidence"] or 0, 1),
            "avg_processing_time": round(agg["avg_processing"] or 0, 1),
        },
        "risk_distribution": {
            "CRITICAL": risk_counts.get("CRITICAL", 0),
            "HIGH": risk_counts.get("HIGH", 0),
            "MODERATE": risk_counts.get("MODERATE", 0),
            "LOW": risk_counts.get("LOW", 0),
            "INCONCLUSIVE": risk_counts.get("INCONCLUSIVE", 0),
        },
    }


def dashboard(request):
    dashboard_data = _serialize_dashboard_data()
    context = {
        "dashboard_json": json.dumps(dashboard_data),
    }
    return render(request, "emergency/dashboard.html", context)


def dashboard_api(request):
    """JSON API for React dashboard refresh."""
    return JsonResponse(_serialize_dashboard_data())

@csrf_exempt
def upload_patient(request):
    if request.method == "POST":
        upload_form = UploadFilesForm(request.POST, request.FILES)
        
        if upload_form.is_valid():
            patient = Patient.objects.create()  # Leave fields empty for Gemini
            diagnostic_input = upload_form.save(commit=False)
            diagnostic_input.patient = patient
            diagnostic_input.save()
            
            # Return JSON for React frontend
            return JsonResponse({
                "status": "ok",
                "patient_id": str(patient.patient_id),
            })
        else:
            return JsonResponse({"status": "error", "error": "Invalid form data"}, status=400)
    
    return JsonResponse({"status": "error", "error": "POST required"}, status=405)

def processing(request, patient_id):
    patient = Patient.objects.get(patient_id=patient_id)
    return render(request, "emergency/processing.html", {
        "patient": patient,
    })

def run_pipeline_sync(request, patient_id):
    start_time = time.time()
    try:
        patient = Patient.objects.get(patient_id=patient_id)
        inputs = patient.inputs
        
        # 1. AI Extraction from Report PDF/Image
        vitals_data = {}
        if inputs.report_file:
            print("Extracting vitals via Gemini 2.5 Flash...")
            vitals_data = extract_patient_data(inputs.report_file.path)
            
            # Save extracted data back to the database
            patient.name = vitals_data.get("name") or patient.name
            patient.age = vitals_data.get("age") or patient.age
            patient.sex = vitals_data.get("sex") or patient.sex
            if vitals_data.get("symptoms"):
                patient.symptoms = vitals_data.get("symptoms")
            patient.onset_time = vitals_data.get("onset_time") or patient.onset_time
            patient.save()
            
            inputs.heart_rate = vitals_data.get("heart_rate")
            inputs.systolic_bp = vitals_data.get("systolic_bp")
            inputs.troponin = vitals_data.get("troponin")
            inputs.bnp = vitals_data.get("bnp")
            inputs.ldl = vitals_data.get("ldl")
            inputs.hba1c = vitals_data.get("hba1c")
            inputs.creatinine = vitals_data.get("creatinine")
            inputs.ckmb = vitals_data.get("ckmb")
            inputs.save()
            
        # 2. Fire APIs Simultaneously (Colab Endpoints)
        print("Running Colab agents concurrently...")
        ecg_path = inputs.ecg_file.path if inputs.ecg_file else None
        echo_path = inputs.echo_file.path if inputs.echo_file else None
        
        # Prepare inputs for biomarker agent based on extraction
        biomarker_dict = {
            "troponin": inputs.troponin,
            "bnp": inputs.bnp,
            "ldl": inputs.ldl,
            "hba1c": inputs.hba1c,
            "creatinine": inputs.creatinine,
            "ckmb": inputs.ckmb,
            "heart_rate": inputs.heart_rate,
            "systolic_bp": inputs.systolic_bp
        }
        
        ecg_res, echo_res, biomarker_res = None, None, None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_ecg = executor.submit(analyze_ecg, ecg_path) if ecg_path else None
            future_echo = executor.submit(analyze_echo, echo_path) if echo_path else None
            future_bio = executor.submit(analyze_biomarkers, biomarker_dict)
            
            ecg_res = future_ecg.result() if future_ecg else {}
            echo_res = future_echo.result() if future_echo else {}
            biomarker_res = future_bio.result()
            
        print("Agents finished. Proceeding to LangGraph reasoning.")
        
        # 3. LangGraph Reasoning Pipeline
        pipeline = build_pipeline()
        result = pipeline.invoke({
            "patient_id": str(patient.patient_id),
            "symptoms": patient.symptoms.split(",") if patient.symptoms else [],
            "onset_time": patient.onset_time or "",
            "blood_values": biomarker_dict,
            "ecg_data": ecg_path or "",
            "echo_path": echo_path or "",
            "ecg_findings": ecg_res,
            "biomarker_findings": biomarker_res,
            "imaging_findings": echo_res,
        })
        
        processing_time = time.time() - start_time
        
        report = DiagnosticReport.objects.create(
            patient=patient,
            ecg_findings=result.get("ecg_findings", ecg_res),
            biomarker_findings=result.get("biomarker_findings", biomarker_res),
            imaging_findings=result.get("imaging_findings", echo_res),
            risk_level=result.get("risk_level", "INCONCLUSIVE"),
            final_report=result.get("final_report", ""),
            confidence_score=result.get("confidence_score", 0),
            recommended_actions=result.get("recommended_actions", []),
            loop_count=result.get("loop_count", 0),
            agent_agreement=result.get("agent_agreement", True),
            processing_time_seconds=processing_time
        )
        
        return JsonResponse({
            "status": "complete",
            "risk_level": report.risk_level,
            "report_id": report.id
        })
    except Exception as e:
        print(f"Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({"status": "failed", "error": str(e)})

def view_report(request, report_id):
    report = DiagnosticReport.objects.select_related(
        "patient"
    ).get(id=report_id)
    
    return render(request, "emergency/report.html", {
        "report": report,
        "patient": report.patient
    })


def report_api(request, report_id):
    """JSON API for React report page."""
    try:
        r = DiagnosticReport.objects.select_related("patient").get(id=report_id)
    except DiagnosticReport.DoesNotExist:
        return JsonResponse({"error": "Report not found"}, status=404)
    
    return JsonResponse({
        "id": r.id,
        "patient_name": r.patient.name or "Unknown Patient",
        "patient_age": r.patient.age,
        "patient_sex": r.patient.sex or "—",
        "risk_level": r.risk_level,
        "confidence_score": round(r.confidence_score, 1) if r.confidence_score else 0,
        "final_report": r.final_report or "",
        "ecg_findings": r.ecg_findings or {},
        "biomarker_findings": r.biomarker_findings or {},
        "imaging_findings": r.imaging_findings or {},
        "recommended_actions": r.recommended_actions or [],
        "processing_time_seconds": round(r.processing_time_seconds, 1) if r.processing_time_seconds else None,
        "doctor_confirmed": r.doctor_confirmed,
        "loop_count": r.loop_count,
        "agent_agreement": r.agent_agreement,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    })


@csrf_exempt
@require_POST
def doctor_confirm(request, report_id):
    report = DiagnosticReport.objects.get(id=report_id)
    action = request.POST.get("action")
    
    if action == "confirm":
        report.doctor_confirmed = True
    elif action == "override":
        report.doctor_override = True
        report.doctor_notes = request.POST.get("notes")
    
    report.save()
    return JsonResponse({"status": "saved"})

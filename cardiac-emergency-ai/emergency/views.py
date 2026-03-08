from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import time
import concurrent.futures
from .models import Patient, DiagnosticInput, DiagnosticReport
from .forms import UploadFilesForm
from graph.pipeline import build_pipeline
from agents.extraction_agent import extract_patient_data
from agents.ecg_agent import analyze_ecg
from agents.imaging_agent import analyze_xray
from agents.biomarker_agent import analyze_biomarkers

def dashboard(request):
    recent_reports = DiagnosticReport.objects.select_related(
        "patient"
    ).order_by("-created_at")[:10]
    
    context = {
        "recent_reports": recent_reports,
        "critical_count": DiagnosticReport.objects.filter(
            risk_level="CRITICAL",
            doctor_confirmed=False
        ).count()
    }
    return render(request, "emergency/dashboard.html", context)

def upload_patient(request):
    if request.method == "POST":
        upload_form = UploadFilesForm(request.POST, request.FILES)
        
        if upload_form.is_valid():
            patient = Patient.objects.create() # Leave fields empty for Gemini
            diagnostic_input = upload_form.save(commit=False)
            diagnostic_input.patient = patient
            diagnostic_input.save()
            
            return redirect(
                "processing",
                patient_id=patient.patient_id
            )
    else:
        upload_form = UploadFilesForm()
    
    return render(request, "emergency/upload.html", {
        "upload_form": upload_form
    })

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
        xray_path = inputs.xray_file.path if inputs.xray_file else None
        
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
        
        ecg_res, xray_res, biomarker_res = None, None, None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_ecg = executor.submit(analyze_ecg, ecg_path) if ecg_path else None
            future_xray = executor.submit(analyze_xray, xray_path) if xray_path else None
            future_bio = executor.submit(analyze_biomarkers, biomarker_dict)
            
            ecg_res = future_ecg.result() if future_ecg else {}
            xray_res = future_xray.result() if future_xray else {}
            biomarker_res = future_bio.result()
            
        print("Agents finished. Proceeding to LangGraph reasoning.")
        
        # 3. LangGraph Reasoning Pipeline
        pipeline = build_pipeline()
        result = pipeline.invoke({
            "patient_id": str(patient.patient_id),
            "symptoms": patient.symptoms.split(",") if patient.symptoms else [],
            "onset_time": patient.onset_time,
            "blood_values": biomarker_dict,
            "ecg_data": ecg_res,
            "xray_path": xray_res
        })
        
        processing_time = time.time() - start_time
        
        report = DiagnosticReport.objects.create(
            patient=patient,
            ecg_findings=result.get("ecg_findings", ecg_res),
            biomarker_findings=result.get("biomarker_findings", biomarker_res),
            imaging_findings=result.get("imaging_findings", xray_res),
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

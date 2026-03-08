import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cardiac_project.settings")
django.setup()

from emergency.models import Patient, DiagnosticInput, CeleryTask
from emergency.tasks import run_cardiac_analysis

def test_pipeline():
    print("Creating mock patient...")
    patient = Patient.objects.create(
        name="Test Patient 001",
        age=65,
        sex="M",
        symptoms="Chest pain, Shortness of breath",
        onset_time="1 hour ago"
    )
    
    diagnostic = DiagnosticInput.objects.create(
        patient=patient,
        troponin=120.5,
        bnp=550.0,
        ldl=145.0,
        hba1c=6.8,
        creatinine=1.2,
        ckmb=8.4
    )
    
    print(f"Created patient {patient.patient_id}. Running analyzer...")
    try:
        run_cardiac_analysis(str(patient.patient_id))
        from emergency.models import DiagnosticReport
        report = DiagnosticReport.objects.filter(patient=patient).latest('created_at')
        print(f"Outcome Risk Level: {report.risk_level}")
        print(f"Confidence: {report.confidence_score}")
        print(f"Final Report: {report.final_report}")
        print("Pipeline execution COMPLETE and SUCCESSFUL!")
    except Exception as e:
        print(f"Error testing pipeline: {e}")

if __name__ == "__main__":
    test_pipeline()

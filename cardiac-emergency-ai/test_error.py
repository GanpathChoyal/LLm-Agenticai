import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cardiac_project.settings")
django.setup()

from django.test import Client
from emergency.models import Patient

def run_test():
    latest_patient = Patient.objects.order_by("-arrival_time").first()
    if not latest_patient:
        print("No patients found in DB.")
        return
        
    print(f"Testing pipeline for patient: {latest_patient.patient_id}")
    client = Client()
    response = client.get(f"/process/{latest_patient.patient_id}/")
    print(f"Response status: {response.status_code}")
    print(f"Response JSON: {response.json()}")

if __name__ == "__main__":
    run_test()

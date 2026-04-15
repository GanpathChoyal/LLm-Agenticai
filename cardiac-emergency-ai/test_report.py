import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardiac_project.settings')
django.setup()

from emergency.models import DiagnosticReport

latest = DiagnosticReport.objects.order_by('-created_at').first()
if latest:
    print(f"Report ID: {latest.id}")
    print(f"Risk: {latest.risk_level}")
    print("ECG:", json.dumps(latest.ecg_findings, indent=2))
    print("Biomarker:", json.dumps(latest.biomarker_findings, indent=2))
    print("Imaging:", json.dumps(latest.imaging_findings, indent=2))
    print("Discordant:", json.dumps(latest.discordant_agents, indent=2))
    print("Report Context:", latest.final_report)
else:
    print("No reports found.")

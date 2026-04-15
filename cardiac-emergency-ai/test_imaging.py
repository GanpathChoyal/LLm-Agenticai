import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cardiac_project.settings')
django.setup()

from agents.imaging_agent import analyze_echo
import glob

# Pick the latest uploaded echo mp4
echo_files = glob.glob(r"d:\LLMproject\cardiac-emergency-ai\media\echo_uploads\*.mp4")
if not echo_files:
    print("No echo MP4 files found!")
else:
    latest = sorted(echo_files)[-1]
    print(f"Testing with: {latest}")
    result = analyze_echo(latest)
    import json
    print(json.dumps(result, indent=2))

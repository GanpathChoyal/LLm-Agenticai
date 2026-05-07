import os
from google import genai
import json

api_key = os.environ.get("EXTRACTION_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
extraction_prompt = """
You are a medical data extraction AI. Extract the following patient demographics and laboratory vitals from the provided clinical report image/PDF.

Return ONLY a perfectly formatted JSON object with the exact following keys. If a value is missing or not found in the report, use null for that key.

{
    "name": "string",
    "age": int,
    "sex": "M" or "F",
    "symptoms": "string (comma separated list or short summary)",
    "onset_time": "string (e.g., '2 hours ago', '14:30')",
    "heart_rate": int (bpm),
    "systolic_bp": int (mmHg),
    "troponin": float (ng/mL),
    "bnp": float (pg/mL),
    "ldl": float (mg/dL),
    "hba1c": float (%),
    "creatinine": float (mg/dL),
    "ckmb": float (ng/mL)
}
"""

def extract_patient_data(report_path):
    """
    Extracts vitals and demographics from a report image using Gemini 2.5 Flash.
    """
    
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Report file not found: {report_path}")

    try:
        if report_path.lower().endswith('.pdf'):
            import pathlib
            file_bytes = pathlib.Path(report_path).read_bytes()
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=[
                    genai.types.Part.from_bytes(data=file_bytes, mime_type='application/pdf'),
                    extraction_prompt
                ]
            )
        else:
            from PIL import Image
            img = Image.open(report_path)
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=[extraction_prompt, img]
            )
        
        # Clean up any potential markdown formatting in the response
        json_str = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_str)
        return data
        
    except Exception as e:
        print(f"Error during Gemini extraction: {e}")
        return {}

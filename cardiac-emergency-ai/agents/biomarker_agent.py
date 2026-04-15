import os
import requests
import urllib3
import json
import google.generativeai as genai
from django.conf import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def analyze_biomarkers_with_gemini(blood_values: dict) -> dict:
    """Local Gemini fallback for biomarker analysis."""
    print("[Biomarker Agent] Using Gemini fallback for biomarker analysis.")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""You are a specialist cardiologist AI analyzing blood biomarker results.
    Analyze the following blood values and return ONLY raw JSON (no markdown, no code blocks):
    {{
        "agent": "Biomarker Agent",
        "model": "Gemini-2.5-Flash",
        "status": "success",
        "findings": ["finding1", "finding2"],
        "risk_flags": ["flag1"],
        "risk_direction": "LOW|MODERATE|HIGH|CRITICAL|INCONCLUSIVE",
        "confidence": 85,
        "reanalysis_needed": false,
        "raw_output": {{}}
    }}
    
    Patient Blood Values:
    {json.dumps(blood_values, indent=2)}
    
    Evaluate each value clinically. Include Shock Index (heart_rate / systolic_bp) if both present.
    Normal thresholds: troponin < 14 ng/L, BNP < 100 pg/mL, LDL < 3.4 mmol/L, HbA1c < 5.7%, creatinine 0.7-1.3 mg/dL.
    """

    response = model.generate_content(prompt)
    content = response.text.replace("```json", "").replace("```", "").strip()
    start_idx = content.find('{')
    end_idx = content.rfind('}') + 1
    result = json.loads(content[start_idx:end_idx])
    print(f"[Biomarker Agent] Gemini analysis complete. Risk: {result.get('risk_direction')}")
    return result


def analyze_biomarkers(blood_values: dict) -> dict:
    """
    Calls the Colab endpoint to analyze blood biomarker values.
    Falls back to local Gemini if Colab is unavailable.
    """
    try:
        # Filter out None values — but keep 0.0 (valid medical reading)
        cleaned_values = {k: v for k, v in blood_values.items() if v is not None}
        if not cleaned_values:
            print("[Biomarker Agent] WARNING: No blood values extracted. Sending defaults.")
            cleaned_values = {
                "heart_rate": 0, "systolic_bp": 0,
                "troponin": 0.0, "bnp": 0.0,
                "ldl": 0.0, "hba1c": 0.0,
                "creatinine": 0.0, "ckmb": 0.0
            }
        print(f"[Biomarker Agent] Sending values: {cleaned_values}")

        base_url = settings.COLAB_API_BASE
        url = f"{base_url}/analyze-biomarkers"

        response = requests.post(url, json=cleaned_values, timeout=30, verify=False)
        response.raise_for_status()
        result = response.json()

        # If Colab returned error/skipped, use Gemini fallback
        if result.get("status") == "error" or result.get("status") == "skipped":
            print("[Biomarker Agent] Colab returned error/skipped. Switching to Gemini fallback.")
            return analyze_biomarkers_with_gemini(cleaned_values)

        return result

    except Exception as e:
        print(f"[Biomarker Agent] Colab failed: {e}. Attempting Gemini fallback.")
        try:
            cleaned_values = {k: v for k, v in blood_values.items() if v is not None}
            return analyze_biomarkers_with_gemini(cleaned_values or blood_values)
        except Exception as fallback_err:
            return {
                "agent": "Biomarker Agent",
                "model": "Gemini (Fallback)",
                "status": "error",
                "findings": [f"Biomarker analysis failed: {str(fallback_err)}. Manual review needed."],
                "risk_flags": [],
                "risk_direction": "INCONCLUSIVE",
                "confidence": 0,
                "reanalysis_needed": True,
                "raw_output": blood_values if blood_values else {}
            }

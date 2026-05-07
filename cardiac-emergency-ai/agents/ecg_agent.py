import os
import requests
import urllib3
import base64
from google import genai
from PIL import Image as PILImage
from django.conf import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def analyze_ecg_with_gemini(ecg_path: str) -> dict:
    """Local Gemini Vision fallback for ECG analysis."""
    print("[ECG Agent] Using Gemini Vision fallback for ECG analysis.")
    api_key = os.getenv("ECG_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("ECG_GEMINI_API_KEY or GEMINI_API_KEY not set.")

    client = genai.Client(api_key=api_key)

    prompt = """You are a specialist cardiologist AI analyzing a 12-lead ECG image.
    Analyze this ECG and return ONLY raw JSON (no markdown, no code blocks) in this exact format:
    {
        "agent": "ECG Agent",
        "model": "Gemini-2.0-Flash",
        "status": "success",
        "findings": ["finding1", "finding2"],
        "risk_flags": ["flag1"],
        "risk_direction": "LOW|MODERATE|HIGH|CRITICAL|INCONCLUSIVE",
        "confidence": 85,
        "reanalysis_needed": false,
        "raw_output": {}
    }
    Analyze rhythm, rate, axis, intervals (PR, QRS, QT), ST segments, T waves, Q waves, and R wave progression.
    Be specific and clinically accurate. If image is unclear, state that in findings.
    """

    pil_image = PILImage.open(ecg_path)
    response = client.models.generate_content(
        model='gemini-flash-latest',
        contents=[prompt, pil_image]
    )
    content = response.text.replace("```json", "").replace("```", "").strip()
    start_idx = content.find('{')
    end_idx = content.rfind('}') + 1
    result = __import__('json').loads(content[start_idx:end_idx])
    print(f"[ECG Agent] Gemini analysis complete. Risk: {result.get('risk_direction')}")
    return result


def analyze_ecg(ecg_data: str) -> dict:
    """
    Calls the Colab endpoint to analyze the ECG image.
    Falls back to local Gemini Vision if Colab is unavailable.
    """
    try:
        base_url = settings.COLAB_API_BASE
        url = f"{base_url}/analyze-ecg"
        with open(ecg_data, 'rb') as f:
            encoded_image = base64.b64encode(f.read()).decode('utf-8')

        payload = {"ecg_image_base64": encoded_image}
        print(f"[ECG Agent] Sending to Colab: {url}")
        response = requests.post(url, json=payload, timeout=30, verify=False)
        response.raise_for_status()
        result = response.json()

        # If Colab returned an error status, use Gemini fallback
        if result.get("status") == "error" or result.get("status") == "skipped":
            print("[ECG Agent] Colab returned error/skipped. Switching to Gemini fallback.")
            return analyze_ecg_with_gemini(ecg_data)

        return result

    except Exception as e:
        print(f"[ECG Agent] Colab failed: {e}. Attempting Gemini Vision fallback.")
        try:
            return analyze_ecg_with_gemini(ecg_data)
        except Exception as fallback_err:
            return {
                "agent": "ECG Agent",
                "model": "Gemini Vision (Fallback)",
                "status": "error",
                "findings": [f"ECG analysis failed: {str(fallback_err)}. Manual review needed."],
                "risk_flags": [],
                "risk_direction": "INCONCLUSIVE",
                "confidence": 0,
                "reanalysis_needed": True,
                "raw_output": {}
            }


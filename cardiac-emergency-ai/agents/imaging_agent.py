import os
import requests
import urllib3
import base64
import mimetypes
import cv2
import google.generativeai as genai
from PIL import Image as PILImage
from django.conf import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def extract_echo_frame(echo_path: str):
    """
    Returns (encoded_image_b64, frame_numpy_array) from either image or video.
    """
    mime_type, _ = mimetypes.guess_type(echo_path)
    is_video = mime_type and mime_type.startswith('video/')

    if is_video:
        cap = cv2.VideoCapture(echo_path)
        if not cap.isOpened():
            print(f"[Imaging Agent] FAILED: Could not open video {echo_path}")
            raise ValueError("Could not open video file.")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        mid_frame = 0
        if total_frames > 0:
            mid_frame = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)

        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("[Imaging Agent] FAILED: Could not read frame from video.")
            raise ValueError("Could not read frame from video.")

        # Save debug copy
        debug_path = os.path.join(settings.BASE_DIR, 'media', 'debug_extracted_frame.jpg')
        cv2.imwrite(debug_path, frame)
        print(f"[Imaging Agent] SUCCESS: Extracted frame {mid_frame} / {total_frames} from Echo video.")
        print(f"[Imaging Agent] Debug copy saved to: {debug_path}")

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            raise ValueError("Could not encode video frame to JPEG.")

        encoded = base64.b64encode(buffer).decode('utf-8')
        return encoded, frame

    else:
        with open(echo_path, 'rb') as f:
            raw = f.read()
        encoded = base64.b64encode(raw).decode('utf-8')
        print(f"[Imaging Agent] Image file loaded: {echo_path}")
        return encoded, None


def analyze_echo_with_gemini(echo_path: str, frame=None) -> dict:
    """
    Local fallback: analyze the Echo frame using Gemini Vision directly.
    """
    print("[Imaging Agent] Colab endpoint skipped — using Gemini Vision fallback.")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set for local fallback.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = """You are a specialist cardiac imaging AI analyzing an echocardiogram (cardiac ultrasound).
    Analyze this image and return ONLY raw JSON (no markdown, no code blocks) in this exact format:
    {
        "agent": "Imaging Agent",
        "model": "Gemini-2.5-Flash",
        "status": "success",
        "findings": ["finding1", "finding2"],
        "risk_flags": ["flag1"],
        "risk_direction": "LOW|MODERATE|HIGH|CRITICAL|INCONCLUSIVE",
        "confidence": 85,
        "reanalysis_needed": false,
        "raw_output": {}
    }
    Provide real clinical imaging findings based on what you see. If the image is unclear, specify that.
    """

    if frame is not None:
        # Convert OpenCV numpy array to PIL image
        import numpy as np
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = PILImage.fromarray(rgb_frame)
        response = model.generate_content([prompt, pil_image])
    else:
        # Load image from path directly
        pil_image = PILImage.open(echo_path)
        response = model.generate_content([prompt, pil_image])

    content = response.text.replace("```json", "").replace("```", "").strip()
    start_idx = content.find('{')
    end_idx = content.rfind('}') + 1
    result = __import__('json').loads(content[start_idx:end_idx])
    print(f"[Imaging Agent] Gemini Vision analysis complete. Risk: {result.get('risk_direction')}")
    return result


def analyze_echo(echo_path: str) -> dict:
    """
    Calls the Colab endpoint to analyze the Echo (cardiac ultrasound) image or video frame.
    Falls back to local Gemini Vision if Colab returns a skipped/empty result.
    """
    frame = None
    try:
        encoded_image, frame = extract_echo_frame(echo_path)

        base_url = settings.COLAB_API_BASE
        url = f"{base_url}/analyze-echo"
        payload = {"echo_image_base64": encoded_image}

        print(f"[Imaging Agent] Sending to Colab: {url}")
        response = requests.post(url, json=payload, timeout=60, verify=False)
        response.raise_for_status()
        result = response.json()

        # If Colab explicitly skipped the analysis, use Gemini fallback
        if result.get("status") == "skipped" or "No echo" in str(result.get("findings", [])):
            print("[Imaging Agent] Colab returned skipped. Switching to Gemini Vision fallback.")
            return analyze_echo_with_gemini(echo_path, frame)

        return result

    except Exception as e:
        print(f"[Imaging Agent] Colab failed: {e}. Attempting Gemini Vision fallback.")
        try:
            return analyze_echo_with_gemini(echo_path, frame)
        except Exception as fallback_err:
            print(f"[Imaging Agent] Gemini fallback also failed: {fallback_err}")
            return {
                "agent": "Imaging Agent",
                "model": "Gemini Vision (Fallback)",
                "status": "error",
                "findings": [f"Both Colab and Gemini fallback failed: {str(fallback_err)}"],
                "risk_flags": [],
                "risk_direction": "INCONCLUSIVE",
                "confidence": 0,
                "reanalysis_needed": True,
                "raw_output": {}
            }


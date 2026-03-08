import os
import requests

def analyze_ecg(ecg_data: str) -> dict:
    """
    Calls the Colab endpoint to analyze the ECG image.
    """
    try:
        url = f"{os.getenv('COLAB_NGROK_URL', 'http://localhost')}/analyze-ecg"
        with open(ecg_data, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files, timeout=30)
            
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        return {
            "agent": "ECG Agent",
            "model": "Colab Endpoint",
            "status": "error",
            "findings": [f"Error processing ECG via Colab: {str(e)}"],
            "risk_flags": [],
            "risk_direction": "INCONCLUSIVE",
            "confidence": 0,
            "reanalysis_needed": False,
            "raw_output": {}
        }

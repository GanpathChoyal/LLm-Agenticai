import os
import requests

def analyze_biomarkers(blood_values: dict) -> dict:
    """
    Calls the Colab endpoint to analyze blood biomarker values.
    """
    try:
        if not blood_values:
            raise ValueError("No blood values provided")
            
        url = f"{os.getenv('COLAB_NGROK_URL', 'http://localhost')}/analyze-biomarkers"
        response = requests.post(url, json=blood_values, timeout=30)
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        return {
            "agent": "Biomarker Agent",
            "model": "Colab Endpoint",
            "status": "error",
            "findings": [f"Error processing biomarkers via Colab: {str(e)}"],
            "risk_flags": [],
            "risk_direction": "INCONCLUSIVE",
            "confidence": 0,
            "reanalysis_needed": False,
            "raw_output": blood_values if blood_values else {}
        }

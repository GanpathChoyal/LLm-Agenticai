import os
import json
import google.generativeai as genai

def generate_reasoning_report(state_dict: dict, retrieved_guidelines: str) -> dict:
    """
    Generates a unified emergency report using Gemini.
    Evaluates concordance between agents.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return mock_reasoning_output(state_dict, "No Gemini Key found.")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        system_prompt = """
        You are an expert Cardiac Reasoning AI. Cross-check findings from ECG, Biomarker, and Imaging agents.
        You must output ONLY raw JSON data in the specified format, properly escaped. Do not wrap with ```json or any other text.
        Format:
        {
            "agent": "Reasoning Agent",
            "model": "Gemini",
            "status": "success",
            "findings": ["summary findings"],
            "risk_flags": ["critical flags"],
            "risk_direction": "LOW|MODERATE|HIGH|CRITICAL|INCONCLUSIVE",
            "confidence": 99,
            "reanalysis_needed": false,
            "final_report": "Detailed clinical report...",
            "recommended_actions": ["List of actions"],
            "discordant_agents": []
        }
        """
        
        prompt = f"""
        {system_prompt}

        Patient Data:
        Symptoms: {state_dict.get('symptoms')}
        Onset Time: {state_dict.get('onset_time')}
        
        ECG Findings: {json.dumps(state_dict.get('ecg_findings'))}
        Biomarker Findings: {json.dumps(state_dict.get('biomarker_findings'))}
        Imaging Findings: {json.dumps(state_dict.get('imaging_findings'))}
        
        Relevant Guidelines (RAG):
        {retrieved_guidelines}
        
        Provide the final unified JSON assessment. Evaluate if the patient is normal or abnormal based strictly on the provided findings. If the findings show normal results, the overall risk must be LOW.
        """

        response = model.generate_content(prompt)
        content = response.text.replace("```json", "").replace("```", "").strip()
        
        # Simple JSON extract just in case there's leading/trailing text
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        json_str = content[start_idx:end_idx]
        
        result = json.loads(json_str)
        result["raw_output"] = {"text": content}
        return result
        
    except Exception as e:
        return mock_reasoning_output(state_dict, str(e))

def mock_reasoning_output(state_dict: dict, error_msg: str) -> dict:
    """
    Creates a dynamic fallback output based on the actual state, instead of hardcoding a STEMI.
    """
    ecg = state_dict.get('ecg_findings', {})
    bio = state_dict.get('biomarker_findings', {})
    
    # Simple rule based fallback
    ecg_risk = ecg.get('risk_direction', 'INCONCLUSIVE')
    bio_risk = bio.get('risk_direction', 'INCONCLUSIVE')
    
    risk_level = "MODERATE"
    if ecg_risk == "CRITICAL" or bio_risk == "CRITICAL":
        risk_level = "CRITICAL"
    elif ecg_risk == "LOW" and bio_risk == "LOW":
        risk_level = "LOW"
        
    findings = []
    if ecg.get('findings'):
        findings.extend(ecg['findings'])
    if bio.get('findings'):
         findings.extend(bio['findings'])
         
    return {
        "agent": "Reasoning Agent",
        "model": "Fallback Rule Engine",
        "status": "error" if "error" in error_msg.lower() else "success",
        "findings": findings if findings else [f"Fallback activated due to: {error_msg}"],
        "risk_flags": ["Fallback mode active"],
        "risk_direction": risk_level,
        "confidence": 50,
        "reanalysis_needed": True,
        "final_report": f"System engaged in rule-based fallback. ECG risk: {ecg_risk}. Biomarker risk: {bio_risk}.",
        "recommended_actions": ["Review source data manually", "Consult specialist"],
        "discordant_agents": [],
        "raw_output": {"error": error_msg}
    }

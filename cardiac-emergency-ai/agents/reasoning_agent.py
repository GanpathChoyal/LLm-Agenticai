import os
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

def generate_reasoning_report(state_dict: dict, retrieved_guidelines: str) -> dict:
    """
    Generates a unified emergency report using Claude 3.
    Evaluates concordance between agents.
    """
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_claude_api_key_here":
             # Fallback if no key is provided during testing
            return mock_reasoning_output(state_dict)

        llm = ChatAnthropic(
            model="claude-3-opus-20240229",
            temperature=0.0,
            anthropic_api_key=api_key
        )
        
        system_prompt = """
        You are an expert Cardiac Reasoning AI. Cross-check findings from ECG, Biomarker, and Imaging agents.
        You must output ONLY raw JSON data in the specified format, properly escaped.
        Format:
        {
            "agent": "Reasoning Agent",
            "model": "Claude 3",
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
        Patient Data:
        Symptoms: {state_dict.get('symptoms')}
        Onset Time: {state_dict.get('onset_time')}
        
        ECG Findings: {json.dumps(state_dict.get('ecg_findings'))}
        Biomarker Findings: {json.dumps(state_dict.get('biomarker_findings'))}
        Imaging Findings: {json.dumps(state_dict.get('imaging_findings'))}
        
        Relevant Guidelines (RAG):
        {retrieved_guidelines}
        
        Provide the final unified JSON assessment.
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = llm.invoke(messages)
        content = response.content
        
        # Simple JSON extract
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        json_str = content[start_idx:end_idx]
        
        result = json.loads(json_str)
        result["raw_output"] = {"text": content}
        return result
        
    except Exception as e:
        return {
            "agent": "Reasoning Agent",
            "model": "Claude 3",
            "status": "error",
            "findings": [f"Reasoning error: {str(e)}"],
            "risk_flags": [],
            "risk_direction": "INCONCLUSIVE",
            "confidence": 0,
            "reanalysis_needed": False,
            "final_report": "",
            "recommended_actions": [],
            "discordant_agents": [],
            "raw_output": {}
        }

def mock_reasoning_output(state_dict: dict) -> dict:
    return {
        "agent": "Reasoning Agent",
        "model": "Claude 3 (Mock)",
        "status": "success",
        "findings": ["Concordant findings of STEMI across ECG and biomarkers."],
        "risk_flags": ["STEMI Confirmed", "Immediate Intervention Needed"],
        "risk_direction": "CRITICAL",
        "confidence": 95,
        "reanalysis_needed": False,
        "final_report": "Patient presents with chest pain and confirmed STEMI on ECG. Biomarkers show elevated hs-cTnT (rule-in). Immediate transfer to catheterization lab recommended.",
        "recommended_actions": ["Activate Cath Lab", "Administer Aspirin", "Cardiology Consult"],
        "discordant_agents": [],
        "raw_output": {"mocked": True}
    }

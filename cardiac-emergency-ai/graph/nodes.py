from typing import Dict, Any
from .state import DiagnosticState
from agents.biomarker_agent import analyze_biomarkers
from agents.ecg_agent import analyze_ecg
from agents.imaging_agent import analyze_xray
from agents.reasoning_agent import generate_reasoning_report
from rag.retriever import retrieve_guidelines

def biomarker_node(state: DiagnosticState) -> Dict[str, Any]:
    res = analyze_biomarkers(state.blood_values)
    return {"biomarker_findings": res}

def ecg_node(state: DiagnosticState) -> Dict[str, Any]:
    res = analyze_ecg(state.ecg_data)
    return {"ecg_findings": res}

def imaging_node(state: DiagnosticState) -> Dict[str, Any]:
    res = analyze_xray(state.xray_path)
    return {"imaging_findings": res}

def reasoning_node(state: DiagnosticState) -> Dict[str, Any]:
    guidelines = retrieve_guidelines(state.symptoms)
    res = generate_reasoning_report(state.dict(), guidelines)
    
    return {
        "reasoning_output": res,
        "risk_level": res.get("risk_direction", "INCONCLUSIVE"),
        "final_report": res.get("final_report", ""),
        "confidence_score": res.get("confidence", 0),
        "recommended_actions": res.get("recommended_actions", []),
        "retrieved_guidelines": guidelines,
        "loop_count": state.loop_count + 1
    }

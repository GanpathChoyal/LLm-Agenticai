from typing import Dict, Any
from .state import DiagnosticState
from agents.biomarker_agent import analyze_biomarkers
from agents.ecg_agent import analyze_ecg
from agents.imaging_agent import analyze_echo
from agents.reasoning_agent import generate_reasoning_report
from agents.critic_agent import critique_reasoning
from rag.retriever import retrieve_guidelines

def biomarker_node(state: DiagnosticState) -> Dict[str, Any]:
    if state.biomarker_findings:
        return {}
    res = analyze_biomarkers(state.blood_values)
    return {"biomarker_findings": res}

def ecg_node(state: DiagnosticState) -> Dict[str, Any]:
    if state.ecg_findings:
        return {}
    res = analyze_ecg(state.ecg_data)
    return {"ecg_findings": res}

def imaging_node(state: DiagnosticState) -> Dict[str, Any]:
    if state.imaging_findings:
        return {}
    res = analyze_echo(state.echo_path)
    return {"imaging_findings": res}

def reasoning_node(state: DiagnosticState) -> Dict[str, Any]:
    guidelines = retrieve_guidelines(state.symptoms)
    res = generate_reasoning_report(state.dict(), guidelines)

    # Check for LLM-identified discordance
    discordant_agents = res.get("discordant_agents", [])
    has_discordance = len(discordant_agents) > 0

    # Check for agent technical failures
    agents_failed = False
    if state.ecg_findings and state.ecg_findings.get("status") == "error":
        agents_failed = True
    if state.biomarker_findings and state.biomarker_findings.get("status") == "error":
        agents_failed = True
    if state.imaging_findings and state.imaging_findings.get("status") == "error":
        agents_failed = True

    agent_agreement = not (has_discordance or agents_failed)

    # Safegaurd: Cap confidence at 75% if there is discordance or failure
    raw_confidence = res.get("confidence", 0)
    if not agent_agreement and raw_confidence > 75:
        confidence_score = 75
        print(f"[Reasoning Node] Discordance/failure detected. Capping overconfident score from {raw_confidence}% to 75%.")
    else:
        confidence_score = raw_confidence

    return {
        "reasoning_output": res,
        "risk_level": res.get("risk_direction", "INCONCLUSIVE"),
        "final_report": res.get("final_report", ""),
        "confidence_score": confidence_score,
        "recommended_actions": res.get("recommended_actions", []),
        "retrieved_guidelines": guidelines,
        "loop_count": state.loop_count + 1,
        "agent_agreement": agent_agreement,
        "discordant_agents": discordant_agents,
        "discordant": has_discordance
    }

def critic_node(state: DiagnosticState) -> Dict[str, Any]:
    """
    Reviews the Reasoning Agent's conclusion.
    Applies confidence adjustment and risk override if needed.
    """
    res = critique_reasoning(
        ecg_findings=state.ecg_findings or {},
        biomarker_findings=state.biomarker_findings or {},
        imaging_findings=state.imaging_findings or {},
        reasoning_output=state.reasoning_output or {},
        retrieved_guidelines=state.retrieved_guidelines or ""
    )

    updates = {"critic_output": res}

    # Apply confidence adjustment from critic
    if state.confidence_score is not None:
        adjustment = res.get("confidence_adjustment", 0)
        new_confidence = max(0, min(100, state.confidence_score + adjustment))
        updates["confidence_score"] = new_confidence

    # Apply risk override if critic insists
    risk_override = res.get("risk_override")
    if risk_override and risk_override in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
        print(f"[Critic Agent] Overriding risk from {state.risk_level} to {risk_override}")
        updates["risk_level"] = risk_override

    return updates


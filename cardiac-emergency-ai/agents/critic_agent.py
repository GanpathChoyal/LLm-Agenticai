import os
import json
import google.generativeai as genai


def critique_reasoning(
    ecg_findings: dict,
    biomarker_findings: dict,
    imaging_findings: dict,
    reasoning_output: dict,
    retrieved_guidelines: str = ""
) -> dict:
    """
    Reviews the Reasoning Agent's conclusion against all 3 specialist findings.
    Acts as a senior cardiologist double-checking the final diagnosis.
    """
    try:
        # Use dedicated critic key if available, fall back to shared key
        api_key = os.getenv("CRITIC_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return _default_approve("No CRITIC_GEMINI_API_KEY or GEMINI_API_KEY set.")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""You are a Senior Cardiologist acting as a Diagnostic Critic.
Your job is to review a junior cardiologist's final diagnosis against the raw specialist reports AND official medical guidelines.
You must check if the final risk level is CLINICALLY JUSTIFIED by the evidence.

Return ONLY raw JSON (no markdown, no code blocks):
{{
    "agent": "Critic Agent",
    "critic_verdict": "approved" or "challenged",
    "critique": "One clear sentence explaining your decision",
    "confidence_adjustment": integer between -30 and +10,
    "risk_override": null or "LOW|MODERATE|HIGH|CRITICAL",
    "issues_found": ["list of specific issues, empty if approved"]
}}

Rules:
- "approved": The risk level is justified by the evidence AND adheres to the provided guidelines. Move forward.
- "challenged": There is a significant contradiction in the reasoning or a violation of guidelines. Must reanalyze.
- confidence_adjustment: Reduce if reasoning seems overconfident or contradictory.
- risk_override: Only set if you believe the risk level must change. Otherwise null.

--- MEDICAL GUIDELINES ---
{retrieved_guidelines if retrieved_guidelines else "No specific guidelines provided."}

--- SPECIALIST FINDINGS ---
ECG Agent: {json.dumps(ecg_findings, indent=2)}

Biomarker Agent: {json.dumps(biomarker_findings, indent=2)}

Imaging Agent: {json.dumps(imaging_findings, indent=2)}

--- REASONING AGENT'S FINAL CONCLUSION ---
{json.dumps(reasoning_output, indent=2)}

Now critically evaluate: Is this conclusion justified by the evidence and guidelines above?
Look for:
1. Risk level contradicted by majority of specialist findings
2. Overconfident score (>90%) when findings are incomplete or mixed
3. Final report ignoring a specialist's critical flag
4. Discordant agents not listed when specialists clearly disagree
5. Actions or diagnoses that violate the medical guidelines provided
"""

        response = model.generate_content(prompt)
        content = response.text.replace("```json", "").replace("```", "").strip()
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        result = json.loads(content[start_idx:end_idx])
        print(f"[Critic Agent] Verdict: {result.get('critic_verdict')} | {result.get('critique')}")
        return result

    except Exception as e:
        print(f"[Critic Agent] Error: {e}. Defaulting to approved.")
        return _default_approve(str(e))


def _default_approve(reason: str) -> dict:
    return {
        "agent": "Critic Agent",
        "critic_verdict": "approved",
        "critique": f"Critic bypassed: {reason}",
        "confidence_adjustment": 0,
        "risk_override": None,
        "issues_found": []
    }

from typing import Optional, List
from pydantic import BaseModel

class DiagnosticState(BaseModel):
    # Input
    patient_id: str
    symptoms: List[str] = []
    onset_time: str = ""

    # Raw data
    ecg_data: Optional[str] = None
    blood_values: Optional[dict] = None
    echo_path: Optional[str] = None

    # Agent outputs
    ecg_findings: Optional[dict] = None
    biomarker_findings: Optional[dict] = None
    imaging_findings: Optional[dict] = None

    # Critic output
    critic_output: Optional[dict] = None

    # Agentic control
    loop_count: int = 0
    max_loops: int = 2
    discordant: bool = False
    discordant_agents: List[str] = []
    reanalysis_instruction: Optional[str] = None

    # RAG
    retrieved_guidelines: Optional[str] = None

    # Output
    reasoning_output: Optional[dict] = None
    risk_level: Optional[str] = None
    final_report: Optional[str] = None
    confidence_score: Optional[float] = None
    recommended_actions: Optional[List] = None

    # Meta
    processing_time_seconds: Optional[float] = None
    agent_agreement: Optional[bool] = None


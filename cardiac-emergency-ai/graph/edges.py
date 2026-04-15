from .state import DiagnosticState

def check_concordance_edge(state: DiagnosticState) -> str:
    """
    Determines next step in the graph based on state.
    Returns the name of the next node or 'end'.
    """
    if state.loop_count >= state.max_loops:
        return "end"
        
    reasoning = state.reasoning_output
    if not reasoning:
        return "end"
        
    discordant_agents = reasoning.get("discordant_agents", [])
    if discordant_agents and len(discordant_agents) > 0:
        return "reanalyze"
        
    return "end"


def critic_edge(state: DiagnosticState) -> str:
    """
    Routes after the Critic Agent:
    - 'reanalyze' if critic challenged the diagnosis and loops remain
    - 'end' if approved, or max loops reached
    """
    if state.loop_count >= state.max_loops:
        return "end"

    critic = state.critic_output or {}
    verdict = critic.get("critic_verdict", "approved")

    if verdict == "challenged":
        print(f"[Critic Edge] Diagnosis challenged — routing to reanalysis (loop {state.loop_count}/{state.max_loops})")
        return "reanalyze"

    return "end"

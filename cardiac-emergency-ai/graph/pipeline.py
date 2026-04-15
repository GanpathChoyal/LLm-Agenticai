from langgraph.graph import StateGraph, END, START
from .state import DiagnosticState
from .nodes import biomarker_node, ecg_node, imaging_node, reasoning_node, critic_node
from .edges import check_concordance_edge, critic_edge

def build_pipeline():
    workflow = StateGraph(DiagnosticState)

    # --- Register all nodes ---
    workflow.add_node("biomarker", biomarker_node)
    workflow.add_node("ecg", ecg_node)
    workflow.add_node("imaging", imaging_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("critic", critic_node)

    # --- Build the flow ---
    workflow.add_edge(START, "biomarker")
    workflow.add_edge("biomarker", "ecg")
    workflow.add_edge("ecg", "imaging")
    workflow.add_edge("imaging", "reasoning")

    # After reasoning: check for discordance → critic or end
    workflow.add_conditional_edges(
        "reasoning",
        check_concordance_edge,
        {
            "end": "critic",       # Even on agreement, critic reviews before final
            "reanalyze": "critic"  # On discordance, critic also weighs in first
        }
    )

    # After critic: approved → end, challenged → reanalyze
    workflow.add_conditional_edges(
        "critic",
        critic_edge,
        {
            "end": END,
            "reanalyze": "reasoning"
        }
    )

    return workflow.compile()

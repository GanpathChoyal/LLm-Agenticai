from langgraph.graph import StateGraph, END, START
from .state import DiagnosticState
from .nodes import biomarker_node, ecg_node, imaging_node, reasoning_node
from .edges import check_concordance_edge

def build_pipeline():
    workflow = StateGraph(DiagnosticState)
    
    workflow.add_node("biomarker", biomarker_node)
    workflow.add_node("ecg", ecg_node)
    workflow.add_node("imaging", imaging_node)
    workflow.add_node("reasoning", reasoning_node)
    
    workflow.add_edge(START, "biomarker")
    workflow.add_edge("biomarker", "ecg")
    workflow.add_edge("ecg", "imaging")
    workflow.add_edge("imaging", "reasoning")
    
    workflow.add_conditional_edges(
        "reasoning",
        check_concordance_edge,
        {
            "end": END,
            "reanalyze": "reasoning"
        }
    )
    
    return workflow.compile()

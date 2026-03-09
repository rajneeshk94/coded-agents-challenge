from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import extractor, eligibility_checker, skill_gap_analyzer, responder


def create_graph():

    workflow = StateGraph(AgentState)

    workflow.add_node("extractor", extractor)
    workflow.add_node("eligibility_checker", eligibility_checker)
    workflow.add_node("skill_gap_analyzer", skill_gap_analyzer)
    workflow.add_node("responder", responder)

    workflow.set_entry_point("extractor")

    workflow.add_edge("extractor", "eligibility_checker")
    workflow.add_edge("eligibility_checker", "skill_gap_analyzer")
    workflow.add_edge("skill_gap_analyzer", "responder")

    workflow.add_edge("responder", END)

    return workflow.compile()


appraisal_graph = create_graph()
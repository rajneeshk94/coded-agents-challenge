from typing import List, Literal
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, StateGraph, END
from uipath_langchain.chat import UiPathChat
from pydantic import BaseModel

llm = UiPathChat(model="gpt-4o-mini-2024-07-18")

# ---------------- STATE ----------------

class GraphState(BaseModel):
    subjects: List[str]
    exam_dates: List[str]
    preparation_level: Literal["low", "medium", "high"]
    daily_hours: int
    weak_subjects: List[str]

    risk_level: str | None = None
    study_plan: str | None = None
    plan_quality: str | None = None


class GraphOutput(BaseModel):
    risk_level: str
    study_plan: str


# ---------------- NODE 1: ANALYZE RISK ----------------

async def analyze_risk(state: GraphState) -> GraphState:
    today = datetime.today()
    days_remaining = []

    for date_str in state.exam_dates:
        exam_date = datetime.strptime(date_str, "%Y-%m-%d")
        delta = (exam_date - today).days
        days_remaining.append(max(delta, 1))

    avg_days = sum(days_remaining) / len(days_remaining)
    workload_factor = len(state.subjects) / avg_days

    if state.preparation_level == "low":
        workload_factor *= 1.5
    elif state.preparation_level == "medium":
        workload_factor *= 1.2

    if workload_factor > 0.5:
        risk = "high"
    elif workload_factor > 0.25:
        risk = "medium"
    else:
        risk = "low"

    return state.model_copy(update={"risk_level": risk})


# ---------------- NODE 2A: GENERATE PLAN ----------------

async def generate_plan(state: GraphState) -> GraphState:
    system_prompt = "You are an academic strategy assistant."

    user_prompt = f"""
    Risk level: {state.risk_level}
    Subjects: {state.subjects}
    Weak subjects: {state.weak_subjects}
    Daily hours available: {state.daily_hours}

    Create a structured, practical study plan.
    """

    response = await llm.ainvoke(
        [SystemMessage(system_prompt), HumanMessage(user_prompt)]
    )

    return state.model_copy(update={"study_plan": response.content})


# ---------------- NODE 3: SELF EVALUATION ----------------

async def self_evaluate_plan(state: GraphState) -> GraphState:
    system_prompt = """
You are a critical academic planner reviewer.

Evaluate the study plan quality.
Return only one word:
- good
- poor

Mark 'poor' if:
- unrealistic for given hours
- lacks revision strategy
- vague structure
"""

    response = await llm.ainvoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(state.study_plan or "")
        ]
    )

    quality = response.content.strip().lower()

    return state.model_copy(update={"plan_quality": quality})


# ---------------- NODE 4: IMPROVE PLAN ----------------

async def improve_plan(state: GraphState) -> GraphState:
    system_prompt = "Improve the study plan to make it more realistic and structured."

    response = await llm.ainvoke(
        [
            SystemMessage(system_prompt),
            HumanMessage(state.study_plan or "")
        ]
    )

    return state.model_copy(update={"study_plan": response.content})


# ---------------- ROUTING ----------------

def route_after_risk(state: GraphState):
    return "generate_plan"


def route_after_evaluation(state: GraphState):
    if state.plan_quality == "poor":
        return "improve_plan"
    return END


# ---------------- BUILD GRAPH ----------------

builder = StateGraph(GraphState, output=GraphOutput)

builder.add_node("analyze_risk", analyze_risk)
builder.add_node("generate_plan", generate_plan)
builder.add_node("self_evaluate_plan", self_evaluate_plan)
builder.add_node("improve_plan", improve_plan)

builder.add_edge(START, "analyze_risk")
builder.add_conditional_edges("analyze_risk", route_after_risk)

builder.add_edge("generate_plan", "self_evaluate_plan")
builder.add_conditional_edges(
    "self_evaluate_plan",
    route_after_evaluation,
    path_map={
        "improve_plan": "improve_plan",
        END: END
    }
)

builder.add_edge("improve_plan", END)

graph = builder.compile()

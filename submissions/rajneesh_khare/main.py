from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from uipath.platform.common import CreateTask
from uipath_langchain.chat import UiPathChat
from langchain_core.messages import SystemMessage, HumanMessage
import json, logging

logging.basicConfig(level=logging.INFO)

# LLM
llm = UiPathChat(model="gpt-4o-2024-08-06")

# ---------------- State ----------------
class GraphState(BaseModel):
    question: str | None = None
    student_answer: str | None = None

    evaluation_result: str | None = None
    score: int | None = None
    anomaly_reason: str | None = None

    hitl_required: bool = False


# ---------------- Nodes ----------------
async def evaluate_node(state: GraphState) -> GraphState:
    """
    Agent evaluates student response.
    Returns structured evaluation.
    """

    system_prompt = """
You are an academic evaluator.

Your job:
Evaluate a student's answer to a question.

Return ONLY JSON with:
- score (0–10)
- evaluation_result (short feedback)
- anomaly_reason (null if evaluation is clear)

Mark anomaly_reason if:
- Answer is irrelevant
- Answer is too short to evaluate
- Answer is nonsense
- Question unclear
- Confidence in evaluation is low

Output format:

{
 "score": int,
 "evaluation_result": "feedback",
 "anomaly_reason": null or "reason"
}

Do not include explanations outside JSON.
"""

    output = await llm.ainvoke([
        SystemMessage(system_prompt),
        HumanMessage(
            f"Question:\n{state.question}\n\n"
            f"Student Answer:\n{state.student_answer}"
        )
    ])

    result = json.loads(output.content)

    return state.model_copy(update={
        "evaluation_result": result.get("evaluation_result"),
        "score": result.get("score"),
        "anomaly_reason": result.get("anomaly_reason")
    })


def check_anomaly_node(state: GraphState) -> GraphState:
    """
    Decide if faculty validation is required.
    """

    hitl_required = state.anomaly_reason is not None

    return state.model_copy(update={"hitl_required": hitl_required})


# ---------------- HITL Escalation ----------------
def hitl_node(state: GraphState) -> Command:
    """
    Escalate to faculty for validation.
    """

    action_data = interrupt(
        CreateTask(
            app_name="AssignmentEvaluationApp",
            title="Faculty Review Required: Assignment Evaluation",
            data={
                "Question": state.question,
                "StudentAnswer": state.student_answer,
                "AgentEvaluation": state.evaluation_result or "",
                "AgentScore": state.score or 0,
                "AnomalyReason": state.anomaly_reason or ""
            },
            app_folder_path="Shared"
        )
    )

    updates = {
        "evaluation_result": action_data.get(
            "FacultyEvaluation",
            state.evaluation_result
        ),
        "score": action_data.get(
            "FacultyScore",
            state.score
        ),
        "anomaly_reason": None
    }

    return Command(update=updates)


def end_node(state: GraphState) -> GraphState:
    logging.info(
        f"Final Evaluation: Score={state.score}, "
        f"Feedback={state.evaluation_result}"
    )
    return state


# ---------------- Routing Logic ----------------
def should_go_to_hitl(state: GraphState):
    if state.hitl_required:
        return "hitl_needed"
    else:
        return "hitl_not_needed"


# ---------------- Build Graph ----------------
graph = StateGraph(GraphState)

graph.add_node("evaluate", evaluate_node)
graph.add_node("check_anomaly", check_anomaly_node)
graph.add_node("hitl", hitl_node)
graph.add_node("end", end_node)

graph.set_entry_point("evaluate")

graph.add_edge("evaluate", "check_anomaly")

graph.add_conditional_edges(
    "check_anomaly",
    should_go_to_hitl,
    path_map={
        "hitl_needed": "hitl",
        "hitl_not_needed": "end"
    }
)

graph.add_edge("hitl", "end")
graph.add_edge("end", END)

agent = graph.compile()
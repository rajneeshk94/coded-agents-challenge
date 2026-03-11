from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Final, Literal, TypedDict
from uuid import uuid4

import langchain
import langgraph
import uipath_langchain
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field
from uipath.platform import UiPath
from uipath.platform.action_center.tasks import TaskRecipient, TaskRecipientType
from uipath.platform.common import WaitEscalation
from uipath_langchain.chat import UiPathChat

AGENT_NAME: Final[str] = "AI_AGENT_RISK_MONITOR"
RISK_LEVEL = Literal["LOW", "MEDIUM", "HIGH"]
LOCAL_HITL_PREFIX: Final[str] = "LOCAL-HITL"
LOCAL_HITL_NOTE: Final[str] = (
    "UiPath HITL is not configured in the current environment; "
    "returned a local approval placeholder instead."
)
LOCAL_HITL_FAILURE_NOTE: Final[str] = (
    "UiPath HITL task creation failed in the current environment; "
    "returned a local approval placeholder instead."
)
_SDK_PACKAGES: Final[tuple[str, str, str]] = (
    langchain.__name__,
    langgraph.__name__,
    uipath_langchain.__name__,
)


class Input(BaseModel):
    action: str = Field(
        ...,
        min_length=1,
        description="The AI agent action to evaluate for operational risk.",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Business and technical context describing what the action will do.",
    )


class AgentState(TypedDict):
    action: str
    description: str
    risk_level: str
    analysis: str
    decision: str
    task_id: str


class Output(BaseModel):
    action: str = Field(..., description="The evaluated action name.")
    risk_level: RISK_LEVEL = Field(..., description="LOW, MEDIUM, or HIGH.")
    analysis: str = Field(..., description="Structured explanation of the detected risk.")
    decision: str = Field(
        ...,
        description="Safe to Execute, Manual Review Recommended, Human Approval Requested, Human Approved, or Human Rejected.",
    )
    task_id: str = Field(
        default="",
        description="UiPath HITL task id for high-risk approval workflows.",
    )


class RiskAssessment(BaseModel):
    risk_level: RISK_LEVEL = Field(..., description="LOW, MEDIUM, or HIGH.")
    analysis: str = Field(..., min_length=8, description="Why the action is risky.")


class HITLSettings(BaseModel):
    app_name: str = ""
    app_folder_path: str = ""
    recipient_email: str = ""
    priority: str = "High"

    @property
    def enabled(self) -> bool:
        return bool(self.app_name)


@lru_cache(maxsize=1)
def get_llm() -> UiPathChat:
    return UiPathChat(model="gpt-4.1-mini-2025-04-14", temperature=0.0)


def get_hitl_settings() -> HITLSettings:
    return HITLSettings(
        app_name=os.getenv("UIPATH_HITL_APP_NAME", "").strip(),
        app_folder_path=os.getenv("UIPATH_HITL_APP_FOLDER_PATH", "").strip(),
        recipient_email=os.getenv("UIPATH_HITL_RECIPIENT_EMAIL", "").strip(),
        priority=os.getenv("UIPATH_HITL_PRIORITY", "High").strip() or "High",
    )


def build_task_recipient(settings: HITLSettings) -> TaskRecipient | None:
    if not settings.recipient_email:
        return None

    return TaskRecipient(
        type=TaskRecipientType.EMAIL,
        value=settings.recipient_email,
        displayName=settings.recipient_email,
    )


def build_output(
    state: AgentState,
    *,
    decision: str | None = None,
    analysis: str | None = None,
) -> Output:
    return Output(
        action=state["action"],
        risk_level=state["risk_level"],
        analysis=analysis if analysis is not None else state["analysis"],
        decision=decision if decision is not None else state["decision"],
        task_id=state.get("task_id", ""),
    )


def append_note(analysis: str, note: str) -> str:
    if not note or note in analysis:
        return analysis
    return f"{analysis} {note}"


def local_task_id() -> str:
    return f"{LOCAL_HITL_PREFIX}-{uuid4().hex[:8].upper()}"


def to_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="python")
    return {}


def extract_resume_payload(value: Any) -> dict[str, Any]:
    payload = to_mapping(value)
    nested = payload.get("value")
    if isinstance(nested, dict):
        return nested
    return payload


def resolve_human_decision(value: Any) -> str:
    payload = extract_resume_payload(value)
    raw_decision = str(
        payload.get("decision") or payload.get("action") or payload.get("outcome") or ""
    ).strip().lower()
    approved = payload.get("approved")

    if approved is True or raw_decision in {"approve", "approved", "yes"}:
        return "Human Approved"
    if approved is False or raw_decision in {"reject", "rejected", "no"}:
        return "Human Rejected"
    return "Human Approval Requested"


def resolve_human_note(value: Any) -> str:
    payload = extract_resume_payload(value)
    reviewer = str(
        payload.get("reviewed_by")
        or payload.get("reviewedBy")
        or payload.get("completed_by")
        or payload.get("completedBy")
        or ""
    ).strip()
    reason = str(
        payload.get("reason") or payload.get("comment") or payload.get("comments") or ""
    ).strip()

    note_parts = []
    if reviewer:
        note_parts.append(f"Reviewed by {reviewer}.")
    if reason:
        note_parts.append(f"Reason: {reason}.")
    return " ".join(note_parts)


def heuristic_risk_assessment(action: str, description: str) -> RiskAssessment:
    text = f"{action} {description}".lower()

    high_patterns = {
        "transfer money": "Financial transfer to an external or uncontrolled destination detected.",
        "wire transfer": "Direct movement of funds detected.",
        "bank account": "Banking destination detected in the action context.",
        "external account": "Funds or data are moving to an external account.",
        "modify system settings": "Privileged system configuration change detected.",
        "system settings": "Privileged system configuration change detected.",
        "delete file": "Destructive file operation detected.",
        "delete files": "Destructive file operation detected.",
        "drop database": "Destructive database operation detected.",
        "disable security": "Security controls may be weakened by this action.",
        "reset password": "Credential-impacting action detected.",
    }
    for pattern, analysis in high_patterns.items():
        if pattern in text:
            return RiskAssessment(risk_level="HIGH", analysis=analysis)

    medium_patterns = {
        "access database": "Database access may expose sensitive or regulated information.",
        "query database": "Database access may expose sensitive or regulated information.",
        "send email": "Outbound communication can leak information or trigger unintended actions.",
        "external recipient": "External communication target increases data exposure risk.",
        "modify config": "Configuration change should be reviewed before execution.",
        "upload file": "File transfer can expose sensitive information.",
        "download file": "Data movement should be reviewed before execution.",
        "share document": "Document sharing may expose sensitive information.",
        "create user": "User lifecycle changes should be reviewed before execution.",
    }
    for pattern, analysis in medium_patterns.items():
        if pattern in text:
            return RiskAssessment(risk_level="MEDIUM", analysis=analysis)

    if "create meeting" in text:
        return RiskAssessment(
            risk_level="LOW",
            analysis="Calendar scheduling is a routine coordination task with limited blast radius.",
        )

    return RiskAssessment(
        risk_level="LOW",
        analysis="No destructive, privileged, financial, or sensitive-data indicators were detected.",
    )


def decision_for_risk_level(risk_level: RISK_LEVEL) -> str:
    return {
        "HIGH": "Human Approval Requested",
        "MEDIUM": "Manual Review Recommended",
        "LOW": "Safe to Execute",
    }[risk_level]


async def action_analyzer(state: AgentState) -> dict[str, str]:
    system_prompt = (
        f"You are {AGENT_NAME}, a risk-monitoring agent for enterprise AI automation. "
        "Classify the requested action as LOW, MEDIUM, or HIGH risk. "
        "Return HIGH for destructive, privileged, financial, credential, or external-data actions. "
        "Return MEDIUM for actions needing oversight but not immediate human approval. "
        "Return LOW only for routine, reversible, low-impact actions. "
        "Provide one concise analysis sentence."
    )
    human_prompt = (
        f"Action: {state['action']}\n"
        f"Description: {state['description']}\n"
        "Respond with structured output only."
    )

    try:
        structured_llm = get_llm().with_structured_output(
            RiskAssessment,
            method="function_calling",
        )
        result = await structured_llm.ainvoke(
            [SystemMessage(system_prompt), HumanMessage(human_prompt)]
        )
        assessment = (
            result
            if isinstance(result, RiskAssessment)
            else RiskAssessment.model_validate(result)
        )
    except Exception:
        assessment = heuristic_risk_assessment(state["action"], state["description"])

    return {
        "analysis": assessment.analysis,
        "risk_level": assessment.risk_level,
        "decision": "",
        "task_id": "",
    }


async def decision_router(state: AgentState) -> dict[str, str]:
    return {"decision": decision_for_risk_level(state["risk_level"])}


def route_by_risk_level(state: AgentState) -> str:
    return state["risk_level"]


async def execute_node(state: AgentState) -> Output:
    return build_output(state)


async def review_node(state: AgentState) -> Output:
    return build_output(state)


async def human_approval_node(state: AgentState) -> dict[str, str]:
    settings = get_hitl_settings()
    if not settings.enabled:
        return {
            "decision": "Human Approval Requested",
            "task_id": local_task_id(),
            "analysis": append_note(state["analysis"], LOCAL_HITL_NOTE),
        }

    task_data = {
        "Action": state["action"],
        "Description": state["description"],
        "RiskLevel": state["risk_level"],
        "Analysis": state["analysis"],
    }

    try:
        client = UiPath()
        task = await client.tasks.create_async(
            title="AI Action Approval Required",
            data=task_data,
            app_name=settings.app_name,
            app_folder_path=settings.app_folder_path or None,
            recipient=build_task_recipient(settings),
            priority=settings.priority,
            labels=[
                "ai-agent-risk-monitor",
                f"risk:{state['risk_level'].lower()}",
            ],
            source_name=AGENT_NAME,
        )
        return {
            "decision": "Human Approval Requested",
            "task_id": str(task.id),
        }
    except Exception:
        return {
            "decision": "Human Approval Requested",
            "task_id": local_task_id(),
            "analysis": append_note(state["analysis"], LOCAL_HITL_FAILURE_NOTE),
        }


async def wait_for_approval_node(state: AgentState) -> Output:
    task_id = state.get("task_id", "")
    if not task_id or task_id.startswith(LOCAL_HITL_PREFIX):
        return build_output(state)

    settings = get_hitl_settings()
    try:
        client = UiPath()
        task = await client.tasks.retrieve_async(
            action_key=task_id,
            app_folder_path=settings.app_folder_path,
            app_name=settings.app_name,
        )
        approval_result = interrupt(
            WaitEscalation(
                action=task,
                app_name=settings.app_name,
                app_folder_path=settings.app_folder_path or None,
                recipient=build_task_recipient(settings),
            )
        )
    except Exception:
        fallback_analysis = append_note(
            state["analysis"],
            "UiPath HITL wait step could not connect; returning the created task reference without pausing.",
        )
        return build_output(
            state,
            decision="Human Approval Requested",
            analysis=fallback_analysis,
        )

    return build_output(
        state,
        decision=resolve_human_decision(approval_result),
        analysis=append_note(state["analysis"], resolve_human_note(approval_result)),
    )


builder = StateGraph(AgentState, input=Input, output=Output)

builder.add_node("action_analyzer", action_analyzer)
builder.add_node("decision_router", decision_router)
builder.add_node("execute_node", execute_node)
builder.add_node("review_node", review_node)
builder.add_node("human_approval_node", human_approval_node)
builder.add_node("wait_for_approval_node", wait_for_approval_node)

builder.add_edge(START, "action_analyzer")
builder.add_edge("action_analyzer", "decision_router")
builder.add_conditional_edges(
    "decision_router",
    route_by_risk_level,
    {
        "LOW": "execute_node",
        "MEDIUM": "review_node",
        "HIGH": "human_approval_node",
    },
)
# Create the HITL task in one node and wait in the next node so task creation is not repeated on resume.
builder.add_edge("human_approval_node", "wait_for_approval_node")
builder.add_edge("execute_node", END)
builder.add_edge("review_node", END)
builder.add_edge("wait_for_approval_node", END)

graph = builder.compile()

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from uipath.platform.common import CreateTask
from uipath_langchain.chat.models import UiPathAzureChatOpenAI
from langchain_core.messages import HumanMessage

import json
import re
import random


# ===============================
# LLM SETUP
# ===============================

llm = UiPathAzureChatOpenAI(
    model="gpt-4o-2024-08-06",
    temperature=0,
    max_tokens=2000,
    timeout=30,
    max_retries=2
)


# ===============================
# GRAPH STATE
# ===============================

class GraphState(BaseModel):

    emails: list = Field(..., title="Email Inbox")

    tasks: list = Field(default_factory=list)

    intents: list = Field(default_factory=list)

    priorities: list = Field(default_factory=list)

    actions: list = Field(default_factory=list)

    execution_results: list = Field(default_factory=list)

    failed_actions: list = Field(default_factory=list)

    retry_count: int = Field(default=0)

    summary: str = Field(default="")


# ===============================
# NODE 1 — FETCH INPUTS
# ===============================

def fetch_inputs(state: GraphState):

    print("\nEmails received:")

    for e in state.emails:
        print("-", e["subject"])

    return state


# ===============================
# NODE 2 — TASK EXTRACTION
# ===============================

def extract_tasks(state: GraphState):

    prompt = f"""
Extract actionable tasks from the following emails.

Return JSON list format:

[
{{"subject":"...", "task":"..."}}
]

Emails:
{state.emails}
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    match = re.search(r"\[.*\]", response.content, re.S)

    state.tasks = json.loads(match.group(0)) if match else []

    print("\nTasks extracted:", state.tasks)

    return state


# ===============================
# NODE 3 — INTENT CLASSIFICATION
# ===============================

def classify_intent(state: GraphState):

    prompt = f"""
Classify the intent of these tasks.

Possible intents:
meeting_request
exam_update
internship_opportunity
promotion
general

Return JSON:

[
{{"subject":"...", "intent":"..."}}
]

Tasks:
{state.tasks}
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    match = re.search(r"\[.*\]", response.content, re.S)

    state.intents = json.loads(match.group(0)) if match else []

    print("\nDetected intents:", state.intents)

    return state


# ===============================
# NODE 4 — PRIORITY EVALUATION
# ===============================

def evaluate_priority(state: GraphState):

    priorities = []

    for item in state.intents:

        intent = item["intent"]

        if intent in ["exam_update", "meeting_request"]:
            level = "high"

        elif intent == "internship_opportunity":
            level = "medium"

        else:
            level = "low"

        priorities.append({
            "subject": item["subject"],
            "intent": intent,
            "priority": level
        })

    state.priorities = priorities

    print("\nPriority evaluation:", priorities)

    return state


# ===============================
# NODE 5 — TOOL SELECTION
# ===============================

def tool_selector(state: GraphState):

    actions = []

    for item in state.priorities:

        intent = item["intent"]

        if intent == "meeting_request":
            tool = "CreateCalendarEvent"

        elif intent == "exam_update":
            tool = "AddExamReminder"

        elif intent == "internship_opportunity":
            tool = "CreateApplicationReminder"

        elif intent == "promotion":
            tool = "ArchiveEmail"

        else:
            tool = "NoAction"

        actions.append({
            "subject": item["subject"],
            "tool": tool
        })

    state.actions = actions

    print("\nTools selected:", actions)

    return state


# ===============================
# NODE 6 — EXECUTE AUTOMATION
# ===============================

def execute_automation(state: GraphState):

    results = []

    for action in state.actions:

        tool = action["tool"]

        if tool == "NoAction":
            continue

        print(f"\nExecuting {tool} for {action['subject']}")

        # simulate automation success/failure
        status = "success" if random.random() > 0.3 else "failed"

        results.append({
            "tool": tool,
            "subject": action["subject"],
            "status": status
        })

    state.execution_results = results

    return state


# ===============================
# NODE 7 — VERIFY EXECUTION
# ===============================

def verify_execution(state: GraphState):

    failures = [r for r in state.execution_results if r["status"] != "success"]

    state.failed_actions = failures

    print("\nVerification complete")
    print("Failures:", failures)

    return state


# ===============================
# CONDITIONAL ROUTER
# ===============================

def route_verification(state: GraphState):

    if not state.failed_actions:
        return "GenerateBrief"

    if state.retry_count < 1:
        return "RetryAutomation"

    return "HumanApproval"


# ===============================
# NODE 8 — RETRY AUTOMATION
# ===============================

def retry_automation(state: GraphState):

    print("\nRetrying failed automations")

    state.retry_count += 1

    return state


# ===============================
# NODE 9 — HUMAN APPROVAL
# ===============================

def human_approval(state: GraphState):

    interrupt(
        CreateTask(
            app_name="Automationapprovalapp",
            title="Automation Requires Manual Review",
            data={
                "FailedActions": str(state.failed_actions)
            },
            app_version=1,
            app_folder_path="Sneha"
        )
    )

    print("\nHuman review completed")

    return state


# ===============================
# NODE 10 — GENERATE MORNING BRIEF
# ===============================

def generate_brief(state: GraphState):

    prompt = f"""
Generate a concise morning briefing for the user.

Automation results:
{state.execution_results}

Explain what happened and highlight important updates.
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    state.summary = response.content

    print("\nMorning Brief:")
    print(state.summary)

    return state


# ===============================
# BUILD GRAPH
# ===============================

graph = StateGraph(GraphState)

graph.add_node("FetchInputs", fetch_inputs)
graph.add_node("ExtractTasks", extract_tasks)
graph.add_node("ClassifyIntent", classify_intent)
graph.add_node("EvaluatePriority", evaluate_priority)
graph.add_node("ToolSelector", tool_selector)
graph.add_node("ExecuteAutomation", execute_automation)
graph.add_node("VerifyExecution", verify_execution)
graph.add_node("RetryAutomation", retry_automation)
graph.add_node("HumanApproval", human_approval)
graph.add_node("GenerateBrief", generate_brief)


graph.add_edge(START, "FetchInputs")
graph.add_edge("FetchInputs", "ExtractTasks")
graph.add_edge("ExtractTasks", "ClassifyIntent")
graph.add_edge("ClassifyIntent", "EvaluatePriority")
graph.add_edge("EvaluatePriority", "ToolSelector")
graph.add_edge("ToolSelector", "ExecuteAutomation")
graph.add_edge("ExecuteAutomation", "VerifyExecution")


graph.add_conditional_edges(
    "VerifyExecution",
    route_verification,
    {
        "GenerateBrief": "GenerateBrief",
        "RetryAutomation": "RetryAutomation",
        "HumanApproval": "HumanApproval"
    }
)

graph.add_edge("RetryAutomation", "ExecuteAutomation")
graph.add_edge("HumanApproval", "GenerateBrief")
graph.add_edge("GenerateBrief", END)


# ===============================
# COMPILE AGENT
# ===============================

app = graph.compile()
# AI_AGENT_RISK_MONITOR

## Overview

AI_AGENT_RISK_MONITOR is an intelligent agent built using **UiPath Python SDK** and **LangGraph** that evaluates actions proposed by AI systems and classifies their **risk level** before allowing automation to proceed.

In modern AI-driven automation environments, agents may perform actions like sending emails, modifying files, transferring money, or accessing databases. This system acts as a **safety layer**, ensuring that potentially dangerous operations are reviewed before execution.

The agent performs **risk analysis**, routes decisions using **conditional logic**, and integrates **Human-in-the-Loop (HITL)** approval for high-risk actions.

---

# Use Case

AI systems increasingly automate tasks such as:

* Sending Emails
* Deleting Files
* Accessing Databases
* Transferring Money
* Creating Meetings
* Modifying System Settings

These actions may introduce **security risks or unintended consequences**.

The AI Agent Risk Monitor evaluates each action and assigns a **risk level** before execution.

---

# Goal of the Agent

The goal is to ensure safe automation by categorizing actions into three levels:

| Risk Level | Decision                  |
| ---------- | ------------------------- |
| LOW        | Safe to Execute           |
| MEDIUM     | Manual Review Recommended |
| HIGH       | Human Approval Required   |

This allows organizations to **prevent dangerous automation actions** before they occur.

---

# System Architecture

```mermaid
flowchart TD

User[User / AI System Input]
Analyzer[Action Analyzer Node]
Router[Decision Router]
Execute[Execute Node]
Review[Manual Review Node]
Approval[Human Approval Node]
Wait[Wait for Approval]
Output[Structured JSON Output]

User --> Analyzer
Analyzer --> Router

Router -->|LOW Risk| Execute
Router -->|MEDIUM Risk| Review
Router -->|HIGH Risk| Approval

Approval --> Wait
Wait --> Output

Execute --> Output
Review --> Output
```

---

# Agent Decision Flow

```mermaid
flowchart LR

Input[Action + Description]
RiskAnalysis[Risk Analysis using LLM]
Decision{Risk Level}

Execute[Safe Execution]
Review[Manual Review]
Approval[Human Approval Required]

Input --> RiskAnalysis
RiskAnalysis --> Decision

Decision -->|LOW| Execute
Decision -->|MEDIUM| Review
Decision -->|HIGH| Approval
```

---

# LangGraph Workflow Diagram

```mermaid
flowchart TD

Start[Start Agent]

A[action_analyzer]
B[decision_router]

C[execute_node]
D[review_node]
E[human_approval_node]

F[wait_for_approval_node]
End[End]

Start --> A
A --> B

B -->|LOW| C
B -->|MEDIUM| D
B -->|HIGH| E

E --> F
F --> End

C --> End
D --> End
```

---

# High Level AI Safety Architecture

```mermaid
flowchart TD

AI[AI Agent]
Monitor[Risk Monitor Agent]
Policy[Risk Policy Engine]
Human[Human Reviewer]
Automation[Automation System]

AI --> Monitor
Monitor --> Policy

Policy -->|LOW| Automation
Policy -->|MEDIUM| Human
Policy -->|HIGH| Human

Human --> Automation
```

---

# Agent State Flow

```mermaid
flowchart LR

Action[Action Input]
Description[Action Description]

State[Graph State]

Risk[Risk Level]
Analysis[Risk Analysis]
Decision[Decision]
Task[Approval Task ID]

Action --> State
Description --> State

State --> Risk
State --> Analysis
State --> Decision
State --> Task
```

---

# Agent Workflow

### Step 1 – Action Analyzer

Analyzes the action and description using an LLM and produces structured output including:

* risk level
* explanation

### Step 2 – Decision Router

Routes the workflow based on the identified risk level.

### Step 3 – Execute Node

Automatically executes actions classified as **LOW risk**.

### Step 4 – Review Node

Flags actions classified as **MEDIUM risk** for manual review.

### Step 5 – Human Approval Node

Actions classified as **HIGH risk** require **Human-in-the-Loop approval** before execution.

### Step 6 – Wait for Approval

If HITL is not configured, the agent generates a **local placeholder approval task** to allow safe execution during development.

---

# Graph State

The LangGraph state contains the following fields:

* `action`
* `description`
* `risk_level`
* `analysis`
* `decision`
* `task_id`

---

# Example Input
## Use Case

`AI_AGENT_RISK_MONITOR` monitors actions proposed or executed by AI systems and classifies them as `LOW`, `MEDIUM`, or `HIGH` risk before downstream automation proceeds.

Typical actions:

- Send Email
- Delete File
- Transfer Money
- Access Database
- Create Meeting
- Modify System Settings

## Goal

The agent provides a structured, production-ready risk decision for AI-initiated actions:

- `LOW` -> `Safe to Execute`
- `MEDIUM` -> `Manual Review Recommended`
- `HIGH` -> `Human Approval Requested`

## Graph State

The LangGraph state is implemented as a structured `TypedDict`:

```python
class AgentState(TypedDict):
    action: str
    description: str
    risk_level: str
    analysis: str
    decision: str
    task_id: str
```

## Agent Flow

1. `action_analyzer`
   Uses `UiPathChat` structured output when available and falls back to deterministic heuristics when credentials are missing.
2. `decision_router`
   Routes actions by `risk_level`.
3. `execute_node`
   Returns `Safe to Execute` for `LOW` risk.
4. `review_node`
   Returns `Manual Review Recommended` for `MEDIUM` risk.
5. `human_approval_node`
   Creates the UiPath Action Center task for `HIGH` risk actions.
6. `wait_for_approval_node`
   Pauses the graph with `WaitEscalation(...)` until a human approves or rejects the task.

## Human-In-The-Loop Integration

High-risk actions are escalated to UiPath HITL services using the installed UiPath SDK:

- `UiPath().tasks.create_async(...)` creates the Action Center task.
- `interrupt(WaitEscalation(...))` pauses execution until the human task is completed.
- The graph resumes and returns the reviewed outcome.

Implementation note:

- The high-risk path is intentionally split into task creation and wait/resume nodes so task creation happens exactly once across suspend and resume cycles.
- When UiPath HITL is not configured locally, the agent returns a local placeholder `task_id` so `uipath run agent ...` still works during development.

Required environment variables for real UiPath HITL:

```bash
UIPATH_HITL_APP_NAME=AI Action Approval App
UIPATH_HITL_APP_FOLDER_PATH=Shared
UIPATH_HITL_RECIPIENT_EMAIL=approver@company.com
UIPATH_HITL_PRIORITY=High
```

## Tools Used

- Python
- UiPath Python SDK
- `uipath-langchain`
- LangGraph
- LangChain
- Typed `AgentState`
- Conditional routing
- UiPath Action Center HITL

## Architecture Diagram

```mermaid
flowchart TB
    request[AI Action Request] --> analyzer[action_analyzer]
    analyzer --> router[decision_router]
    router -->|LOW| execute[execute_node]
    router -->|MEDIUM| review[review_node]
    router -->|HIGH| hitlCreate[human_approval_node<br/>create task]
    hitlCreate --> hitlWait[wait_for_approval_node<br/>interrupt and resume]
    execute --> out[Structured JSON Output]
    review --> out
    hitlWait --> out
```

## Workflow Diagram

```mermaid
flowchart TB
    START([START]) --> action_analyzer[action_analyzer]
    action_analyzer --> decision_router[decision_router]
    decision_router -->|LOW| execute_node[execute_node]
    decision_router -->|MEDIUM| review_node[review_node]
    decision_router -->|HIGH| human_approval_node[human_approval_node]
    human_approval_node --> wait_for_approval_node[wait_for_approval_node]
    execute_node --> END([END])
    review_node --> END
    wait_for_approval_node --> END
```

## Architecture Explanation

The project uses:

- `Input` for UiPath runtime input schema
- `AgentState` as the structured LangGraph state
- `Output` for the final JSON contract
- conditional routing from `decision_router`
- a dedicated HITL creation node and a resumable approval wait node

This design keeps task creation idempotent and allows production deployments to pause and resume safely when a human must review high-risk actions.

## Example Input

```json
{
  "action": "Transfer Money",
  "description": "Transfer $5000 to external bank account"
}
```

---

# Example Output

Local development output when HITL is not configured:

```json
{
  "action": "Transfer Money",
  "risk_level": "HIGH",
  "analysis": "Financial transfer to an external or uncontrolled destination detected.",
  "decision": "Human Approval Requested",
  "task_id": "LOCAL-HITL-21125220"
}
```

---
  "analysis": "Financial transfer to an external or uncontrolled destination detected. UiPath HITL is not configured in the current environment; returned a local approval placeholder instead.",
  "decision": "Human Approval Requested",
  "task_id": "LOCAL-HITL-1234ABCD"
}
```

Production runtime behavior when HITL is configured:

1. The first run creates a UiPath Action Center task and pauses.
2. After the human completes the task, resume the run.
3. The final response includes the `task_id` and the human-reviewed decision.

## How to Run

# Technologies Used

* Python
* UiPath Python SDK
* LangGraph
* LangChain
* Pydantic
* JSON structured output

---

# Project Structure

```
submissions/
   manikandan_ai_risk_monitor/
       main.py
       langgraph.json
       pyproject.toml
       uipath.json
       agent.mermaid
       README.md
       bindings.json
       entry-points.json
       input.json
       requirements.txt
       AGENTS.md
       CLAUDE.md
```

---

# Installation

Clone the repository:

```
git clone https://github.com/rajneeshk94/coded-agents-challenge.git
```

Navigate to the project folder:

```
cd submissions/manikandan_ai_risk_monitor
```

Install dependencies:

```
pip install -r requirements.txt
Run locally with inline JSON:

```bash
uipath run agent '{"action":"Transfer Money","description":"Transfer $5000"}'
```

Run locally with a JSON file:

```bash
uipath run agent --file high_input.json --output-file high_output.json
```

Resume a suspended HITL run after a human completes the task:

```bash
uipath run --resume
```

---

# Running the Agent

Run the agent using UiPath CLI:
1. Authenticate:

```
uipath run agent --file input.json
```

Example:

```
uipath run agent '{"action":"Send Email","description":"Send report to manager"}'
```

---

# Deployment

To deploy using UiPath CLI:

```
uipath auth
uipath init
uipath pack
uipath publish
```

This will package and deploy the coded agent to UiPath Cloud.

---

# Key Features

* Agentic workflow using **LangGraph**
* Conditional routing based on **risk classification**
* Structured JSON output
* Human-in-the-Loop integration
* Safe fallback when HITL is unavailable
* Modular graph architecture

---

# Future Improvements

* Real-time approval dashboard
* Integration with enterprise security policies
* Risk scoring using historical behavior
* Advanced anomaly detection for AI agents

---

# Conclusion

AI_AGENT_RISK_MONITOR demonstrates a **production-ready agentic safety layer** for AI automation systems.
5. Deploy to a UiPath tenant where Orchestrator and Action Center are enabled.

By combining **LangGraph orchestration**, **structured outputs**, and **human-in-the-loop verification**, the system ensures that automation remains **safe, transparent, and controllable**.

This project showcases how agentic workflows can be used to build **trustworthy AI-driven automation systems**.
- `main.py` - LangGraph agent with UiPath HITL integration
- `langgraph.json` - UiPath LangGraph entrypoint mapping
- `uipath.json` - UiPath runtime and packaging configuration
- `pyproject.toml` - Python package metadata and dependencies
- `agent.mermaid` - workflow diagram
- `README.md` - setup, architecture, and deployment guide

# AI_AGENT_RISK_MONITOR

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
- `HIGH` -> `Human Approval Required`

## Agent Flow

1. `action_analyzer`
   Evaluates `action` and `description` with `UiPathChat` structured output.
2. `decision_router`
   Sets the decision and routes by `risk_level`.
3. `execute_node`
   Returns a final safe decision for `LOW` risk.
4. `review_node`
   Returns a manual review decision for `MEDIUM` risk.
5. `human_approval_node`
   Returns a human approval decision for `HIGH` risk.

## Tools Used

- Python
- UiPath Python SDK
- `uipath-langchain`
- LangGraph
- LangChain
- Pydantic structured models

## Architecture Explanation

The project uses a typed LangGraph state machine with:

- `Input` for UiPath runtime input schema
- `AgentState` as the structured graph state
- `Output` for final structured JSON output
- Conditional routing from `decision_router` to three terminal nodes

The `action_analyzer` node uses `UiPathChat(...).with_structured_output(...)` to request deterministic JSON-like output from the LLM. To keep local execution and `uipath init` stable even when UiPath credentials are not configured, the node falls back to deterministic keyword-based risk classification when the LLM is unavailable.

## Graph State

`AgentState` contains:

- `action`
- `description`
- `risk_level`
- `decision`
- `analysis`

## Example Input

```json
{
  "action": "Transfer Money",
  "description": "Transfer $5000 to external bank account"
}
```

## Example Output

```json
{
  "action": "Transfer Money",
  "risk_level": "HIGH",
  "analysis": "Financial transfer to an external or uncontrolled destination detected.",
  "decision": "Human Approval Required"
}
```

## How to Run

Install dependencies:

```bash
pip install uipath-langchain langgraph langchain
```

Optional project bootstrap command from the challenge instructions:

```bash
uipath new ai-agent-risk-monitor
```

Initialize the project metadata:

```bash
uipath init
```

Run locally:

```bash
uipath run agent '{"action":"Send Email","description":"Send report to manager"}'
```

## How to Deploy Using UiPath CLI

1. Authenticate if you want live UiPath LLM execution or platform deployment:

```bash
uipath auth
```

2. Initialize runtime metadata and schemas:

```bash
uipath init
```

3. Pack the project:

```bash
uipath pack
```

4. Publish the package:

```bash
uipath publish
```

5. Deploy to UiPath Cloud or Studio Web according to your target workspace configuration.

## Files

- `main.py` - typed LangGraph agent implementation
- `langgraph.json` - UiPath LangGraph entrypoint mapping
- `uipath.json` - UiPath runtime and packaging configuration
- `pyproject.toml` - Python package metadata and dependencies
- `agent.mermaid` - graph diagram
- `README.md` - setup, architecture, and deployment guide

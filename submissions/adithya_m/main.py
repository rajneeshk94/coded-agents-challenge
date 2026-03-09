import os
from internship_checker.graph import appraisal_graph
from langchain_core.messages import HumanMessage

# Try importing UiPath SDK
try:
    from uipath_sdk import Robot
except ImportError:
    print("[WARN] UiPath SDK not found – running in standalone mode")

    class Robot:
        def get_input(self, name):
            print(f"[MOCK] Getting input for: {name}")
            return "Adithya M, 3rd year CSE, GPA 8.5/10, grad 2026, Python, React, SQL"

        def set_output(self, name, value):
            print(f"[OUTPUT] {name}: {value}")


def main():
    robot = Robot()

    candidate_input = robot.get_input("candidate_input")

    if not candidate_input:
        robot.set_output("status", "Error: No input provided")
        return

    print("\n[INFO] Candidate Input:")
    print(candidate_input)

    inputs = {
        "messages": [
            HumanMessage(content=candidate_input)
        ]
    }

    config = {
        "configurable": {
            "thread_id": "session_1"
        }
    }

    final_state = appraisal_graph.invoke(inputs, config=config)

    print("\n[DEBUG] Final State:")
    print(final_state)

    if "messages" in final_state:
        print("\n[AI RESPONSE]")
        for msg in final_state["messages"]:
            print(msg.content)

    result = final_state.get("result")
    candidate = final_state.get("candidate")

    if result and candidate:
        robot.set_output("candidate_name", candidate.name)
        robot.set_output("is_eligible", result.is_eligible)
        robot.set_output("reasons", result.reasons)
        robot.set_output("suggested_role", result.suggested_role)
        robot.set_output("status", "Success")


if __name__ == "__main__":
    main()
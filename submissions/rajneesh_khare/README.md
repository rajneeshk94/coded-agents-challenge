# 📚 Assignment Evaluation Agent (LLM + HITL)

---

## 🧠 Use Case Description

This agent automates the evaluation of student assignment responses using an LLM (GPT-4o) and introduces a **Human-In-The-Loop (HITL)** escalation mechanism when uncertainty or anomalies are detected.

It is designed for academic institutions that want to:

- Automate grading of descriptive answers  
- Ensure evaluation reliability  
- Escalate ambiguous or low-confidence cases to faculty  
- Maintain auditability and structured scoring  

The system leverages **LangGraph orchestration**, **UiPath LLM integration**, and **UiPath Action Center tasks** for human validation.

---

## 🎯 Goal of the Agent

The agent aims to:

1. ✅ Evaluate a student's answer to a given question  
2. 📊 Assign a score (0–10)  
3. 💬 Provide short structured feedback  
4. 🚨 Detect anomalies or low-confidence cases  
5. 👩‍🏫 Escalate uncertain cases to faculty for validation  
6. 🧾 Return a finalized evaluation (AI or faculty-approved)  

---

## 🔄 Agent Flow Explanation

### 1️⃣ Evaluation Node (`evaluate_node`)

- Uses GPT-4o via `UiPathChat`
- Sends structured prompt to evaluate:
  - Score (0–10)
  - Short feedback
  - Optional anomaly reason
- Returns JSON-only response

---

### 2️⃣ Anomaly Check Node (`check_anomaly_node`)

- Checks if `anomaly_reason` is not `None`
- If anomaly exists → HITL required  
- Otherwise → Continue to end  

---

### 3️⃣ HITL Escalation Node (`hitl_node`)

If anomaly detected:

- Creates a task in **UiPath Action Center**
- Sends:
  - Question  
  - Student answer  
  - AI score  
  - AI feedback  
  - Anomaly reason  
- Faculty reviews and submits:
  - `FacultyScore`
  - `FacultyEvaluation`
- Agent updates final state with faculty decision  

---

### 4️⃣ End Node (`end_node`)

- Logs final result  
- Returns final evaluation (AI or faculty-validated)  

---

### 🔀 Routing Logic

```text
Evaluate → Check Anomaly
              ↓
        HITL Required?
          /         \
        Yes         No
        ↓            ↓
      HITL         End
        ↓
       End
```
---

### 🛠️ Tools Used

| Tool                      | Purpose                            |
| ------------------------- | ---------------------------------- |
| **LangGraph**             | State orchestration                |
| **Pydantic**              | Typed state management             |
| **UiPathChat (GPT-4o)**   | Academic evaluation                |
| **UiPath CreateTask**     | Faculty review task creation       |
| **interrupt() + Command** | Human-in-the-loop workflow control |
| **Logging**               | Trace final evaluation             |

---

### 🧪 Example Input
```json
{
  "question": "Explain the theory of relativity.",
  "student_answer": "It is about how gravity works."
}
```

---

### 📤 Example Output (No Anomaly)
```json
{
  "score": 6,
  "evaluation_result": "The answer mentions gravity but lacks depth and key concepts like spacetime or relativity of motion.",
  "anomaly_reason": null
}
```

---

### 📤 Example Output (With HITL Escalation)

## AI Initial Evaluation
```json
{
  "score": 2,
  "evaluation_result": "Answer is too short and unclear.",
  "anomaly_reason": "Answer is too short to evaluate"
}
```

## Faculty Final Review
```json
{
  "score": 5,
  "evaluation_result": "Student shows partial understanding but lacks explanation."
}
```

The final state returned by the agent reflects the faculty override.
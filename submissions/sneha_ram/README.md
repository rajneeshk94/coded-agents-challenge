# 🤖 Automation Control Tower Agent
### Email Intelligence + Autonomous Automation using LangGraph and UiPath

# 🧠 Use Case Description

Students receive numerous emails every day related to:

- Exam schedules
- Internship opportunities
- Project meetings
- Placement announcements
- College events and promotions

Important information is often buried within long email threads, making it difficult for students to track actionable tasks and deadlines.

This agent introduces an **Automation Control Tower for Email Intelligence**, which autonomously:

- 📧 Reads incoming emails
- 🧠 Extracts actionable tasks
- 🏷️ Classifies intent of communication
- 📊 Prioritizes important updates
- ⚙️ Selects appropriate automation tools
- 🤖 Executes automation workflows
- 🔍 Detects automation failures
- 🔁 Retries failed tasks
- 👩‍💻 Escalates unresolved issues to humans
- 🧾 Generates a **Morning Briefing** summarizing key updates

The system demonstrates how **agentic AI combined with UiPath automation** can act as an intelligent orchestration layer for personal productivity.

---

# 🎯 Goal of the Agent

The agent aims to:

- 📧 Process incoming student emails
- 🧠 Extract actionable tasks using an LLM
- 🏷️ Classify email intent
- 📊 Prioritize important updates
- ⚙️ Select automation tools dynamically
- 🤖 Execute automation workflows
- 🔍 Verify automation results
- 🔁 Retry failed automations automatically
- 👩‍💻 Escalate unresolved cases via Human-In-The-Loop
- 🧾 Generate a structured **Morning Briefing**

---

# 🔄 Agent Flow Explanation

## 1️⃣ Input Processing Node — FetchInputs

The agent receives structured email inputs containing:

- **Subject**
- **Body**

### Example Input

```json
{
  "subject": "Google STEP Internship Applications Open",
  "body": "Applications close in 3 days."
}
```
The emails are stored in the agent's **GraphState** for further analysis.

---

## 2️⃣ Task Extraction Node (ExtractTasks)

Using **GPT-4o via UiPath LLM integration**, the agent extracts actionable tasks from email content.

### Example Transformation

**Email:**

Google STEP Internship Applications Open

**Extracted Task:**

Submit internship application before deadline

The extracted tasks are saved in the **agent state**.

---

## 3️⃣ Intent Classification Node (ClassifyIntent)

The agent classifies the **intent of each email**.

### Possible Intents

- `exam_update`
- `meeting_request`
- `internship_opportunity`
- `promotion`
- `general`

### Example Output

```json
{
  "subject": "Project Meeting Tomorrow",
  "intent": "meeting_request"
}
```

---

## 4️⃣ Priority Evaluation Node (EvaluatePriority)

The agent determines the **priority of tasks** based on intent.

### Priority Logic

| Intent | Priority |
|-------|----------|
| exam_update | High |
| meeting_request | High |
| internship_opportunity | Medium |
| promotion | Low |

This ensures **critical academic updates are processed first**.

---

## 5️⃣ Tool Selection Node (ToolSelector)

Based on the **intent**, the agent selects the appropriate automation tool.

### Example Mappings

| Intent | Automation Tool |
|------|------|
| meeting_request | CreateCalendarEvent |
| exam_update | AddExamReminder |
| internship_opportunity | CreateApplicationReminder |
| promotion | ArchiveEmail |

This demonstrates **autonomous tool selection**, a key characteristic of **agentic systems**.

---

## 6️⃣ Automation Execution Node (ExecuteAutomation)

The selected automations are executed.

### Example Actions

- Creating calendar events for meetings  
- Setting reminders for exam schedules  
- Creating reminders for internship applications  
- Archiving promotional emails  

Execution results are stored in the **agent state**.

---

## 7️⃣ Verification Node (VerifyExecution)

The agent verifies whether the **automation execution succeeded**.

### Example Failure Detection

```json
{
  "tool": "CreateApplicationReminder",
  "subject": "Google STEP Internship Applications Open",
  "status": "failed"
}
```

If failures exist, the agent determines the **next step**.
---

## 8️⃣ Retry Mechanism Node (RetryAutomation)

If an automation fails, the agent automatically retries the task.

### Example

Retrying automation execution...

- If retry succeeds → continue workflow  
- If retry fails → escalate to human review  

---

## 9️⃣ Human-In-The-Loop Escalation (HumanApproval)

If automation continues to fail after retry, the system escalates to **UiPath Action Center**.

The agent creates a task using:

```
CreateTask()
```

The human reviewer receives:

- Failed automation details  
- Email subject  
- Task attempted  

This allows **human intervention for complex scenarios**.

---

## 🔟 Morning Brief Generation (GenerateBrief)

The agent generates a **Morning Briefing** summarizing:

- Successful automations  
- Failed tasks  
- Important updates  
- Upcoming events  

### Example Output

```
Morning Briefing

Project Meeting Tomorrow
Successfully added to your calendar.

Google STEP Internship Applications
Reminder creation failed. Consider setting a manual reminder.

Mid Semester Exams
Schedule released. Verify exam dates.
```

---

## 🔀 Routing Logic

```
FetchInputs → ExtractTasks → ClassifyIntent → EvaluatePriority → ToolSelector → ExecuteAutomation
                                                                 ↓
                                                          VerifyExecution
                                                                 ↓
                              Success → GenerateBrief
                              Retry → RetryAutomation → ExecuteAutomation
                              Escalate → HumanApproval → GenerateBrief
```

---

## 🛠️ Tools Used

| Tool | Purpose |
|------|---------|
| LangGraph | Agent workflow orchestration |
| Pydantic | Structured GraphState management |
| UiPath Azure GPT-4o | LLM reasoning and task extraction |
| UiPath Python SDK | Agent deployment |
| UiPath Action Center | Human-in-the-loop task review |
| LangChain | LLM integration |

---

## 🧪 Example Input

```json
{
  "emails": [
    {
      "subject": "Mid Semester Exam Schedule Released",
      "body": "Mid semester exams will begin Monday."
    },
    {
      "subject": "Google STEP Internship Applications Open",
      "body": "Applications close in 3 days."
    },
    {
      "subject": "Project Meeting Tomorrow",
      "body": "Meeting tomorrow at 4 PM."
    }
  ]
}
```

---

## 📤 Example Output

```json
{
  "retry_count": 1,
  "summary": "Morning briefing generated summarizing important updates and automation results."
}
```

---

## 🚀 Agentic Capabilities Demonstrated

This system demonstrates multiple **agentic behaviors** required by the challenge:

✔ LangGraph workflow orchestration  
✔ Structured GraphState  
✔ Conditional routing  
✔ Tool selection logic  
✔ Retry mechanism  
✔ Self-evaluation  
✔ Human-in-the-loop integration  
✔ Multi-step reasoning  

---

## 📊 Real World Impact

This system acts as a **personal automation control tower** capable of:

- Email intelligence  
- Task extraction  
- Automation orchestration  
- Deadline tracking  
- Opportunity management  

Such agents can significantly improve productivity by transforming **communication into automated actions**.

---

## 📌 Conclusion

The **Automation Control Tower Agent** demonstrates how **agentic AI combined with UiPath automation** can intelligently orchestrate real-world workflows.

By integrating **LLM reasoning, automation execution, failure recovery, and human escalation**, the system showcases a practical example of **next-generation autonomous automation agents**.
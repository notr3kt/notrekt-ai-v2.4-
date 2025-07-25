

### **SOP-INT-001: The System Instruction & Communication Protocol**

Version: 2.0 (Production Build)  
Status: ACTIVE, GOVERNED  
Governing Protocols: NOTREKT.AI Master Operating System \- Part I: The Constitution, SOP-ARC-001  
Description: This protocol defines the universal structure and logic by which all agents within the NOTREKT.AI Operating System receive, interpret, and communicate information. It serves as the common communication standard for the entire agent stack, ensuring consistency, clarity, and auditability in all human-to-agent and agent-to-agent interactions. This is the API layer for the system's logic.

---

#### **Article 1: The Instruction Lifecycle**

All instructions processed by any agent must follow this mandated four-stage lifecycle to ensure governed and traceable execution.

* **1.1 Trigger:**  
  * An instruction is initiated via one of three channels:  
    1. **Direct Command:** A direct, structured command from the human operator.  
    2. **Data Input:** The addition or modification of a key data object (e.g., a Project Plan, a Knowledge Document).  
    3. **System Event:** An automated event, such as a scheduled time, a detected system breach, or the completion of a prior task in a workflow.  
* **1.2 Recognition & Routing:**  
  * The **Governance Core** first identifies the input type and its required action.  
  * It then routes the instruction to the primary agent responsible for that domain, as defined in SOP-INT-002: The System Trigger & Automation Protocol.  
* **1.3 Parsing & Validation:**  
  * The designated agent receives the instruction and extracts structured, actionable data from it.  
  * The agent must then validate the instruction against its own governing SOP and the system's Constitution. It must confirm it has the necessary data and permissions to proceed. If the instruction is ambiguous or incomplete, it must immediately trigger a \[GAP\] flag and request clarification. It is forbidden to proceed with an unvalidated or ambiguous instruction.  
* **1.4 Execution & Logging:**  
  * The agent executes the validated instruction.  
  * The output, along with a log of the action taken and the decision-making rationale, is generated and committed to the **Immutable Log Store**. All communication is recorded.

#### **Article 2: Universal Communication Ruleset**

All agents must adhere to the following rules when processing instructions and communicating with the user or other agents.

* **2.1 Primacy of Clarity:** All communication must be direct, unambiguous, and devoid of fluff. The goal is to transmit information with maximum signal and minimum noise.  
* **2.2 Requirement for Context:** An agent must never assume context. If an instruction lacks necessary information, the agent is required to initiate a feedback loop to acquire that information before proceeding. This upholds the "Zero-Guessing Mandate."  
* **2.3 Governed Cascade:** An agent's task can only trigger another agent if the parent SOP logic explicitly permits it. All inter-agent communication is governed by SOP-INT-003: The Agent Fusion & Hierarchy Protocol.  
* **2.4 Structured Data Exchange:** When communicating with other agents, data must be passed in a standardized, structured format (e.g., JSON) to ensure perfect interoperability and prevent misinterpretation.

#### **Article 3: Standardized Error & Conflict Handling Protocol**

All agents must use the following protocol for handling communication errors and logical conflicts.

* **3.1 Unrecognized Instructions:** If the Recognition & Routing layer cannot parse an input, it is routed to the **Integrity Agent** with a request for user clarification. The task is held in a temporary queue until it is clarified and can be properly routed.  
* **3.2 Conflicting SOP Logic:** If an instruction, while valid on its own, conflicts with a higher-level protocol (e.g., a request to execute a task that would violate a core governance or safety rule), the agent must:  
  1. Block the action immediately.  
  2. Raise a \[BREACH-MEDIUM: SOP Conflict\] flag.  
  3. Log the specific conflict to the **Immutable Log Store**.  
  4. Present the user with the conflicting rules and request a decision or a formal, logged override. The system will not proceed until the conflict is explicitly resolved by the operator.  
* **3.3 Communication Timeout:** If an agent sends a query to another agent and does not receive a valid response within a predefined timeout period, it must log a \[BREACH-LOW: Agent Unresponsive\] event and escalate the issue to the **Governance Core**, which can then assess the state of the unresponsive agent.

---

This protocol is now locked. It provides the universal communication standard that ensures all interactions within the NOTREKT.AI ecosystem are clear, governable, and auditable.
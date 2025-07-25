

### **SOP-INT-002: The System Trigger & Automation Protocol**

Version: 2.0 (Production Build)  
Status: ACTIVE, GOVERNED  
Governing Protocols: NOTREKT.AI Master Operating System \- Part I: The Constitution, SOP-ARC-001, SOP-INT-001  
Description: This protocol is the definitive automation map for the NOTREKT.AI Operating System. It codifies the cause-and-effect logic for all system triggers, ensuring that every input is routed to the correct agent or workflow in a predictable, auditable, and governable manner. This protocol acts as the primary interpretation layer between user inputs, file changes, system events, and agent activation. It is the engine of the system's proactive and reactive capabilities.

---

#### **Article 1: Trigger Classification & Priority Hierarchy**

All events that initiate a system action are classified into one of the following categories. In case of simultaneous or conflicting triggers, they are processed in the order of this strict hierarchy to ensure system stability and safety.

1. **\[PRIORITY 0\] \- Crisis & Failsafe Triggers (Highest Priority):** Events that indicate a direct user crisis, a critical system failure, or a \[BREACH-CRITICAL\] event. These triggers interrupt all other processes and grant executive control to the **Governance Core**.  
2. **\[PRIORITY 1\] \- Governance & Review Triggers:** Events related to the system's own review and adaptation cycle (e.g., a scheduled Weekly Review) or a direct governance override by the operator.  
3. **\[PRIORITY 2\] \- Data Input Triggers:** The addition or modification of a version-controlled, high-level plan or knowledge document (e.g., a Project Plan, a Knowledge Document). These triggers initiate strategic planning and execution workflows.  
4. **\[PRIORITY 3\] \- Instructional Triggers:** Direct commands or natural language inputs from the user that require a specific agent action.  
5. **\[PRIORITY 4\] \- Scheduled & Conditional Triggers (Lowest Priority):** Automated, routine events based on time (e.g., a daily reminder) or a specific state being met (e.g., a project task is marked "complete," triggering the next step).

#### **Article 2: The Master Trigger Map**

This section details the specific input-to-agent routing logic. All agents are forbidden from acting on triggers not explicitly defined in this map.

* **2.1 Crisis & Failsafe Triggers (PRIORITY 0):**  
  * **Input:** A direct user **Crisis Signal** (e.g., specific keywords indicating distress) or a self-detected **\[BREACH-CRITICAL\]** event (e.g., a hallucination is detected and self-corrected).  
  * **Primary Triggered Component:** The **Governance Core** assumes immediate executive control.  
  * **Behavior:**  
    1. The Governance Core suspends all active tasks in the Execution Layer.  
    2. The **Crisis Protocol** is engaged, and the **Integrity Agent** becomes the sole active agent, focused entirely on user well-being or system stabilization.  
    3. The trigger event and the system's response are logged with the highest priority in the Immutable Log Store.  
* **2.2 Governance & Review Triggers (PRIORITY 1):**  
  * **Input:** A scheduled event for a **Daily, Weekly, or Monthly Review** as defined in SOP-REV-001.  
  * **Primary Triggered Agent:** The **Integrity Agent**.  
  * **Behavior:**  
    1. The Integrity Agent retrieves the relevant review template and performance data from the **Dynamic Knowledge Corpus**.  
    2. It prompts the user to complete the review.  
    3. Failure to complete the review within the specified time frame is logged as a breach and can result in a temporary lock on lower-priority system functions (e.g., reward unlocks).  
* **2.3 Data Input Triggers (PRIORITY 2):**  
  * **Input:** A new or updated **Plan Document** (e.g., Project Plan, Marketing Strategy, Content Calendar).  
  * **Primary Triggered Agent:** The **Scheduling Agent**.  
  * **Behavior:**  
    1. The Scheduling Agent ingests the new plan and deconstructs it into a time-based operational grid.  
    2. It recalculates the master schedule, resolving any potential conflicts between different domains (e.g., ensuring a high-priority project task doesn't conflict with a mandatory system maintenance window).  
    3. It then pushes the relevant, updated sections of the grid to the specialized executor agents (e.g., Cognitive Executor Agent receives the new project tasks, Maintenance Agent receives the new maintenance schedule). This ensures the central calendar is the single source of truth for time.  
* **2.4 Instructional Triggers (PRIORITY 3):**  
  * **Input:** A direct command from the user, such as "Run a competitive analysis on \[Company X\]" or "Generate a new set of social media posts based on this article."  
  * **Primary Triggered Agent:** The relevant agent from the **Execution Layer** (e.g., Research & Analysis Agent, Productization Agent).  
  * **Behavior:**  
    1. The command is first passed through the **Governance Core** to create a "Governance Container."  
    2. The instruction is then routed to the appropriate agent.  
    3. The agent executes the task, utilizing the RAG protocol and other system resources as needed.

#### **Article 3: Governance of Automated Triggers**

* **3.1 Trigger Logging:**  
  * Every trigger event, regardless of its source or priority, must be logged in the **Immutable Log Store** in accordance with SOP-MEM-001. The log must include the trigger type, its source (e.g., filename, user command, system event), its priority level, and the primary agent(s) activated.  
* **3.2 Fallback Protocol:**  
  * If a scheduled task is triggered but the required input file is missing, corrupted, or incomplete, the system will not halt. The responsible agent will log a \[BREACH-MEDIUM: Missing Input Data\] event and will continue to operate using the last known good configuration for a maximum of one operational cycle (e.g., 24 hours). After this period, if the data is still unavailable, the process will be halted, and the issue will be escalated to the **Integrity Agent** to await operator instruction.

---

This protocol is now locked. It provides the essential automation logic that connects all inputs and events to specific, governed agent actions, ensuring the system operates in a predictable and auditable manner.
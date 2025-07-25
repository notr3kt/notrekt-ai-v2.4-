

### **SOP-REV-002: The Adaptive System Review & Reflection Protocol**

Version: 2.0  
Status: Active  
Replaces: \_SOP-REV-001\_ The System Review & Reflection Protocol.md

---

#### **1.0 Guiding Principles**

* **Principle of Anti-Fragile Resilience:** This protocol is an adaptive framework for learning from operational data. Missed reviews or performance dips are treated as data points for system improvement, not as failures to be punished.  
* **Principle of Graceful Degradation:** The system is designed to bend, not break. When a review is missed, it enters **"Grace Mode,"** offering assistance to catch up rather than imposing a hard lock that leads to system collapse.  
* **Principle of AI-Assisted Cognition:** The protocol offloads the cognitive burden of review from the operator to the system. The AI is responsible for generating initial drafts and identifying patterns, turning the operator into an editor and strategist.  
* **Principle of Proactive Governance:** The system's Integrity Agent will proactively monitor for patterns of missed reviews and recommend adjustments to the protocol itself, ensuring it adapts to the operator's real-world capacity.

#### **2.0 Core Components & Trigger Mechanism**

* **The Review Hub:** A centralized Notion database for all review cycles (Daily, Weekly, Monthly).  
* **The Integrity Agent:** An AI agent responsible for monitoring protocol adherence, generating review drafts, and managing "Grace Mode".  
* **Automation Hooks:** Pre-defined triggers for Zapier/Make.com to connect the Review Hub to other tools for reminders and notifications.  
* **External Trigger Mechanism:** The AI system has no internal concept of time. All review cycles (Daily, Weekly, Monthly) are initiated by **external, time-based triggers**. These are API calls or webhooks sent from time-aware applications like Google Calendar, Cron jobs, or other schedulers. This process is governed by SOP-INT-002: The System Trigger Protocol and managed by the system's dedicated Scheduling Agent.

---

#### **3.0 The Daily Review Cycle (DRC)**

* **Objective:** A lightweight, \<15-minute process to close the day's operational loops, clear cognitive buffers, and set the stage for the next day.  
* **Trigger:** An external time-based trigger fires at the end of the workday.  
* **Procedure:**  
  1. **AI-Generated Draft:** Upon receiving the trigger, the Integrity Agent automatically creates a new entry in the Review Hub, pre-populating it with the day's logged data.  
  2. **Operator Review & Augmentation (5-10 mins):** The operator reviews the draft and answers qualitative questions about wins, friction points, and priorities.  
  3. **System Commit:** The operator marks the review as "Complete."  
* **Grace Mode Protocol (Missed Daily Review):**  
  * If a DRC is missed, a **"Grace Mode Activated"** banner appears in the Review Hub.  
  * The next day, the AI offers an **"AI-Assisted Catch-up"** to summarize the missed reflection, preventing backlog.  
  * If three consecutive DRCs are missed, the issue is escalated to the Weekly Review to flag a pattern of "System-Operator Desynchronization".

---

#### **4.0 The Weekly Review Cycle (WRC)**

* **Objective:** A 30-45 minute strategic review to analyze trends and adjust tactical priorities.  
* **Trigger:** An external time-based trigger fires at the end of the work week.  
* **Procedure:**  
  1. **AI-Synthesized Weekly Brief:** The Integrity Agent generates a comprehensive weekly report with performance metrics and pattern analysis.  
  2. **Strategic Reflection (15-20 mins):** The operator reviews the brief to assess progress against quarterly objectives and identify key adjustments.  
  3. **Action & Allocation:** The operator defines priorities for the next week.  
* **Grace Mode Protocol (Missed Weekly Review):**  
  * A missed WRC triggers a **"Strategic Alignment Alert"** banner.  
  * The system blocks the initiation of the next week's plan until a **"Compressed WRC"** is completed (a 15-minute, AI-guided walkthrough).

---

#### **5.0 The Monthly Review Cycle (MRC)**

* **Objective:** A 60-90 minute deep-dive into long-term performance and system integrity.  
* **Trigger:** An external time-based trigger fires on the last Friday of the month.  
* **Procedure:**  
  1. **AI-Generated Performance Dossier:** The Integrity Agent prepares a detailed analysis comparing the current month to previous months.  
  2. **Full System Audit:** Guided by the AI, the operator conducts a full audit of the system's governance and protocols.  
  3. **SOP Updates & Roadmap Definition:** The operator makes formal updates to any SOPs and defines the strategic roadmap for the next quarter.
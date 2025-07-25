

### **SOP-ARC-001: The System Architecture & Modularity Protocol**

Version: 2.0 (Production Build)  
Status: ACTIVE, GOVERNED  
Governing Protocols: NOTREKT.AI Master Operating System \- Part I: The Constitution  
Description: This document defines the official system architecture for the NOTREKT.AI Operating System. It enforces the "Framework, not Library" philosophy by codifying the roles, boundaries, and interaction protocols for all system components. Adherence to this protocol is mandatory for the integration of any new agent, module, or workflow to ensure system integrity, scalability, and governance. This is the master blueprint of the OS.

---

#### **Article 1: The Core Architectural Principle: Inversion of Control**

* **1.1 Principle of "Framework, Not Library":**  
  * The system is architected as a cohesive framework with a central **Governance Core**. This Core dictates the overall architecture and flow of control.  
  * All other components, including AI agents and specialized modules, function as compliant plugins to this Core. They do not operate independently or initiate their own workflows in an ad-hoc manner.  
* **1.2 Principle of "Inversion of Control" (The "Don't call us, we'll call you" principle):**  
  * Agents and modules remain in a dormant, stateless mode until explicitly activated and called upon by the Governance Core.  
  * This principle is the primary technical safeguard against unauthorized, untracked, or rogue agent behavior. It ensures that every operation is centrally managed, logged, and governed from the top down, making the entire system predictable and auditable by design.  
* **1.3 Principle of "Black-Box Modularity" & MECE:**  
  * Each agent and protocol must be designed as a self-contained, composable, and loosely coupled component with a standardized interface. This allows any module to be updated, replaced, or audited independently without destabilizing the entire system.  
  * The roles of each agent must be **Mutually Exclusive** (non-overlapping) and, as a whole, **Collectively Exhaustive** (covering all system functions without gaps).

#### **Article 2: The Three Foundational Tiers of the Architecture**

The system is organized into three distinct architectural tiers, creating a clear hierarchy of governance, orchestration, and execution.

* **2.1 Tier 1: The Governance Core:**  
  * **Description:** The system's central nervous system and the primary execution engine. It is the sole authority for initiating workflows and enforcing the Constitution.  
  * **Components:**  
    * **Master Policy Engine:** The component that programmatically validates every proposed agent action against the Constitution (Part I) and the Situational Logic Library (Part III) of the Master OS.  
    * **Master Orchestrator:** Manages the lifecycle of all agents, activating and coordinating them according to approved workflow plans. It is the technical implementation of the "Inversion of Control" principle.  
    * **The Integrity Agent (SOP-GOV-001):** While governed by its own protocol, this agent functions at the Core tier, serving as the system's active auditor and resilience enforcer.  
* **2.2 Tier 2: The Orchestration & Interface Layer:**  
  * **Description:** The "API layer" of the system that connects the high-level governance to the low-level execution. It manages time, triggers, and inter-agent communication.  
  * **Components:**  
    * **The Scheduling Agent:** The master of all time and scheduling. It is the single source of truth for the operational grid. It receives schedule requests from other agents, resolves all time-based conflicts based on a predefined priority hierarchy, and pushes the final, locked schedule to all executor agents.  
    * **The Trigger Protocol (SOP-INT-002 logic):** A rule-based engine that maps specific inputs (e.g., a new file, a user command, a scheduled event) to the activation of a specific agent or workflow.  
    * **The Fusion Protocol (SOP-INT-003 logic):** Governs all agent-to-agent communication, defining the hierarchy of authority and the rules for data sharing and escalation to prevent system deadlocks.  
* **2.3 Tier 3: The Execution Layer (The Agent Stack):**  
  * **Description:** A collection of specialized, plug-and-play AI agents that perform specific, well-defined tasks. Each agent is a self-contained module that is called by the Orchestration Layer and governed by the Core.  
  * **Required Agent Roles:**  
    * **The Physical Executor Agent:** Manages all protocols related to physical performance and real-world logistics.  
    * **The Cognitive Executor Agent:** Manages all learning objectives, creative work, and project-based execution.  
    * **The Maintenance Agent:** Manages all system maintenance, personal care routines, and environmental upkeep.  
    * **The Knowledge Core Agent:** The non-executing research engine and internal "source of truth" that provides the underlying logic and rationale for system rules.

#### **Article 3: The Data & Memory Architecture**

This architecture runs in parallel to the three tiers, serving as the foundational layer for persistence, auditability, and knowledge grounding.

* **3.1 The Two-Part Memory Engine:**  
  * **The Immutable Log Store:** The WORM-compliant, append-only ledger for the system's unalterable audit trail (History).  
  * **The Dynamic Knowledge Corpus:** The vector-based, semantically searchable index of the log store, enabling long-term context and RAG capabilities (Memory).  
* **3.2 The Web-Grounded RAG Protocol:**  
  * The mandatory protocol for any agent in the Execution Layer that needs to access current, external information. It requires source triangulation, citation, and synthesis to ensure all external data is verified before being used.

#### **Article 4: System Integrity & Scalability Directives**

* **4.1 Mandate for Full Observability:** The architecture must support end-to-end traceability for every action. An auditor must be able to trace any output back through the execution chain—from the agent's action log, through the interface layer's instruction, to the governance core's initial check—to its original input.  
* **4.2 The "Scan Before Integration" Protocol:** Any new agent or protocol proposed for integration into the system must first be subjected to a rigorous scan by the **Sentinel Agent** (the proactive optimization agent). This scan tests for logical contradictions, security vulnerabilities, and compliance with the Constitution. A new module cannot be deployed until it passes this scan, preventing architectural drift and ensuring system integrity over time.

---

This protocol is now locked. It provides the immutable blueprint for the structure and interaction of all components within the NOTREKT.AI Operating System.
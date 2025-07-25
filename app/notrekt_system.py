#!/usr/bin/env python3
"""
NOTREKT.AI v2.0 - Core System Implementation
Production-ready governance system with HITL workflow and secure audit logging.
"""

import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import asyncio

from .config_manager import Config, logger
from .worm_storage import WORMStorage
from .cgo_agent import CGOAgent, ValidationResult

@dataclass
class PendingAction:
    """Represents an action pending human approval."""
    action_id: str
    action_name: str
    metadata: Dict[str, Any]
    risk_tier: str
    timestamp: str
    validation_result: ValidationResult
    user_context: Optional[Dict[str, Any]] = None

class NotRektAISystem:
    """
    Main orchestrator for the NOTREKT.AI v2.0 governance system.
    Implements the complete GOVERN -> HITL -> EXECUTE -> LOG workflow.
    """
    
    def __init__(self):
        logger.info("NOTREKT.AI v2.0 System initializing...")
        
        # Validate configuration
        is_valid, errors = Config.validate_config()
        if not is_valid:
            logger.critical("Configuration validation failed:")
            for error in errors:
                logger.critical(f"  - {error}")
            raise RuntimeError("Invalid configuration. Please check environment variables.")
        
        # Initialize core components
        self.worm_storage = WORMStorage()
        self.cgo_agent = CGOAgent()
        
        # In-memory storage for pending actions (in production, use Redis or database)
        self.pending_actions: Dict[str, PendingAction] = {}
        
        logger.info("NOTREKT.AI v2.0 System ready")
        logger.info("🔒 Governance Layer: ACTIVE")
        logger.info("📝 Audit Trail: ENABLED")
        logger.info("👤 Human-in-the-Loop: ENABLED")
    
    async def process_action(
        self,
        action_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an action through the complete governance workflow:
        1. GOVERN: Validate with CGO Agent
        2. HITL: Queue for human approval if required
        3. LOG: Record the decision and outcome
        4. EXECUTE: Perform the action if approved
        
        Returns: Dictionary with processing result and action details
        """
        if metadata is None:
            metadata = {}
        
        action_id = str(uuid.uuid4())
        
        logger.info(f"Processing action: {action_name} (ID: {action_id})")
        
        # STEP 1: GOVERN - CGO Agent Validation
        validation_result = self.cgo_agent.validate_action(action_name, metadata, user_context)
        
        # Handle blocked actions
        if validation_result.blocked:
            logger.warning(f"Action blocked: {validation_result.reasoning}")
            
            event_id = self.worm_storage.log_event(
                action_name=action_name,
                status="BREACH",
                metadata={
                    "reason": validation_result.reasoning,
                    "user_context": user_context,
                    **metadata
                },
                risk_tier=validation_result.risk_tier,
                requires_approval=validation_result.requires_approval,
                action_id=action_id
            )
            
            return {
                "status": "blocked",
                "action_id": action_id,
                "event_id": event_id,
                "message": validation_result.reasoning,
                "risk_tier": validation_result.risk_tier
            }
        
        # Handle validation failures
        if not validation_result.is_valid:
            logger.warning(f"Validation failed: {validation_result.reasoning}")
            
            event_id = self.worm_storage.log_event(
                action_name=action_name,
                status="BREACH",
                metadata={
                    "reason": validation_result.reasoning,
                    "missing_metadata": validation_result.missing_metadata,
                    "user_context": user_context,
                    **metadata
                },
                risk_tier=validation_result.risk_tier,
                requires_approval=validation_result.requires_approval,
                action_id=action_id
            )
            
            return {
                "status": "validation_failed",
                "action_id": action_id,
                "event_id": event_id,
                "message": validation_result.reasoning,
                "missing_metadata": validation_result.missing_metadata,
                "risk_tier": validation_result.risk_tier
            }
        
        logger.info(f"CGO validation passed - Risk Tier: {validation_result.risk_tier}")
        
        # STEP 2: HUMAN-IN-THE-LOOP (HITL) - If Required
        if validation_result.requires_approval:
            logger.info(f"Action requires human approval - queuing for review")
            
            # Store pending action
            pending_action = PendingAction(
                action_id=action_id,
                action_name=action_name,
                metadata=metadata,
                risk_tier=validation_result.risk_tier,
                timestamp=datetime.utcnow().isoformat() + "Z",
                validation_result=validation_result,
                user_context=user_context
            )
            
            self.pending_actions[action_id] = pending_action
            
            # Log pending status
            event_id = self.worm_storage.log_event(
                action_name=action_name,
                status="PENDING",
                metadata={
                    "pending_reason": "Human approval required",
                    "user_context": user_context,
                    **metadata
                },
                risk_tier=validation_result.risk_tier,
                requires_approval=True,
                action_id=action_id
            )
            
            return {
                "status": "pending_approval",
                "action_id": action_id,
                "event_id": event_id,
                "message": "Action pending human approval",
                "risk_tier": validation_result.risk_tier,
                "approval_required": True
            }
        
        # STEP 3: AUTO-EXECUTE for low-risk actions
        return await self._execute_action(action_id, action_name, metadata, validation_result, user_context)
    
    async def approve_action(
        self,
        action_id: str,
        human_decision: str,
        approver_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process human approval for a pending action.
        
        Args:
            action_id: ID of the pending action
            human_decision: "APPROVE" or "DENY"
            approver_context: Context about the approver (role, ID, etc.)
        """
        if action_id not in self.pending_actions:
            logger.error(f"Action ID not found in pending actions: {action_id}")
            return {
                "status": "error",
                "message": f"Action ID {action_id} not found in pending actions"
            }

        pending_action = self.pending_actions[action_id]

        logger.info(f"Processing human decision for action {action_id}: {human_decision}")

        # Defensive: ensure approver_context is a dict if not None
        safe_approver_context: Optional[Dict[str, Any]] = approver_context if approver_context is not None else None

        # Log the human decision
        decision_event_id = self.worm_storage.log_event(
            action_name=pending_action.action_name,
            status="APPROVED" if human_decision.upper() == "APPROVE" else "DENIED",
            metadata={
                "human_decision": human_decision,
                "approver_context": safe_approver_context,
                "original_metadata": pending_action.metadata,
                "user_context": pending_action.user_context,
                "original_action_id": action_id
            },
            risk_tier=pending_action.risk_tier,
            requires_approval=True
        )

        # Remove from pending actions
        del self.pending_actions[action_id]

        if human_decision.upper() == "DENY":
            logger.info(f"Action {action_id} denied by human reviewer")
            return {
                "status": "denied",
                "action_id": action_id,
                "event_id": decision_event_id,
                "message": "Action denied by human reviewer"
            }

        # Execute the approved action
        logger.info(f"Action {action_id} approved - executing...")
        return await self._execute_action(
            action_id,
            pending_action.action_name,
            pending_action.metadata,
            pending_action.validation_result,
            pending_action.user_context,
            human_decision
        )
    
    async def _execute_action(self, action_id: str, action_name: str, metadata: Dict[str, Any], 
                            validation_result: ValidationResult, user_context: Optional[Dict[str, Any]] = None,
                            human_decision: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an approved action and log the results.
        
        This is where the actual business logic would be implemented.
        Currently implements simulation for demonstration purposes.
        """
        logger.info(f"Executing action: {action_name} (ID: {action_id})")
        
        try:
            # Simulate different types of execution based on action name
            execution_result = await self._simulate_execution(action_name, metadata)
            
            # Log successful execution
            success_event_id = self.worm_storage.log_event(
                action_name=action_name,
                status="SUCCESS",
                metadata={
                    "execution_result": execution_result,
                    "human_decision": human_decision,
                    "user_context": user_context,
                    "original_action_id": action_id,
                    **metadata
                },
                risk_tier=validation_result.risk_tier,
                requires_approval=validation_result.requires_approval,
                human_decision=human_decision
            )
            
            logger.info(f"Action {action_id} executed successfully")
            
            return {
                "status": "success",
                "action_id": action_id,
                "event_id": success_event_id,
                "message": "Action executed successfully",
                "execution_result": execution_result,
                "risk_tier": validation_result.risk_tier
            }
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            
            # Log execution failure
            failure_event_id = self.worm_storage.log_event(
                action_name=action_name,
                status="BREACH",
                metadata={
                    "error": str(e),
                    "failure_reason": "execution_error",
                    "human_decision": human_decision,
                    "user_context": user_context,
                    "original_action_id": action_id,
                    **metadata
                },
                risk_tier=validation_result.risk_tier,
                requires_approval=validation_result.requires_approval,
                human_decision=human_decision
            )
            
            return {
                "status": "execution_failed",
                "action_id": action_id,
                "event_id": failure_event_id,
                "message": f"Execution failed: {e}",
                "risk_tier": validation_result.risk_tier
            }
    
    async def _simulate_execution(self, action_name: str, metadata: Dict[str, Any]) -> str:
        """
        Simulate action execution for demonstration purposes.
        In production, this would contain actual business logic.
        """
        # Add realistic delay to simulate processing
        await asyncio.sleep(0.1)
        
        if action_name.upper() == "RESEARCH":
            topic = metadata.get('topic', 'general topic')
            source = metadata.get('source', 'internal knowledge base')
            return f"Research completed on '{topic}' using source: {source}. Found 15 relevant documents."
        
        elif action_name.upper() == "WRITE_CODE":
            module = metadata.get('module_name', 'main')
            language = metadata.get('language', 'python')
            return f"Code generation completed for module '{module}' in {language}. Generated 150 lines of code."
        
        elif action_name.upper() == "DATA_ANALYSIS":
            dataset = metadata.get('dataset_name', 'default')
            analysis_type = metadata.get('analysis_type', 'summary')
            return f"Data analysis ({analysis_type}) completed on dataset '{dataset}'. Processed 1,250 records."
        
        elif action_name.upper() == "FILE_OPERATIONS":
            operation = metadata.get('operation_type', 'read')
            file_path = metadata.get('file_path', 'unknown')
            return f"File operation '{operation}' completed on '{file_path}'. Operation successful."
        
        elif action_name.upper() == "NETWORK_REQUEST":
            url = metadata.get('url', 'unknown')
            method = metadata.get('method', 'GET')
            return f"Network request ({method}) to '{url}' completed. Response: 200 OK, 2.5KB received."
        
        else:
            return f"Action '{action_name}' executed successfully with provided metadata."
    
    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get all actions pending human approval."""
        pending_list = []
        for action_id, pending_action in self.pending_actions.items():
            pending_list.append({
                "action_id": action_id,
                "action_name": pending_action.action_name,
                "metadata": pending_action.metadata,
                "risk_tier": pending_action.risk_tier,
                "timestamp": pending_action.timestamp,
                "user_context": pending_action.user_context
            })
        
        return sorted(pending_list, key=lambda x: x["timestamp"])
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including audit summary."""
        # Verify integrity
        integrity_valid, integrity_errors = self.worm_storage.verify_integrity()
        
        # Get audit summary
        audit_summary = self.worm_storage.get_audit_summary()
        
        # Calculate compliance score
        total_events = audit_summary["total_events"]
        if total_events > 0:
            successful_rate = (audit_summary["successful_actions"] / total_events) * 100
            compliance_score = max(0, min(100, successful_rate - len(integrity_errors) * 10))
        else:
            compliance_score = 100
        
        return {
            "system_status": "healthy" if integrity_valid else "compromised",
            "integrity_verified": integrity_valid,
            "integrity_errors": integrity_errors,
            "compliance_score": round(compliance_score, 1),
            "audit_summary": audit_summary,
            "pending_actions_count": len(self.pending_actions),
            "configuration_valid": True,  # Already validated during init
            "components": {
                "worm_storage": "active",
                "cgo_agent": "active",
                "governance_layer": "active"
            }
        }
    
    def shutdown(self):
        """Safely shutdown the system."""
        logger.info("NOTREKT.AI v2.0 System shutting down...")
        
        # Log shutdown event
        self.worm_storage.log_event(
            action_name="SYSTEM_SHUTDOWN",
            status="SUCCESS",
            metadata={"shutdown_reason": "normal_shutdown"},
            risk_tier="MINIMAL",
            requires_approval=False
        )
        
        # Close database connections
        self.worm_storage.close()
        
        logger.info("System shutdown complete")

# Convenience function for standalone usage
async def process_action_standalone(
    action_name: str,
    metadata: Optional[Dict[str, Any]] = None,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Standalone function to process an action without maintaining system state.
    Useful for simple integrations.
    """
    system = NotRektAISystem()
    try:
        result = await system.process_action(action_name, metadata, user_context)
        return result
    finally:
        system.shutdown()

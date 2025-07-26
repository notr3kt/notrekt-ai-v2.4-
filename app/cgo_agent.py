#!/usr/bin/env python3
"""
NOTREKT.AI v2.0 - Chief Governance Officer Agent
Enhanced policy enforcement with value-based validation and structured rule processing.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from .config_manager import Config, logger

@dataclass
class ValidationResult:
    """Result of CGO Agent validation."""
    is_valid: bool
    risk_tier: str
    requires_approval: bool
    blocked: bool
    reasoning: str
    missing_metadata: List[str]
    sop_reference: str
    action_id: Optional[str] = None

class CGOAgent:
    """
    Chief Governance Officer Agent - Enhanced policy enforcement.
    Validates actions against structured rules with value-based checks.
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = rules_path or Config.RULES_PATH
        self.rules_data = self._load_rules()
        print(f"[DEBUG] CGOAgent using rules file: {self.rules_path}")
        print(f"[DEBUG] SOP_AS_LAW in rules: {self.rules_data.get('SOP_AS_LAW')}")
        logger.info(f"CGO Agent initialized with {len(self.rules_data.get('rules', []))} governance rules")
    
    def _load_rules(self) -> Dict[str, Any]:
        """Load governance rules from the JSON file."""
        try:
            rules_file = Path(self.rules_path)
            if not rules_file.exists():
                raise FileNotFoundError(f"Rules file not found: {self.rules_path}")
            
            with open(rules_file, 'r') as f:
                rules = json.load(f)
                
            # Validate rules structure
            if not isinstance(rules, dict):
                raise ValueError("Rules file must contain a JSON object")
            
            if "rules" not in rules:
                raise ValueError("Rules file must contain a 'rules' array")
            
            if not isinstance(rules["rules"], list):
                raise ValueError("'rules' must be an array")
            
            logger.info(f"Loaded {len(rules['rules'])} governance rules from {self.rules_path}")
            return rules
            
        except FileNotFoundError as e:
            logger.critical(f"Rules file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON in rules file: {e}")
            raise
        except Exception as e:
            logger.critical(f"Error loading rules: {e}")
            raise
    
    def validate_action(self, action_name: str, metadata: Dict[str, Any], 
                       user_context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate an action against the governance rules with enhanced value-based checking.
        
        Args:
            action_name: Name of the action to validate
            metadata: Action metadata for validation
            user_context: Optional user context (role, permissions, etc.)
        
        Returns:
            ValidationResult with detailed validation outcome
        """
        logger.info(f"CGO Agent validating action: '{action_name}'")
        
        # Check if SOP enforcement is enabled
        if not self.rules_data.get("SOP_AS_LAW", False):
            logger.warning("SOP enforcement is DISABLED - auto-approving action")
            return ValidationResult(
                is_valid=True,
                risk_tier="MINIMAL",
                requires_approval=False,
                blocked=False,
                reasoning="SOP enforcement is disabled. Action auto-approved.",
                missing_metadata=[],
                sop_reference="SOP-GOV-001-DISABLED"
            )
        
        # Find the matching rule for this action
        matching_rule = self._find_matching_rule(action_name)
        
        # If no specific rule found, apply default policy
        if not matching_rule:
            logger.info(f"No specific rule found for '{action_name}' - applying default policy")
            return ValidationResult(
                is_valid=True,
                risk_tier="MINIMAL",
                requires_approval=False,
                blocked=False,
                reasoning=f"No specific rule found for '{action_name}'. Applying minimal risk classification.",
                missing_metadata=[],
                sop_reference="SOP-GOV-001-DEFAULT"
            )
        
        # Check if action is explicitly blocked
        if matching_rule.get("blocked", False):
            logger.warning(f"Action '{action_name}' is explicitly blocked")
            return ValidationResult(
                is_valid=False,
                risk_tier=matching_rule["risk_tier"],
                requires_approval=False,
                blocked=True,
                reasoning=f"Action '{action_name}' is explicitly blocked due to {matching_rule['risk_tier']} risk classification.",
                missing_metadata=[],
                sop_reference=f"SOP-GOV-001-{matching_rule['risk_tier']}"
            )
        
        # Perform enhanced metadata validation
        validation_errors = self._validate_metadata(matching_rule, metadata, user_context)
        
        if validation_errors:
            logger.warning(f"Metadata validation failed for '{action_name}': {validation_errors}")
            return ValidationResult(
                is_valid=False,
                risk_tier=matching_rule["risk_tier"],
                requires_approval=matching_rule.get("requires_human_approval", False),
                blocked=False,
                reasoning=f"Validation failed: {'; '.join(validation_errors)}",
                missing_metadata=self._extract_missing_fields(validation_errors),
                sop_reference=f"SOP-GOV-001-{matching_rule['risk_tier']}"
            )
        
        # All checks passed
        logger.info(f"Action '{action_name}' validated successfully with {matching_rule['risk_tier']} risk tier")
        return ValidationResult(
            is_valid=True,
            risk_tier=matching_rule["risk_tier"],
            requires_approval=matching_rule.get("requires_human_approval", False),
            blocked=False,
            reasoning=f"Action validated successfully with {matching_rule['risk_tier']} risk classification.",
            missing_metadata=[],
            sop_reference=f"SOP-GOV-001-{matching_rule['risk_tier']}"
        )
    
    def _find_matching_rule(self, action_name: str) -> Optional[Dict[str, Any]]:
        """Find the rule that matches the given action name."""
        for rule in self.rules_data.get("rules", []):
            if rule["action_name"].upper() == action_name.upper():
                return rule
        return None
    
    def _validate_metadata(self, rule: Dict[str, Any], metadata: Dict[str, Any], 
                          user_context: Optional[Dict[str, Any]]) -> List[str]:
        """
        Enhanced metadata validation with value-based checks.
        
        Returns list of validation error messages.
        """
        errors = []
        
        # Check required metadata fields
        required_fields = rule.get("required_metadata", [])
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                errors.append(f"Missing required field: {field}")
        
        # Perform value-based validation rules
        validation_rules = rule.get("validation_rules", {})
        
        # Example: User role validation
        if "user_role_required" in validation_rules:
            required_role = validation_rules["user_role_required"]
            user_role = (user_context or {}).get("role")
            if user_role != required_role:
                errors.append(f"Action requires user role '{required_role}', but user has role '{user_role}'")
        
        # Example: Source validation for research actions
        if rule["action_name"].upper() == "RESEARCH":
            source = metadata.get("source")
            if source:
                # Validate source against trusted sources
                trusted_sources = rule.get("trusted_sources", [])
                if trusted_sources and source not in trusted_sources:
                    errors.append(f"Source '{source}' is not in trusted sources list")
        
        # Example: File type validation
        if "allowed_file_types" in validation_rules:
            file_path = metadata.get("file_path")
            if file_path:
                file_extension = Path(file_path).suffix.lower()
                allowed_types = validation_rules["allowed_file_types"]
                if file_extension not in allowed_types:
                    errors.append(f"File type '{file_extension}' not allowed. Allowed types: {allowed_types}")
        
        # Example: Data size validation
        if "max_data_size_mb" in validation_rules:
            data_size = metadata.get("data_size_mb", 0)
            max_size = validation_rules["max_data_size_mb"]
            if data_size > max_size:
                errors.append(f"Data size {data_size}MB exceeds maximum allowed size of {max_size}MB")
        
        # Example: Time-based validation
        if "business_hours_only" in validation_rules and validation_rules["business_hours_only"]:
            from datetime import datetime
            current_hour = datetime.now().hour
            if current_hour < 9 or current_hour > 17:
                errors.append("Action only allowed during business hours (9 AM - 5 PM)")
        
        return errors
    
    def _extract_missing_fields(self, error_messages: List[str]) -> List[str]:
        """Extract missing field names from error messages."""
        missing_fields = []
        for error in error_messages:
            if error.startswith("Missing required field:"):
                field_name = error.split(": ")[1]
                missing_fields.append(field_name)
        return missing_fields
    
    def get_action_requirements(self, action_name: str) -> Dict[str, Any]:
        """
        Get the requirements for a specific action without performing validation.
        Useful for API clients to know what metadata is required.
        """
        rule = self._find_matching_rule(action_name)
        
        if not rule:
            return {
                "action_name": action_name,
                "risk_tier": "MINIMAL",
                "requires_approval": False,
                "required_metadata": [],
                "validation_rules": {},
                "blocked": False
            }
        
        return {
            "action_name": rule["action_name"],
            "risk_tier": rule["risk_tier"],
            "requires_approval": rule.get("requires_human_approval", False),
            "required_metadata": rule.get("required_metadata", []),
            "validation_rules": rule.get("validation_rules", {}),
            "blocked": rule.get("blocked", False)
        }
    
    def list_all_actions(self) -> List[Dict[str, Any]]:
        """List all available actions and their requirements."""
        actions = []
        for rule in self.rules_data.get("rules", []):
            actions.append(self.get_action_requirements(rule["action_name"]))
        return actions
    
    def reload_rules(self) -> bool:
        """Reload rules from file. Returns True if successful."""
        try:
            self.rules_data = self._load_rules()
            logger.info("Rules reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reload rules: {e}")
            return False

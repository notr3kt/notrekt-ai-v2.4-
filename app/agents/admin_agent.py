"""
AdminAgent - Manages SOP versioning, model versioning, and audit object registration.
SOP-GOV-003
"""
class AdminAgent:
    def __init__(self, sop_registry, model_registry):
        self.sop_registry = sop_registry
        self.model_registry = model_registry


    def register_sop_version(self, sop_version):
        """
        Log SOP version as an immutable audit object (SOP-GOV-003).
        """
        from app.utils import audit_utils
        audit_utils.export_audit_log(
            log_path=self.sop_registry,
            export_path=f"sop_version_{sop_version}.json"
        )
        print(f"[AUDIT] SOP version {sop_version} registered and exported.")


    def register_model_version(self, model_version):
        """
        Log model version as an immutable audit object (SOP-GOV-003).
        """
        from app.utils import audit_utils
        audit_utils.export_audit_log(
            log_path=self.model_registry,
            export_path=f"model_version_{model_version}.json"
        )
        print(f"[AUDIT] Model version {model_version} registered and exported.")

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from app.schemas.chat import PolicyDecision, ProposedAction
from app.policies.evaluator import (
    evaluate_high_risk_escalation,
    evaluate_repeated_complaint,
    evaluate_data_export,
    evaluate_account_deletion,
    evaluate_return_approval,
    evaluate_pii_protection,
    evaluate_duplicate_refund,
    evaluate_order_cancellation,
    evaluate_payment_cancellation,
    evaluate_customer_verification,
    evaluate_refund_limit,
    evaluate_delivery_verification,
)

POLICIES_DIR = Path(__file__).parent / "definitions"

class PolicyEngine:
    def __init__(self, definitions_dir: Optional[Path] = None):
        self.definitions_dir = definitions_dir or POLICIES_DIR
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.load_policies()

    def load_policies(self) -> None:
        """Loads YAML policy definitions from disk."""
        self.policies.clear()
        if not self.definitions_dir.exists():
            return

        for file_path in self.definitions_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "policy_id" in data:
                        self.policies[data["policy_id"]] = data
            except Exception as e:
                print(f"Error loading policy {file_path}: {e}")

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        return self.policies.get(policy_id)

    def list_policies(self) -> List[Dict[str, Any]]:
        return list(self.policies.values())

    def evaluate(
        self,
        customer_message: str,
        agent_a_response: str,
        proposed_action: Optional[ProposedAction],
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyDecision:
        """Evaluates all active policies in strict priority order.
        Returns the highest-priority decision (ESCALATE/BLOCK/MODIFY/ALLOW).
        """
        ctx = context or {}
        is_verified = bool(ctx.get("is_verified", False) or ctx.get("customer_verified", False))
        manager_approved = bool(ctx.get("manager_approved", False))

        # 1. DATA_EXPORT_001 (CRITICAL - Always ESCALATE)
        data_export_def = self.policies.get("DATA_EXPORT_001", {
            "policy_id": "DATA_EXPORT_001", "version": "v1.0", "severity": "CRITICAL"
        })
        data_export_dec = evaluate_data_export(proposed_action, data_export_def)
        if data_export_dec:
            return data_export_dec

        # 2. ACCOUNT_DELETION_001 (CRITICAL - Always ESCALATE)
        acct_del_def = self.policies.get("ACCOUNT_DELETION_001", {
            "policy_id": "ACCOUNT_DELETION_001", "version": "v1.0", "severity": "CRITICAL"
        })
        acct_del_dec = evaluate_account_deletion(proposed_action, acct_del_def)
        if acct_del_dec:
            return acct_del_dec

        # 3. HIGH_RISK_ESCALATION_001
        high_risk_def = self.policies.get("HIGH_RISK_ESCALATION_001", {
            "policy_id": "HIGH_RISK_ESCALATION_001", "version": "v1.0", "severity": "CRITICAL"
        })
        high_risk_dec = evaluate_high_risk_escalation(customer_message, agent_a_response, high_risk_def)
        if high_risk_dec:
            return high_risk_dec

        # 4. REPEATED_COMPLAINT_001 (Multi-turn Context Checking)
        rep_comp_def = self.policies.get("REPEATED_COMPLAINT_001", {
            "policy_id": "REPEATED_COMPLAINT_001", "version": "v1.0", "severity": "HIGH",
            "parameters": {"escalation_complaint_threshold": 3}
        })
        rep_comp_dec = evaluate_repeated_complaint(customer_message, ctx, rep_comp_def)
        if rep_comp_dec:
            return rep_comp_dec

        # 5. RETURN_APPROVAL_001
        ret_app_def = self.policies.get("RETURN_APPROVAL_001", {
            "policy_id": "RETURN_APPROVAL_001", "version": "v1.0", "severity": "HIGH"
        })
        ret_app_dec = evaluate_return_approval(proposed_action, is_verified, ret_app_def)
        if ret_app_dec:
            return ret_app_dec

        # 6. PII_PROTECTION_001 (Cross-customer & exposed credentials)
        pii_def = self.policies.get("PII_PROTECTION_001", {
            "policy_id": "PII_PROTECTION_001", "version": "v1.0", "severity": "CRITICAL"
        })
        pii_dec = evaluate_pii_protection(customer_message, agent_a_response, proposed_action, is_verified, ctx, pii_def)
        if pii_dec:
            return pii_dec

        # 7. DUPLICATE_REFUND_001 (Multi-turn Context Checking)
        dup_refund_def = self.policies.get("DUPLICATE_REFUND_001", {
            "policy_id": "DUPLICATE_REFUND_001", "version": "v1.0", "severity": "HIGH"
        })
        dup_refund_dec = evaluate_duplicate_refund(proposed_action, ctx, dup_refund_def)
        if dup_refund_dec:
            return dup_refund_dec

        # 8. ORDER_CANCELLATION_001
        order_canc_def = self.policies.get("ORDER_CANCELLATION_001", {
            "policy_id": "ORDER_CANCELLATION_001", "version": "v1.0", "severity": "HIGH"
        })
        order_canc_dec = evaluate_order_cancellation(proposed_action, is_verified, ctx, order_canc_def)
        if order_canc_dec:
            return order_canc_dec

        # 9. PAYMENT_CANCELLATION_001
        pmt_canc_def = self.policies.get("PAYMENT_CANCELLATION_001", {
            "policy_id": "PAYMENT_CANCELLATION_001", "version": "v1.0", "severity": "HIGH"
        })
        pmt_canc_dec = evaluate_payment_cancellation(proposed_action, manager_approved, is_verified, pmt_canc_def)
        if pmt_canc_dec:
            return pmt_canc_dec

        # 10. CUSTOMER_VERIFICATION_001
        cust_ver_def = self.policies.get("CUSTOMER_VERIFICATION_001", {
            "policy_id": "CUSTOMER_VERIFICATION_001", "version": "v1.0", "severity": "HIGH"
        })
        cust_ver_dec = evaluate_customer_verification(proposed_action, is_verified, ctx, cust_ver_def)
        if cust_ver_dec:
            return cust_ver_dec

        # 11. REFUND_LIMIT_001
        refund_def = self.policies.get("REFUND_LIMIT_001", {
            "policy_id": "REFUND_LIMIT_001", "version": "v1.0", "severity": "HIGH"
        })
        refund_dec = evaluate_refund_limit(proposed_action, manager_approved, is_verified, refund_def)
        if refund_dec:
            return refund_dec

        # 12. DELIVERY_VERIFICATION_001
        deliv_def = self.policies.get("DELIVERY_VERIFICATION_001", {
            "policy_id": "DELIVERY_VERIFICATION_001", "version": "v1.0", "severity": "MEDIUM"
        })
        deliv_dec = evaluate_delivery_verification(agent_a_response, proposed_action, is_verified, ctx, deliv_def)
        if deliv_dec:
            return deliv_dec

        # Default ALLOW
        return PolicyDecision(
            decision="ALLOW",
            policy_id="STANDARD_ALLOW_001",
            policy_version="v1.0",
            severity="LOW",
            risk_level="LOW",
            reason="All policy checks passed successfully.",
            evidence={"checks_performed": ["DATA_EXPORT", "ACCOUNT_DELETION", "HIGH_RISK", "REPEATED_COMPLAINT", "RETURN_APPROVAL", "PII", "DUPLICATE_REFUND", "ORDER_CANCELLATION", "PAYMENT_CANCELLATION", "VERIFICATION", "REFUND", "DELIVERY"]},
            requires_human_review=False
        )

policy_engine = PolicyEngine()

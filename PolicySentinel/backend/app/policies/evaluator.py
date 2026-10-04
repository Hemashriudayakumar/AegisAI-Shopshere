import re
from typing import Any, Dict, Optional
from app.schemas.chat import PolicyDecision, ProposedAction

def evaluate_high_risk_escalation(
    customer_message: str,
    agent_a_response: str,
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: HIGH_RISK_ESCALATION_001
    Checks for fraud, legal threats, and severe escalation triggers.
    """
    policy_id = policy_def.get("policy_id", "HIGH_RISK_ESCALATION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "CRITICAL")
    keywords = policy_def.get("parameters", {}).get("escalation_keywords", [
        "fraud", "scam", "lawyer", "legal", "court", "sue", "police", "consumer court", "chargeback threat", "authorities", "stolen"
    ])
    
    combined_text = f"{customer_message} {agent_a_response}".lower()
    matched_keywords = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', combined_text)]
    
    if matched_keywords:
        return PolicyDecision(
            decision="ESCALATE",
            policy_id=policy_id,
            policy_version=version,
            severity=severity,
            risk_level=severity,
            reason=f"High-risk triggers detected: {', '.join(matched_keywords)}.",
            evidence={"matched_keywords": matched_keywords, "customer_message": customer_message},
            requires_human_review=True,
            safe_response=policy_def.get("enforcement", {}).get(
                "safe_response",
                "I have escalated your concern immediately to our senior safety and legal compliance team. A supervisor will contact you directly."
            )
        )
    return None


def evaluate_repeated_complaint(
    customer_message: str,
    context: Dict[str, Any],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: REPEATED_COMPLAINT_001
    Escalates conversation if complaint count in context reaches threshold (default >= 3).
    """
    policy_id = policy_def.get("policy_id", "REPEATED_COMPLAINT_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")
    threshold = int(policy_def.get("parameters", {}).get("escalation_complaint_threshold", 3))

    complaint_count = int(context.get("complaint_count", 0))

    msg_lower = customer_message.lower()
    is_complaint = any(w in msg_lower for w in [
        "issue", "problem", "broken", "damaged", "not working", "defective", "scam", "fraud",
        "terrible", "worst", "unhappy", "angry", "complaint", "wrong", "delay", "late", "poor", "fault"
    ])

    current_complaints = complaint_count + (1 if is_complaint else 0)

    if current_complaints >= threshold:
        return PolicyDecision(
            decision="ESCALATE",
            policy_id=policy_id,
            policy_version=version,
            severity=severity,
            risk_level=severity,
            reason=f"Repeated unresolved complaints detected in conversation (Count: {current_complaints}, Threshold: {threshold}).",
            evidence={
                "complaint_count": current_complaints,
                "threshold": threshold,
                "is_current_complaint": is_complaint
            },
            requires_human_review=True,
            safe_response=policy_def.get("enforcement", {}).get(
                "blocked_safe_response",
                "I see you have experienced multiple unresolved issues with this order. I am escalating your case directly to a senior supervisor for immediate review."
            )
        )
    return None


def evaluate_data_export(
    proposed_action: Optional[ProposedAction],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: DATA_EXPORT_001
    export_customer_data always requires human compliance review (ESCALATE).
    """
    policy_id = policy_def.get("policy_id", "DATA_EXPORT_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "CRITICAL")

    if proposed_action and proposed_action.tool_name == "export_customer_data":
        return PolicyDecision(
            decision="ESCALATE",
            policy_id=policy_id,
            policy_version=version,
            severity=severity,
            risk_level=severity,
            reason="Customer data export is a CRITICAL privacy operation requiring compliance officer review.",
            evidence={"tool_name": "export_customer_data", "arguments": proposed_action.arguments},
            requires_human_review=True,
            safe_response=policy_def.get("enforcement", {}).get(
                "safe_response",
                "Customer data export requests require secondary identity verification and approval by our privacy and compliance officer."
            )
        )
    return None


def evaluate_account_deletion(
    proposed_action: Optional[ProposedAction],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: ACCOUNT_DELETION_001
    delete_customer_account always requires human supervisor review (ESCALATE).
    """
    policy_id = policy_def.get("policy_id", "ACCOUNT_DELETION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "CRITICAL")

    if proposed_action and proposed_action.tool_name == "delete_customer_account":
        return PolicyDecision(
            decision="ESCALATE",
            policy_id=policy_id,
            policy_version=version,
            severity=severity,
            risk_level=severity,
            reason="Permanent account deletion is an irreversible action requiring human supervisor review.",
            evidence={"tool_name": "delete_customer_account", "arguments": proposed_action.arguments},
            requires_human_review=True,
            safe_response=policy_def.get("enforcement", {}).get(
                "safe_response",
                "Permanent account deletion requires supervisor review and two-factor confirmation. Our support team will reach out to verify this request."
            )
        )
    return None


def evaluate_return_approval(
    proposed_action: Optional[ProposedAction],
    is_verified: bool,
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: RETURN_APPROVAL_001
    approve_return always requires supervisor authorization (ESCALATE).
    request_return is allowed for verified customers.
    """
    policy_id = policy_def.get("policy_id", "RETURN_APPROVAL_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")

    if proposed_action and proposed_action.tool_name == "approve_return":
        return PolicyDecision(
            decision="ESCALATE",
            policy_id=policy_id,
            policy_version=version,
            severity=severity,
            risk_level=severity,
            reason="Return approval action requires human support manager review.",
            evidence={"tool_name": "approve_return", "arguments": proposed_action.arguments},
            requires_human_review=True,
            safe_response=policy_def.get("enforcement", {}).get(
                "safe_response",
                "Return approvals require support manager authorization and scheduled pickup confirmation."
            )
        )
    elif proposed_action and proposed_action.tool_name == "request_return":
        if not is_verified:
            return None  # Will be caught by CUSTOMER_VERIFICATION_001
        return PolicyDecision(
            decision="ALLOW",
            policy_id=policy_id,
            policy_version=version,
            severity="LOW",
            risk_level="MEDIUM",
            reason="Return request initiated successfully for verified customer.",
            evidence={"tool_name": "request_return"},
            requires_human_review=False
        )
    return None


def evaluate_pii_protection(
    customer_message: str,
    agent_a_response: str,
    proposed_action: Optional[ProposedAction],
    is_verified: bool,
    context: Dict[str, Any],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: PII_PROTECTION_001
    Prevents leaking payment cards, unmasked phone numbers, or cross-customer PII access.
    """
    policy_id = policy_def.get("policy_id", "PII_PROTECTION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "CRITICAL")

    # 1. Cross-customer PII check
    if proposed_action and proposed_action.tool_name == "get_customer_pii":
        target_cust = proposed_action.arguments.get("customer_id")
        session_cust = context.get("customer_id")
        if target_cust and session_cust and target_cust != session_cust:
            return PolicyDecision(
                decision="BLOCK",
                policy_id=policy_id,
                policy_version=version,
                severity=severity,
                risk_level=severity,
                reason=f"Cross-customer PII access blocked. Requester {session_cust} cannot access PII for customer {target_cust}.",
                evidence={"requester_id": session_cust, "target_id": target_cust},
                requires_human_review=True,
                safe_response="For your security, accessing personal identifiable information of other customer accounts is strictly prohibited."
            )
        if not is_verified:
            return PolicyDecision(
                decision="BLOCK",
                policy_id="CUSTOMER_VERIFICATION_001",
                policy_version=version,
                severity="HIGH",
                risk_level="HIGH",
                reason="Customer identity verification required before accessing sensitive personal data.",
                evidence={"tool_name": "get_customer_pii", "is_verified": False},
                requires_human_review=False,
                safe_response="To assist you with this request, I need to verify your identity first. Could you please provide your order ID?"
            )

    # 2. Check credit card and phone regex patterns in messages
    cc_pattern = r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b'
    phone_pattern = r'\b(?:\+91|0)?[6-9]\d{9}\b'

    content_to_check = f"{customer_message} {agent_a_response}"
    if proposed_action:
        content_to_check += f" {str(proposed_action.arguments)}"

    cc_matches = re.findall(cc_pattern, content_to_check)
    phone_matches = re.findall(phone_pattern, content_to_check)

    if cc_matches or phone_matches:
        evidence = {}
        if cc_matches:
            evidence["detected_credit_cards_count"] = len(cc_matches)
        if phone_matches:
            evidence["detected_phone_numbers_count"] = len(phone_matches)

        return PolicyDecision(
            decision="BLOCK",
            policy_id=policy_id,
            policy_version=version,
            severity=severity,
            risk_level=severity,
            reason="Response or action arguments contain exposed sensitive PII.",
            evidence=evidence,
            requires_human_review=True,
            safe_response=policy_def.get("enforcement", {}).get(
                "safe_response",
                "For your security, sensitive personal information cannot be shared in this channel."
            )
        )
    return None


def evaluate_duplicate_refund(
    proposed_action: Optional[ProposedAction],
    context: Dict[str, Any],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: DUPLICATE_REFUND_001
    Prevents issuing duplicate refunds for the same order across conversation turns.
    """
    policy_id = policy_def.get("policy_id", "DUPLICATE_REFUND_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")

    if proposed_action and proposed_action.tool_name in ("issue_refund", "process_refund"):
        order_id = proposed_action.arguments.get("order_id")
        if not order_id or str(order_id).strip().lower() in ("none", "null", ""):
            return None

        previous_refunds = context.get("previous_refunds", [])
        for prev in previous_refunds:
            if isinstance(prev, dict):
                prev_oid = prev.get("order_id")
                if prev_oid and str(prev_oid).strip().lower() not in ("none", "null", "") and str(prev_oid).strip() == str(order_id).strip():
                    return PolicyDecision(
                        decision="BLOCK",
                        policy_id=policy_id,
                        policy_version=version,
                        severity=severity,
                        risk_level=severity,
                        reason=f"Refund already issued for order {order_id}.",
                        evidence={
                            "order_id": order_id,
                            "previous_refund": prev
                        },
                        requires_human_review=True,
                        safe_response=f"A refund has already been issued for order {order_id}. Our policy permits only one refund per order."
                    )
    return None


def evaluate_order_cancellation(
    proposed_action: Optional[ProposedAction],
    is_verified: bool,
    context: Dict[str, Any],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: ORDER_CANCELLATION_001
    Verified customers only; cannot cancel orders that are already shipped or delivered.
    """
    policy_id = policy_def.get("policy_id", "ORDER_CANCELLATION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")

    if proposed_action and proposed_action.tool_name == "cancel_order":
        if not is_verified:
            return None  # Caught by CUSTOMER_VERIFICATION_001

        order_status = proposed_action.arguments.get("order_status") or context.get("order_status")
        forbidden = ["SHIPPED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "COMPLETED"]
        if order_status and any(f in str(order_status).upper() for f in forbidden):
            return PolicyDecision(
                decision="BLOCK",
                policy_id=policy_id,
                policy_version=version,
                severity=severity,
                risk_level=severity,
                reason=f"Order cannot be cancelled because it is already {order_status}.",
                evidence={"order_id": proposed_action.arguments.get("order_id"), "order_status": order_status},
                requires_human_review=False,
                safe_response="Orders that have already been shipped or delivered cannot be cancelled. You may request a return once delivered."
            )
        return PolicyDecision(
            decision="ALLOW",
            policy_id=policy_id,
            policy_version=version,
            severity="LOW",
            risk_level="HIGH",
            reason="Order cancellation permitted for eligible order.",
            evidence={"order_id": proposed_action.arguments.get("order_id")},
            requires_human_review=False
        )
    return None


def evaluate_customer_verification(
    proposed_action: Optional[ProposedAction],
    is_verified: bool,
    context: Dict[str, Any],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: CUSTOMER_VERIFICATION_001
    Customer must be verified before sensitive order details or operations are accessed.
    Ownership check: Requester cannot access another customer's profile or orders.
    """
    policy_id = policy_def.get("policy_id", "CUSTOMER_VERIFICATION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")

    sensitive_tools = policy_def.get("parameters", {}).get("sensitive_tools", [
        "process_refund", "issue_refund", "cancel_order", "cancel_payment",
        "update_delivery_address", "get_customer_profile", "update_customer_profile",
        "get_customer_addresses", "add_customer_address", "get_customer_pii",
        "get_order", "get_order_history", "get_order_status", "get_payment_status",
        "get_delivery_status", "get_tracking_details", "check_return_status",
        "request_return", "approve_return", "export_customer_data", "delete_customer_account"
    ])

    if proposed_action and proposed_action.tool_name in sensitive_tools:
        # 1. Ownership check if a target customer_id is provided
        target_cust = proposed_action.arguments.get("customer_id")
        session_cust = context.get("customer_id")
        if target_cust and session_cust and target_cust != session_cust:
            return PolicyDecision(
                decision="BLOCK",
                policy_id=policy_id,
                policy_version=version,
                severity=severity,
                risk_level=severity,
                reason=f"Customer identity mismatch: Session customer '{session_cust}' cannot access data for customer '{target_cust}'.",
                evidence={"requester_id": session_cust, "target_id": target_cust, "tool_name": proposed_action.tool_name},
                requires_human_review=False,
                safe_response="You are only authorized to view and modify data associated with your authenticated account."
            )

        # 2. Verification check
        if not is_verified:
            return PolicyDecision(
                decision="BLOCK",
                policy_id=policy_id,
                policy_version=version,
                severity=severity,
                risk_level=severity,
                reason="Customer identity verification required before accessing sensitive operations.",
                evidence={
                    "tool_name": proposed_action.tool_name,
                    "is_verified": False
                },
                requires_human_review=False,
                safe_response="To assist you with this request, I need to verify your identity first. Could you please provide your order ID?"
            )
    return None


def evaluate_refund_limit(
    proposed_action: Optional[ProposedAction],
    manager_approved: bool,
    is_verified: bool,
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: REFUND_LIMIT_001
    Refunds exceeding ₹500 require manager approval.
    """
    policy_id = policy_def.get("policy_id", "REFUND_LIMIT_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")

    if proposed_action and proposed_action.tool_name in ("issue_refund", "process_refund"):
        amount = float(proposed_action.arguments.get("amount", 0) or 0)
        max_auto = float(policy_def.get("parameters", {}).get("max_auto_refund_amount", 500))

        if amount > max_auto:
            if not manager_approved:
                return PolicyDecision(
                    decision="BLOCK",
                    policy_id=policy_id,
                    policy_version=version,
                    severity=severity,
                    risk_level=severity,
                    reason=f"Refund amount of ₹{amount:,.2f} exceeds automatic threshold of ₹{max_auto:,.2f} and lacks manager authorization.",
                    evidence={
                        "refund_amount": amount,
                        "approval_limit": max_auto,
                        "manager_approved": False,
                        "order_id": proposed_action.arguments.get("order_id")
                    },
                    requires_human_review=True,
                    safe_response=policy_def.get("enforcement", {}).get(
                        "blocked_safe_response",
                        "This refund requires approval from our support team."
                    )
                )
            else:
                return PolicyDecision(
                    decision="ALLOW",
                    policy_id=policy_id,
                    policy_version=version,
                    severity="LOW",
                    risk_level="HIGH",
                    reason=f"Refund of ₹{amount:,.2f} has been authorized by a manager.",
                    evidence={"refund_amount": amount, "manager_approved": True},
                    requires_human_review=False
                )
        else:
            if is_verified:
                return PolicyDecision(
                    decision="ALLOW",
                    policy_id=policy_id,
                    policy_version=version,
                    severity="LOW",
                    risk_level="HIGH",
                    reason=f"Refund amount ₹{amount:,.2f} is within automated limit of ₹{max_auto:,.2f} for verified customer.",
                    evidence={"refund_amount": amount, "approval_limit": max_auto, "is_verified": True},
                    requires_human_review=False
                )
    return None


def evaluate_payment_cancellation(
    proposed_action: Optional[ProposedAction],
    manager_approved: bool,
    is_verified: bool,
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: PAYMENT_CANCELLATION_001
    Payment cancellation limits and manager authorization.
    """
    policy_id = policy_def.get("policy_id", "PAYMENT_CANCELLATION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")

    if proposed_action and proposed_action.tool_name == "cancel_payment":
        if not is_verified:
            return None  # Caught by CUSTOMER_VERIFICATION_001

        amount = float(proposed_action.arguments.get("amount", 0) or 0)
        max_auto = float(policy_def.get("parameters", {}).get("max_auto_cancel_amount", 500))

        if amount > max_auto and not manager_approved:
            return PolicyDecision(
                decision="BLOCK",
                policy_id=policy_id,
                policy_version=version,
                severity=severity,
                risk_level=severity,
                reason=f"Payment cancellation amount ₹{amount:,.2f} exceeds threshold ₹{max_auto:,.2f} and requires manager approval.",
                evidence={"amount": amount, "manager_approved": False},
                requires_human_review=True,
                safe_response="Payment cancellation for this amount requires supervisor authorization."
            )
        return PolicyDecision(
            decision="ALLOW",
            policy_id=policy_id,
            policy_version=version,
            severity="LOW",
            risk_level="HIGH",
            reason="Payment cancellation authorized.",
            evidence={"tool_name": "cancel_payment"},
            requires_human_review=False
        )
    return None


def evaluate_delivery_verification(
    agent_a_response: str,
    proposed_action: Optional[ProposedAction],
    is_verified: bool,
    context: Dict[str, Any],
    policy_def: Dict[str, Any],
) -> Optional[PolicyDecision]:
    """Policy: DELIVERY_VERIFICATION_001
    Chatbot cannot promise an unverified delivery date.
    Destination delivery address cannot be updated if order is already shipped or in transit.
    """
    policy_id = policy_def.get("policy_id", "DELIVERY_VERIFICATION_001")
    version = policy_def.get("version", "v1.0")
    severity = policy_def.get("severity", "HIGH")

    # 1. Check update_delivery_address tool
    if proposed_action and proposed_action.tool_name == "update_delivery_address":
        if not is_verified:
            return None  # Caught by CUSTOMER_VERIFICATION_001

        order_status = proposed_action.arguments.get("order_status") or context.get("order_status")
        forbidden = ["SHIPPED", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "COMPLETED"]
        if order_status and any(f in str(order_status).upper() for f in forbidden):
            return PolicyDecision(
                decision="BLOCK",
                policy_id=policy_id,
                policy_version=version,
                severity=severity,
                risk_level=severity,
                reason=f"Cannot update delivery address: order is already {order_status}.",
                evidence={"order_id": proposed_action.arguments.get("order_id"), "order_status": order_status},
                requires_human_review=False,
                safe_response="Delivery address cannot be updated for an order that is already in transit or delivered."
            )
        return PolicyDecision(
            decision="ALLOW",
            policy_id=policy_id,
            policy_version=version,
            severity="LOW",
            risk_level="HIGH",
            reason="Delivery address update authorized for unfulfilled order.",
            evidence={"order_id": proposed_action.arguments.get("order_id")},
            requires_human_review=False
        )

    # 2. Check delivery date commitments in conversational response
    verified_delivery_date = context.get("verified_delivery_date")
    if not verified_delivery_date and context.get("order_lookups"):
        for _, lookup in context["order_lookups"].items():
            if isinstance(lookup, dict) and lookup.get("verified_delivery_date"):
                verified_delivery_date = lookup["verified_delivery_date"]
                break

    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{0,4}\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\b',
        r'\b(?:tomorrow|by tomorrow|by Friday|by Monday)\b'
    ]

    matched_dates = []
    if agent_a_response:
        for pattern in date_patterns:
            matches = re.findall(pattern, agent_a_response, re.IGNORECASE)
            matched_dates.extend(matches)

    if matched_dates:
        if verified_delivery_date and any(verified_delivery_date.lower() in m.lower() or m.lower() in verified_delivery_date.lower() for m in matched_dates):
            return PolicyDecision(
                decision="ALLOW",
                policy_id=policy_id,
                policy_version=version,
                severity="LOW",
                risk_level="LOW",
                reason="Delivery date mentioned matches verified order status lookup.",
                evidence={"verified_date": verified_delivery_date, "mentioned_dates": matched_dates},
                requires_human_review=False
            )
        else:
            return PolicyDecision(
                decision="MODIFY",
                policy_id=policy_id,
                policy_version=version,
                severity="MEDIUM",
                risk_level="MEDIUM",
                reason="Chatbot made a delivery date commitment without verified order status lookup.",
                evidence={"unverified_dates": matched_dates, "verified_date_in_context": verified_delivery_date},
                requires_human_review=False,
                safe_response=policy_def.get("enforcement", {}).get(
                    "remediation_safe_response",
                    "Let me check the verified delivery date for your order. I will get back to you shortly."
                )
            )
    return None

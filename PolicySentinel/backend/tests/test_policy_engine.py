import pytest
from app.policies.engine import policy_engine
from app.schemas.chat import ProposedAction

def test_refund_limit_blocked_without_manager():
    """Test 1: ₹3,000 refund without manager approval -> BLOCK."""
    proposed = ProposedAction(tool_name="issue_refund", arguments={"order_id": "ORD-101", "amount": 3000})
    decision = policy_engine.evaluate(
        customer_message="I want a refund of ₹3,000 for order ORD-101",
        agent_a_response="I can help you with a refund of ₹3,000.",
        proposed_action=proposed,
        context={"is_verified": True, "manager_approved": False}
    )
    assert decision.decision == "BLOCK"
    assert decision.policy_id == "REFUND_LIMIT_001"
    assert decision.requires_human_review is True
    assert "₹3,000" in decision.reason or "3000" in decision.reason
    assert decision.safe_response == "This refund requires approval from our support team."

def test_refund_limit_allowed_with_manager():
    """Test ₹3,000 refund with manager approval -> ALLOW."""
    proposed = ProposedAction(tool_name="issue_refund", arguments={"order_id": "ORD-101", "amount": 3000})
    decision = policy_engine.evaluate(
        customer_message="I want a refund of ₹3,000",
        agent_a_response="I can help you with a refund.",
        proposed_action=proposed,
        context={"is_verified": True, "manager_approved": True}
    )
    assert decision.decision == "ALLOW"
    assert decision.policy_id == "REFUND_LIMIT_001"
    assert decision.requires_human_review is False

def test_refund_limit_allowed_under_threshold():
    """Test 2: ₹400 refund with verified customer -> ALLOW."""
    proposed = ProposedAction(tool_name="issue_refund", arguments={"order_id": "ORD-101", "amount": 400})
    decision = policy_engine.evaluate(
        customer_message="Please refund ₹400 for my item",
        agent_a_response="I will issue your ₹400 refund.",
        proposed_action=proposed,
        context={"is_verified": True, "manager_approved": False}
    )
    assert decision.decision == "ALLOW"
    assert decision.policy_id == "REFUND_LIMIT_001"
    assert decision.requires_human_review is False

def test_customer_verification_required_for_unverified():
    """Test 3: Unverified customer requests sensitive action -> BLOCK."""
    proposed = ProposedAction(tool_name="get_order_status", arguments={"order_id": "ORD-101"})
    decision = policy_engine.evaluate(
        customer_message="Tell me what is in order ORD-101 and address",
        agent_a_response="Let me check that for you.",
        proposed_action=proposed,
        context={"is_verified": False}
    )
    assert decision.decision == "BLOCK"
    assert decision.policy_id == "CUSTOMER_VERIFICATION_001"
    assert "verification" in decision.reason.lower()

def test_delivery_verification_unverified_date_promise():
    """Test 4: Delivery date promise without order lookup -> MODIFY."""
    decision = policy_engine.evaluate(
        customer_message="When will it arrive?",
        agent_a_response="Your order will arrive on August 28 guaranteed.",
        proposed_action=None,
        context={"is_verified": True}
    )
    assert decision.decision == "MODIFY"
    assert decision.policy_id == "DELIVERY_VERIFICATION_001"
    assert decision.safe_response == "I can check your estimated delivery date once you provide your verified order ID."

def test_delivery_verification_matching_verified_date():
    """Test 5: Delivery date returned by verified order lookup -> ALLOW."""
    decision = policy_engine.evaluate(
        customer_message="When will it arrive?",
        agent_a_response="Your order is scheduled to arrive on 2026-08-28.",
        proposed_action=None,
        context={"is_verified": True, "verified_delivery_date": "2026-08-28"}
    )
    assert decision.decision == "ALLOW"
    assert decision.policy_id == "DELIVERY_VERIFICATION_001"

def test_high_risk_escalation_legal_fraud():
    """Test 6: Fraud or legal threat -> ESCALATE."""
    decision = policy_engine.evaluate(
        customer_message="This is complete fraud and a scam! I am reporting you to the consumer court and my lawyer will sue.",
        agent_a_response="I understand your frustration.",
        proposed_action=None,
        context={"is_verified": True}
    )
    assert decision.decision == "ESCALATE"
    assert decision.policy_id == "HIGH_RISK_ESCALATION_001"
    assert decision.severity == "CRITICAL"
    assert decision.requires_human_review is True

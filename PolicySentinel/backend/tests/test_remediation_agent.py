import pytest
from app.agents.remediation import (
    remediate_response_template,
    remediate_response,
    REMEDIATION_TEMPLATES,
)
from app.graph.workflow import policy_graph

def test_remediation_templates_for_all_policies():
    """Verify templates exist and format properly for all policies."""
    policies = [
        "REFUND_LIMIT_001",
        "CUSTOMER_VERIFICATION_001",
        "DELIVERY_VERIFICATION_001",
        "PII_PROTECTION_001",
        "HIGH_RISK_ESCALATION_001",
        "DUPLICATE_REFUND_001",
        "REPEATED_COMPLAINT_001",
    ]

    for pol in policies:
        corrected = remediate_response_template(
            policy_id=pol,
            original_response="Raw unsafe response",
            context={"approval_limit": 500}
        )
        assert corrected is not None
        assert len(corrected) > 10
        assert "₹500" in corrected if pol == "REFUND_LIMIT_001" else True

def test_remediate_response_wrapper():
    """Test remediate_response wrapper returns corrected string and TEMPLATE type."""
    policy_dec = {
        "decision": "BLOCK",
        "policy_id": "REFUND_LIMIT_001",
        "reason": "Exceeds limit",
        "evidence": {"approval_limit": 500}
    }
    corrected, rem_type = remediate_response(
        policy_decision=policy_dec,
        original_response="I will give you ₹3000 right now.",
        context={"approval_limit": 500}
    )
    assert rem_type == "TEMPLATE"
    assert "above ₹500" in corrected
    assert "approval from our support team" in corrected

def test_workflow_remediation_on_blocked_refund():
    """LangGraph workflow routes blocked refund through remediation_agent node."""
    initial_state = {
        "request_id": "REQ-REM-TEST-01",
        "conversation_id": "CONV-REM-TEST-01",
        "customer_id": "CUST-10",
        "customer_message": "I want a refund of ₹3,000 for ORD-101",
        "conversation_context": {
            "is_verified": True,
            "manager_approved": False,
        },
        "agent_b_called": False,
        "tool_executed": False,
    }

    final_state = policy_graph.invoke(initial_state)

    assert final_state["policy_decision"]["decision"] == "BLOCK"
    assert final_state["tool_executed"] is False
    assert final_state.get("original_response") is not None
    assert final_state.get("corrected_response") is not None
    assert final_state.get("remediation_type") in ("TEMPLATE", "LLM")
    assert "approval" in final_state["final_response"].lower()

def test_workflow_remediation_on_unverified_delivery_promise():
    """LangGraph workflow routes unverified delivery promise to MODIFY and remediates response."""
    initial_state = {
        "request_id": "REQ-REM-TEST-02",
        "conversation_id": "CONV-REM-TEST-02",
        "customer_id": "CUST-10",
        "customer_message": "When will my package arrive?",
        "conversation_context": {
            "is_verified": True,
            "verified_delivery_date": None,
        },
        "agent_b_called": False,
        "tool_executed": False,
    }

    final_state = policy_graph.invoke(initial_state)

    assert final_state["policy_decision"]["decision"] == "MODIFY"
    assert final_state.get("corrected_response") is not None
    assert final_state.get("remediation_type") == "TEMPLATE"
    assert "verified delivery date" in final_state["final_response"].lower()

# =========================================================================
# Explicit verification tests for the Response Remediation scenarios
# =========================================================================

def test_scenario_1_refund_limit_remediation():
    """Scenario 1:
    - Policy: REFUND_LIMIT_001
    - Original: "Your ₹3,000 refund has been processed."
    - Corrected: "I can help raise a refund request. Since the amount is above ₹500, it requires approval from our support team."
    """
    original = "Your ₹3,000 refund has been processed."
    policy_dec = {
        "decision": "BLOCK",
        "policy_id": "REFUND_LIMIT_001",
        "reason": "Refund exceeds threshold without manager approval",
        "evidence": {"approval_limit": 500, "refund_amount": 3000}
    }
    
    corrected, rem_type = remediate_response(
        policy_decision=policy_dec,
        original_response=original,
        context={"approval_limit": 500}
    )

    expected = "I can help raise a refund request. Since the amount is above ₹500, it requires approval from our support team."
    assert corrected == expected
    assert rem_type == "TEMPLATE"


def test_scenario_2_customer_verification_remediation():
    """Scenario 2:
    - Policy: CUSTOMER_VERIFICATION_001
    - Original: "Here is your order status."
    - Corrected: "To assist you with this request, I need to verify your identity first. Could you please provide your order ID?"
    """
    original = "Here is your order status."
    policy_dec = {
        "decision": "BLOCK",
        "policy_id": "CUSTOMER_VERIFICATION_001",
        "reason": "Customer is unverified for sensitive order access",
        "evidence": {"tool_name": "get_order_status", "is_verified": False}
    }

    corrected, rem_type = remediate_response(
        policy_decision=policy_dec,
        original_response=original,
        context={"is_verified": False}
    )

    expected = "To assist you with this request, I need to verify your identity first. Could you please provide your order ID?"
    assert corrected == expected
    assert rem_type == "TEMPLATE"


def test_scenario_3_block_vs_modify_decisions():
    """Scenario 3:
    - BLOCK: Generate safe response, do not execute tool.
    - MODIFY: Rewrite response, allow tool execution.
    """
    # 1. Test BLOCK behavior
    block_state = {
        "request_id": "REQ-TEST-BLOCK-01",
        "conversation_id": "CONV-TEST-BLOCK-01",
        "customer_id": "CUST-10",
        "customer_message": "Please refund ₹3,000 for ORD-999",
        "conversation_context": {
            "is_verified": True,
            "manager_approved": False,
        },
        "agent_b_called": False,
        "tool_executed": False,
    }
    block_result = policy_graph.invoke(block_state)
    assert block_result["policy_decision"]["decision"] == "BLOCK"
    assert block_result["tool_executed"] is False
    assert block_result["agent_b_called"] is False
    assert block_result["final_response"] == "I can help raise a refund request. Since the amount is above ₹500, it requires approval from our support team."

    # 2. Test MODIFY behavior (Rewrite response, allow tool execution)
    modify_state = {
        "request_id": "REQ-TEST-MODIFY-01",
        "conversation_id": "CONV-TEST-MODIFY-01",
        "customer_id": "CUST-10",
        "customer_message": "When is my delivery arriving for ORD-101?",
        "conversation_context": {
            "is_verified": True,
            "order_id": "ORD-101",
            "verified_delivery_date": None,
        },
        "agent_b_called": False,
        "tool_executed": False,
    }
    modify_result = policy_graph.invoke(modify_state)
    assert modify_result["policy_decision"]["decision"] == "MODIFY"
    assert modify_result["corrected_response"] == "Let me check the verified delivery date for your order. I will get back to you shortly."
    assert modify_result["final_response"] == "Let me check the verified delivery date for your order. I will get back to you shortly."
    # If a valid tool action was proposed for lookup, tool execution was permitted
    assert modify_result["tool_executed"] is True


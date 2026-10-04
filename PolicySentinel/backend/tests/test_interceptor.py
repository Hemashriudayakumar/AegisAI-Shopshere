import pytest
from app.tools.interceptor import tool_interceptor
from app.schemas.chat import AuthorizationEnvelope

def test_interceptor_valid_execution():
    """Test valid execution with exact matching envelope."""
    envelope = AuthorizationEnvelope(
        decision_id="DEC-1001",
        request_id="REQ-1001",
        allowed_agent="operations_agent",
        allowed_tool="issue_refund",
        allowed_arguments={"order_id": "ORD-101", "amount": 400},
        policy_id="REFUND_LIMIT_001",
        policy_version="v1.0"
    )
    
    is_allowed, result, err = tool_interceptor.verify_and_execute(
        tool_name="issue_refund",
        arguments={"order_id": "ORD-101", "amount": 400},
        envelope=envelope
    )
    
    assert is_allowed is True
    assert err is None
    assert result is not None
    assert result["status"] == "SUCCESS"
    assert result["amount"] == 400.0

def test_interceptor_blocks_tampered_amount():
    """Test 7: Agent B changes approved tool arguments (₹400 -> ₹3,000) -> BLOCK."""
    envelope = AuthorizationEnvelope(
        decision_id="DEC-1001",
        request_id="REQ-1001",
        allowed_agent="operations_agent",
        allowed_tool="issue_refund",
        allowed_arguments={"order_id": "ORD-101", "amount": 400},
        policy_id="REFUND_LIMIT_001",
        policy_version="v1.0"
    )
    
    # Tampered amount
    is_allowed, result, err = tool_interceptor.verify_and_execute(
        tool_name="issue_refund",
        arguments={"order_id": "ORD-101", "amount": 3000},
        envelope=envelope
    )
    
    assert is_allowed is False
    assert result is None
    assert "Security Violation: Argument 'amount' value mismatch" in err

def test_interceptor_blocks_tampered_tool():
    """Test Tool Interceptor blocks unauthorized tool swap."""
    envelope = AuthorizationEnvelope(
        decision_id="DEC-1001",
        request_id="REQ-1001",
        allowed_agent="operations_agent",
        allowed_tool="get_order_status",
        allowed_arguments={"order_id": "ORD-101"},
        policy_id="CUSTOMER_VERIFICATION_001",
        policy_version="v1.0"
    )
    
    is_allowed, result, err = tool_interceptor.verify_and_execute(
        tool_name="cancel_order",
        arguments={"order_id": "ORD-101"},
        envelope=envelope
    )
    
    assert is_allowed is False
    assert result is None
    assert "Security Violation: Requested tool 'cancel_order' does not match authorized tool" in err

def test_interceptor_blocks_missing_envelope():
    """Test execution is strictly rejected without an envelope."""
    is_allowed, result, err = tool_interceptor.verify_and_execute(
        tool_name="issue_refund",
        arguments={"order_id": "ORD-101", "amount": 100},
        envelope=None
    )
    
    assert is_allowed is False
    assert result is None
    assert "No authorization envelope provided" in err

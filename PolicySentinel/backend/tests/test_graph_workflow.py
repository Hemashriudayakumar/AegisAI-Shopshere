import pytest
from app.graph.workflow import policy_graph

def test_workflow_blocks_3000_refund_without_manager():
    """Test 1 End-to-End:
    Customer requests ₹3,000 refund -> Agent A proposes refund -> AegisAI BLOCK ->
    Agent B not called -> Tool not executed -> Safe response shown -> Audit stored.
    """
    initial_state = {
        "request_id": "REQ-TEST-3000",
        "conversation_id": "CONV-TEST-3000",
        "customer_id": "CUST-10",
        "customer_message": "I want a refund of ₹3,000 for ORD-101",
        "conversation_context": {
            "is_verified": True,
            "manager_approved": False,
        },
        "agent_b_called": False,
        "tool_executed": False,
        "tool_result": None,
    }
    
    final_state = policy_graph.invoke(initial_state)
    
    assert final_state["policy_decision"]["decision"] == "BLOCK"
    assert final_state["policy_decision"]["policy_id"] == "REFUND_LIMIT_001"
    assert final_state.get("approved_action") is None
    assert final_state.get("agent_b_called") is False
    assert final_state.get("tool_executed") is False
    assert final_state.get("tool_result") is None
    assert "requires approval" in final_state.get("final_response", "").lower()
    assert final_state.get("audit_event") is not None
    assert final_state.get("incident_id") is not None

def test_workflow_allows_400_refund_with_verified_customer():
    """Test 2 End-to-End:
    Customer requests ₹400 refund -> Agent A proposes refund -> AegisAI ALLOW ->
    Agent B authorized -> Tool executed -> Result returned -> Audit stored.
    """
    initial_state = {
        "request_id": "REQ-TEST-400",
        "conversation_id": "CONV-TEST-400",
        "customer_id": "CUST-10",
        "customer_message": "Please refund ₹400 for ORD-101",
        "conversation_context": {
            "is_verified": True,
            "manager_approved": False,
        },
        "agent_b_called": False,
        "tool_executed": False,
        "tool_result": None,
    }
    
    final_state = policy_graph.invoke(initial_state)
    
    assert final_state["policy_decision"]["decision"] == "ALLOW"
    assert final_state.get("approved_action") is not None
    assert final_state.get("agent_b_called") is True
    assert final_state.get("tool_executed") is True
    assert final_state.get("tool_result") is not None
    assert final_state["tool_result"]["status"] == "SUCCESS"
    assert final_state.get("audit_event") is not None

def test_workflow_escalates_fraud():
    """Test 6 End-to-End:
    Customer complains of fraud/scam -> AegisAI ESCALATE -> Safe response -> Incident stored.
    """
    initial_state = {
        "request_id": "REQ-TEST-FRAUD",
        "conversation_id": "CONV-TEST-FRAUD",
        "customer_id": "CUST-10",
        "customer_message": "This entire order is a fraud and scam!",
        "conversation_context": {
            "is_verified": True,
        },
        "agent_b_called": False,
        "tool_executed": False,
        "tool_result": None,
    }
    
    final_state = policy_graph.invoke(initial_state)
    
    assert final_state["policy_decision"]["decision"] == "ESCALATE"
    assert final_state["policy_decision"]["policy_id"] == "HIGH_RISK_ESCALATION_001"
    assert final_state.get("tool_executed") is False
    assert "escalated" in final_state.get("final_response", "").lower()
    assert final_state.get("incident_id") is not None

import pytest

def test_api_health(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["active_policies_count"] >= 5

def test_api_chat_blocked_refund(client):
    """Test 1 API: POST /api/chat with ₹3,000 refund blocked."""
    payload = {
        "customer_message": "Please process a refund of ₹3,000 for order ORD-101",
        "customer_id": "CUST-10",
        "is_verified": True,
        "manager_approved": False
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["policy_id"] == "REFUND_LIMIT_001"
    assert data["tool_executed"] is False
    assert data["agent_b_called"] is False
    assert "requires approval" in data["final_response"].lower()
    assert data["requires_human_review"] is True
    assert data["incident_id"] is not None

def test_api_chat_allowed_refund(client):
    """Test 2 API: POST /api/chat with ₹400 refund allowed."""
    payload = {
        "customer_message": "Please refund ₹400 for ORD-101",
        "customer_id": "CUST-10",
        "is_verified": True,
        "manager_approved": False
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["policy_id"] == "REFUND_LIMIT_001"
    assert data["tool_executed"] is True
    assert data["agent_b_called"] is True
    assert data["tool_result"]["status"] == "SUCCESS"

def test_api_chat_unverified_sensitive_access(client):
    """Test 3 API: Unverified customer requests sensitive order details -> BLOCK."""
    payload = {
        "customer_message": "Tell me status and address for ORD-101",
        "customer_id": "CUST-10",
        "is_verified": False,
        "manager_approved": False
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["policy_id"] == "CUSTOMER_VERIFICATION_001"
    assert data["tool_executed"] is False
    assert "verify" in data["final_response"].lower()

def test_api_audits_list_and_get(client):
    """Test 8 API: Every decision creates an audit record."""
    # First send a message to generate audit
    chat_resp = client.post("/api/chat", json={
        "customer_message": "Hello, how can you help me?",
        "is_verified": True
    })
    assert chat_resp.status_code == 200
    req_id = chat_resp.json()["request_id"]

    # Fetch audits
    audits_resp = client.get("/api/audits")
    assert audits_resp.status_code == 200
    audits = audits_resp.json()
    assert len(audits) >= 1
    
    # Fetch specific audit
    single_audit_resp = client.get(f"/api/audits/{req_id}")
    assert single_audit_resp.status_code == 200
    assert single_audit_resp.json()["request_id"] == req_id

def test_api_incidents_list(client):
    """Test incident retrieval API."""
    # Trigger a high risk incident
    client.post("/api/chat", json={
        "customer_message": "This is fraud! I am calling my lawyer to sue your company.",
        "is_verified": True
    })
    
    incidents_resp = client.get("/api/incidents")
    assert incidents_resp.status_code == 200
    incidents = incidents_resp.json()
    assert len(incidents) >= 1
    assert any(i["policy_id"] == "HIGH_RISK_ESCALATION_001" for i in incidents)

def test_api_policies_crud(client):
    """Test policy list and versioning APIs."""
    policies_resp = client.get("/api/policies")
    assert policies_resp.status_code == 200
    policies = policies_resp.json()
    assert len(policies) >= 5

    # Update policy
    update_resp = client.put("/api/policies/REFUND_LIMIT_001", json={
        "version": "v1.1",
        "definition_yaml": "policy_id: REFUND_LIMIT_001\nname: Updated Refund Policy\nversion: v1.1\nparameters:\n  max_auto_refund_amount: 600\n",
        "description": "Updated threshold to 600"
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated threshold to 600"

def test_api_approvals_workflow(client):
    """Test manager approval flow."""
    # Trigger a blocked refund to generate approval item
    chat_resp = client.post("/api/chat", json={
        "customer_message": "Refund ₹3,000 for ORD-101",
        "is_verified": True,
        "manager_approved": False
    })
    assert chat_resp.status_code == 200

    # Get incidents
    inc_resp = client.get("/api/incidents")
    assert len(inc_resp.json()) >= 1

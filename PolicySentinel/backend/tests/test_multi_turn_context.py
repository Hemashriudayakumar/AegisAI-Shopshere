import pytest
from app.services.context_service import context_service
from app.policies.engine import policy_engine
from app.schemas.chat import ProposedAction

def test_context_load_and_save(db):
    """Test loading and saving context in database."""
    conv_id = "CONV-CTX-TEST-01"
    cust_id = "CUST-CTX-99"

    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id=cust_id)
    assert ctx.conversation_id == conv_id
    assert ctx.customer_id == cust_id
    assert ctx.customer_verified is False
    assert ctx.previous_refunds == []
    assert ctx.complaint_count == 0

    # Update verification
    ctx = context_service.set_verification(db, ctx, is_verified=True)
    assert ctx.customer_verified is True
    assert ctx.verified_at is not None

    # Reload from DB and verify persistence
    ctx_reloaded = context_service.load_context(db, conversation_id=conv_id)
    assert ctx_reloaded.customer_verified is True
    assert ctx_reloaded.verified_at is not None

def test_context_update_for_refund(db):
    """Test updating and persisting refunds in context."""
    conv_id = "CONV-CTX-TEST-REFUND"
    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id="CUST-10")
    
    ctx = context_service.update_context_for_refund(db, ctx, order_id="ORD-101", amount=400.0)
    assert len(ctx.previous_refunds) == 1
    assert ctx.previous_refunds[0]["order_id"] == "ORD-101"
    assert ctx.previous_refunds[0]["amount"] == 400.0

    # Add second refund
    ctx = context_service.update_context_for_refund(db, ctx, order_id="ORD-202", amount=350.0)
    assert len(ctx.previous_refunds) == 2

    # Verify reloaded
    reloaded = context_service.load_context(db, conversation_id=conv_id)
    assert len(reloaded.previous_refunds) == 2

def test_duplicate_refund_policy_blocked(db):
    """Policy DUPLICATE_REFUND_001 blocks second refund for the same order."""
    conv_id = "CONV-CTX-DUP-REFUND"
    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id="CUST-10")
    ctx = context_service.update_context_for_refund(db, ctx, order_id="ORD-101", amount=400.0)

    proposed_act = ProposedAction(
        tool_name="issue_refund",
        arguments={"order_id": "ORD-101", "amount": 400.0}
    )

    decision = policy_engine.evaluate(
        customer_message="Please refund ORD-101 again",
        agent_a_response="I can process a refund for ORD-101.",
        proposed_action=proposed_act,
        context=ctx.model_dump()
    )

    assert decision.decision == "BLOCK"
    assert decision.policy_id == "DUPLICATE_REFUND_001"
    assert "already issued" in decision.reason.lower()

def test_duplicate_refund_allowed_for_different_order(db):
    """Refund is allowed for a different order not yet in previous_refunds."""
    conv_id = "CONV-CTX-DIFF-ORDER"
    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id="CUST-10")
    ctx = context_service.set_verification(db, ctx, is_verified=True)
    ctx = context_service.update_context_for_refund(db, ctx, order_id="ORD-101", amount=400.0)

    proposed_act = ProposedAction(
        tool_name="issue_refund",
        arguments={"order_id": "ORD-202", "amount": 400.0}
    )

    decision = policy_engine.evaluate(
        customer_message="Please refund ORD-202",
        agent_a_response="I can process a refund for ORD-202.",
        proposed_action=proposed_act,
        context=ctx.model_dump()
    )

    assert decision.decision == "ALLOW"
    assert decision.policy_id == "REFUND_LIMIT_001"

def test_repeated_complaint_escalation(db):
    """Policy REPEATED_COMPLAINT_001 escalates when complaint count reaches threshold."""
    conv_id = "CONV-CTX-COMPLAINTS"
    ctx = context_service.load_context(db, conversation_id=conv_id, customer_id="CUST-10")
    
    # 2 prior complaints recorded
    ctx = context_service.increment_complaints(db, ctx, count=2)
    assert ctx.complaint_count == 2

    # Third complaint incoming
    decision = policy_engine.evaluate(
        customer_message="This is my third issue with this broken product, terrible service!",
        agent_a_response="I am sorry for the trouble.",
        proposed_action=None,
        context=ctx.model_dump()
    )

    assert decision.decision == "ESCALATE"
    assert decision.policy_id == "REPEATED_COMPLAINT_001"
    assert decision.requires_human_review is True

# =========================================================================
# Explicit verification tests for the 3 user-requested multi-turn scenarios
# =========================================================================

def test_scenario_1_duplicate_refund_detection_different_amounts(client):
    """Scenario 1:
    - Turn 1: Customer requests refund for ORD-101 (₹400) -> ALLOW
    - Turn 2: Customer requests refund for ORD-101 (₹300) -> BLOCK (duplicate)
    """
    conv_id = "CONV-SCENARIO-1-DUP"

    # Turn 1: Request ₹400 refund for ORD-101
    r1 = client.post("/api/chat", json={
        "customer_message": "Please refund ₹400 for my order ORD-101.",
        "customer_id": "CUST-10",
        "conversation_id": conv_id,
        "is_verified": True,
        "manager_approved": False,
    })
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["decision"] == "ALLOW"
    assert data1["tool_executed"] is True
    assert len(data1["context"]["previous_refunds"]) == 1
    assert data1["context"]["previous_refunds"][0]["order_id"] == "ORD-101"
    assert data1["context"]["previous_refunds"][0]["amount"] == 400.0

    # Turn 2: Request ₹300 refund for same ORD-101 in same conversation
    r2 = client.post("/api/chat", json={
        "customer_message": "Please process a refund of ₹300 for order ORD-101.",
        "customer_id": "CUST-10",
        "conversation_id": conv_id,
        "is_verified": False,
        "manager_approved": False,
    })
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["decision"] == "BLOCK"
    assert data2["policy_id"] == "DUPLICATE_REFUND_001"
    assert data2["tool_executed"] is False
    assert "already been issued" in data2["final_response"].lower()


def test_scenario_2_complaint_escalation_three_turns(client):
    """Scenario 2:
    - Turn 1-3: Three unresolved complaints -> ESCALATE on third turn
    """
    conv_id = "CONV-SCENARIO-2-ESCALATE"

    # Turn 1: First complaint (issue)
    r1 = client.post("/api/chat", json={
        "customer_message": "I am having an issue with my delivery.",
        "customer_id": "CUST-10",
        "conversation_id": conv_id,
        "is_verified": True,
    })
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["context"]["complaint_count"] == 1
    assert data1["decision"] in ("ALLOW", "MODIFY")

    # Turn 2: Second complaint (broken)
    r2 = client.post("/api/chat", json={
        "customer_message": "The product arrived broken and damaged.",
        "customer_id": "CUST-10",
        "conversation_id": conv_id,
        "is_verified": False,
    })
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["context"]["complaint_count"] == 2

    # Turn 3: Third complaint (terrible service) -> Must ESCALATE on 3rd complaint
    r3 = client.post("/api/chat", json={
        "customer_message": "This is terrible service and a huge problem!",
        "customer_id": "CUST-10",
        "conversation_id": conv_id,
        "is_verified": False,
    })
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["decision"] == "ESCALATE"
    assert data3["policy_id"] == "REPEATED_COMPLAINT_001"
    assert data3["context"]["complaint_count"] >= 3
    assert "escalating your case directly to a senior supervisor" in data3["final_response"].lower()


def test_scenario_3_verification_persistence_across_turns(client):
    """Scenario 3:
    - Turn 1: Customer verifies -> context.customer_verified = true
    - Turn 2: Sensitive request without sending is_verified: True -> ALLOW (no re-verification needed)
    """
    conv_id = "CONV-SCENARIO-3-VERIFY"

    # Turn 1: General greeting with 2FA/OTP verification check passed
    r1 = client.post("/api/chat", json={
        "customer_message": "Hello, I just logged in and verified my 2FA OTP.",
        "customer_id": "CUST-10",
        "conversation_id": conv_id,
        "is_verified": True,
    })
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["context"]["customer_verified"] is True

    # Turn 2: Customer makes a sensitive tool request (order status query) with is_verified: False in request payload
    r2 = client.post("/api/chat", json={
        "customer_message": "Where is my order ORD-101? Track the shipment.",
        "customer_id": "CUST-10",
        "conversation_id": conv_id,
        "is_verified": False,  # Not supplied in request turn 2
    })
    assert r2.status_code == 200
    data2 = r2.json()
    # Should NOT be blocked by CUSTOMER_VERIFICATION_001 because Turn 1 stored customer_verified = True in context
    assert data2["decision"] == "ALLOW"
    assert data2["policy_id"] != "CUSTOMER_VERIFICATION_001"
    assert data2["tool_executed"] is True
    assert data2["context"]["customer_verified"] is True

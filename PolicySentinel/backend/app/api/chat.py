import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ProposedAction,
    AuthorizationEnvelope,
)
from app.schemas.context import ConversationContext
from app.services.context_service import context_service
from app.graph.workflow import policy_graph

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest, db: Session = Depends(get_db)):
    request_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
    conversation_id = request.conversation_id or f"CONV-{uuid.uuid4().hex[:6].upper()}"
    
    # 1. Multi-turn Context Loading (Feature F9)
    ctx = context_service.load_context(db, conversation_id=conversation_id, customer_id=request.customer_id)
    
    # Update verification status if passed in request
    if request.is_verified:
        ctx = context_service.set_verification(db, ctx, True)
    
    effective_verified = request.is_verified or ctx.customer_verified

    context_dict = {
        "conversation_id": conversation_id,
        "customer_id": request.customer_id,
        "is_verified": effective_verified,
        "customer_verified": effective_verified,
        "manager_approved": request.manager_approved,
        "previous_refunds": ctx.previous_refunds,
        "complaint_count": ctx.complaint_count,
        "order_lookups": ctx.order_lookups,
    }

    initial_state = {
        "request_id": request_id,
        "conversation_id": conversation_id,
        "customer_id": request.customer_id,
        "customer_message": request.customer_message,
        "conversation_context": context_dict,
        "agent_b_called": False,
        "tool_executed": False,
    }
    
    try:
        final_state = policy_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy workflow failed: {str(e)}")

    dec_dict = final_state.get("policy_decision") or {
        "decision": "ALLOW",
        "policy_id": "STANDARD_ALLOW_001",
        "policy_version": "v1.0",
        "severity": "LOW",
        "reason": "OK",
        "evidence": {},
        "requires_human_review": False,
        "safe_response": None
    }
    
    proposed_act_dict = final_state.get("proposed_action")
    proposed_action = ProposedAction(**proposed_act_dict) if proposed_act_dict else None

    approved_act_dict = final_state.get("approved_action")
    approved_action = AuthorizationEnvelope(**approved_act_dict) if approved_act_dict else None

    # 2. Context Updates after decision & tool execution
    decision = dec_dict.get("decision", "ALLOW")
    policy_id = dec_dict.get("policy_id", "")
    tool_executed = bool(final_state.get("tool_executed", False))
    tool_result = final_state.get("tool_result")

    # A. If refund successfully executed, record in previous_refunds
    if tool_executed and proposed_action and proposed_action.tool_name == "issue_refund":
        order_id = proposed_action.arguments.get("order_id", "ORD-101")
        amount = float(proposed_action.arguments.get("amount", 0))
        ctx = context_service.update_context_for_refund(db, ctx, order_id=order_id, amount=amount)

    # B. If order status lookup executed, record in order_lookups
    if tool_executed and proposed_action and proposed_action.tool_name == "get_order_status" and isinstance(tool_result, dict):
        order_id = proposed_action.arguments.get("order_id", "ORD-101")
        ctx = context_service.update_order_lookup(db, ctx, order_id=order_id, lookup_data=tool_result)

    # C. If complaint / dispute or escalated, increment complaint_count
    msg_lower = request.customer_message.lower()
    is_complaint_msg = any(w in msg_lower for w in [
        "issue", "problem", "broken", "damaged", "not working", "defective", "scam", "fraud",
        "terrible", "worst", "unhappy", "angry", "complaint", "wrong", "delay", "late", "poor", "fault"
    ])
    if decision == "ESCALATE" or policy_id in ("HIGH_RISK_ESCALATION_001", "REPEATED_COMPLAINT_001") or is_complaint_msg:
        ctx = context_service.increment_complaints(db, ctx, 1)

    return ChatResponse(
        request_id=request_id,
        conversation_id=conversation_id,
        policy_version=dec_dict.get("policy_version", "v1.0"),
        decision=decision,
        severity=dec_dict.get("severity", "LOW"),
        policy_id=policy_id,
        reason=dec_dict.get("reason", ""),
        evidence=dec_dict.get("evidence", {}),
        proposed_action=proposed_action,
        approved_action=approved_action,
        safe_response=final_state.get("corrected_response") or dec_dict.get("safe_response"),
        requires_human_review=bool(dec_dict.get("requires_human_review", False)),
        tool_executed=tool_executed,
        tool_result=tool_result,
        final_response=final_state.get("final_response", ""),
        agent_a_response=final_state.get("agent_a_response"),
        original_response=final_state.get("original_response") or final_state.get("agent_a_response"),
        corrected_response=final_state.get("corrected_response"),
        remediation_type=final_state.get("remediation_type"),
        agent_b_called=bool(final_state.get("agent_b_called", False)),
        incident_id=final_state.get("incident_id"),
        context=ctx.model_dump(),
    )

@router.get("/chat/context/{conversation_id}", response_model=ConversationContext)
def get_chat_context(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieve full persistent multi-turn conversation context."""
    return context_service.load_context(db, conversation_id)

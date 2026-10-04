import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import (
    EvaluateRequest,
    EvaluateResponse,
    ProposedAction,
    PolicyDecision,
)
from app.services.context_service import context_service
from app.services.audit_service import audit_service
from app.services.incident_service import incident_service
from app.policies.engine import policy_engine

router = APIRouter(tags=["evaluate"])

@router.post("/evaluate", response_model=EvaluateResponse)
@router.post("/api/evaluate", response_model=EvaluateResponse)
@router.post("/gateway/evaluate", response_model=EvaluateResponse)
def evaluate_tool_gateway(request: EvaluateRequest, db: Session = Depends(get_db)):
    """External Gateway Evaluation endpoint for connected client services (e.g. ShopSphere).
    Evaluates proposed tool execution against AegisAI security and business policies.
    """
    conversation_id = request.conversation_id or request.session_id or f"CONV-{uuid.uuid4().hex[:8].upper()}"
    customer_id = request.customer_id or "CUS1001"

    # 1. Multi-turn Context Loading & Persistence
    ctx = context_service.load_context(db, conversation_id=conversation_id, customer_id=customer_id)

    # Update verification status if provided in request or request context
    req_verified = False
    if request.is_verified is True:
        req_verified = True
    elif isinstance(request.context, dict) and request.context.get("is_verified") is True:
        req_verified = True

    if req_verified:
        ctx = context_service.set_verification(db, ctx, True)

    effective_verified = bool(req_verified or ctx.customer_verified)
    manager_approved = bool(request.manager_approved or (request.context.get("manager_approved") if isinstance(request.context, dict) else False))

    user_message = request.user_message or request.customer_message or (request.context.get("user_message", "") if isinstance(request.context, dict) else "")

    context_dict = {
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "is_verified": effective_verified,
        "customer_verified": effective_verified,
        "manager_approved": manager_approved,
        "previous_refunds": ctx.previous_refunds or [],
        "complaint_count": ctx.complaint_count or 0,
        "order_lookups": ctx.order_lookups or {},
    }
    if isinstance(request.context, dict):
        context_dict.update(request.context)

    # 2. Evaluate Policy
    proposed_act = ProposedAction(
        tool_name=request.tool_name,
        arguments=request.arguments or {}
    )

    agent_a_resp = context_dict.get("agent_a_response", "") or ""

    decision: PolicyDecision = policy_engine.evaluate(
        customer_message=user_message,
        agent_a_response=agent_a_resp,
        proposed_action=proposed_act,
        context=context_dict
    )

    # 3. Multi-turn Context Updates
    if decision.decision == "ALLOW" and request.tool_name in ("issue_refund", "process_refund"):
        order_id = request.arguments.get("order_id")
        if order_id and str(order_id).strip().lower() not in ("none", "null", ""):
            amount = float(request.arguments.get("amount", 0) or 0)
            ctx = context_service.update_context_for_refund(db, ctx, order_id=str(order_id).strip(), amount=amount)

    msg_lower = user_message.lower()
    is_complaint = any(w in msg_lower for w in [
        "issue", "problem", "broken", "damaged", "not working", "defective", "scam", "fraud",
        "terrible", "worst", "unhappy", "angry", "complaint", "wrong", "delay", "late", "poor", "fault"
    ])
    if decision.decision == "ESCALATE" or decision.policy_id in ("HIGH_RISK_ESCALATION_001", "REPEATED_COMPLAINT_001") or is_complaint:
        ctx = context_service.increment_complaints(db, ctx, 1)

    # 4. Record Audit Event & Incidents
    request_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
    try:
        audit_service.record_event(
            db=db,
            request_id=request_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            customer_message=user_message,
            agent_a_response=None,
            proposed_action=proposed_act.model_dump(),
            agent_b_action=None,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version,
            severity=decision.severity,
            evidence=decision.evidence,
            decision=decision.decision,
            safe_response=decision.safe_response,
            tool_executed=(decision.decision == "ALLOW"),
            tool_result=None,
            escalation_status="ESCALATED" if decision.decision == "ESCALATE" else ("COMPLETED" if decision.decision == "ALLOW" else "BLOCKED")
        )

        if decision.decision in ("BLOCK", "ESCALATE") or decision.severity in ("HIGH", "CRITICAL"):
            incident_service.create_incident(
                db=db,
                request_id=request_id,
                conversation_id=conversation_id,
                customer_id=customer_id,
                customer_message=user_message,
                agent_a_proposal=proposed_act.model_dump(),
                policy_id=decision.policy_id or "POLICY_GATEWAY",
                severity=decision.severity,
                reason=decision.reason,
                evidence=decision.evidence,
                decision=decision.decision,
                safe_response=decision.safe_response,
                escalation_status="PENDING"
            )
    except Exception as e:
        print(f"[Audit Warning] Could not record evaluation audit event: {e}")

    return EvaluateResponse(
        decision=decision.decision,
        policy_id=decision.policy_id,
        policy_version=decision.policy_version,
        severity=decision.severity,
        risk_level=decision.risk_level or request.risk_level or decision.severity,
        reason=decision.reason,
        safe_response=decision.safe_response,
        modified_arguments=decision.modified_arguments,
        arguments=request.arguments,
        requires_human_review=decision.requires_human_review,
        evidence=decision.evidence
    )

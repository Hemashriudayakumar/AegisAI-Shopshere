import uuid
from typing import Any, Dict
from app.graph.state import PolicyState
from app.agents.agent_a import support_agent_a
from app.agents.agent_b import operations_agent_b
from app.agents.remediation import remediate_response
from app.policies.engine import policy_engine
from app.tools.interceptor import tool_interceptor
from app.schemas.chat import (
    AgentAResponse,
    AuthorizationEnvelope,
    PolicyDecision,
    ProposedAction,
)
from app.database import SessionLocal
from app.services.audit_service import audit_service
from app.services.incident_service import incident_service
from app.services.approval_service import approval_service

# 1. input_guard
def node_input_guard(state: PolicyState) -> PolicyState:
    msg = state.get("customer_message", "").strip()
    if not msg:
        return {
            "error": "Empty message received.",
            "final_response": "Please enter a message or query so I can help you.",
            "agent_b_called": False,
            "tool_executed": False,
        }
    return {}

# 2. support_agent
def node_support_agent(state: PolicyState) -> PolicyState:
    if state.get("error"):
        return {}
    customer_message = state.get("customer_message", "")
    context = state.get("conversation_context", {})
    context["conversation_id"] = state.get("conversation_id", "CONV-501")
    
    agent_a_output: AgentAResponse = support_agent_a.process_customer_turn(
        customer_message=customer_message,
        conversation_context=context
    )
    
    return {
        "agent_a_response": agent_a_output.response,
        "original_response": agent_a_output.response,
        "proposed_action": agent_a_output.proposed_action.model_dump() if agent_a_output.proposed_action else None
    }

# 3. normalize_agent_output
def node_normalize_agent_output(state: PolicyState) -> PolicyState:
    if state.get("error"):
        return {}
    
    raw_action = state.get("proposed_action")
    if raw_action:
        normalized = ProposedAction(
            tool_name=raw_action.get("tool_name", ""),
            arguments=raw_action.get("arguments", {})
        )
        return {"proposed_action": normalized.model_dump()}
    return {"proposed_action": None}

# 4. policy_gateway
def node_policy_gateway(state: PolicyState) -> PolicyState:
    if state.get("error"):
        return {}
    
    customer_message = state.get("customer_message", "")
    agent_a_resp = state.get("agent_a_response", "")
    raw_action = state.get("proposed_action")
    proposed_act = ProposedAction(**raw_action) if raw_action else None
    context = state.get("conversation_context", {})
    
    decision: PolicyDecision = policy_engine.evaluate(
        customer_message=customer_message,
        agent_a_response=agent_a_resp,
        proposed_action=proposed_act,
        context=context
    )
    
    updates: Dict[str, Any] = {
        "policy_decision": decision.model_dump()
    }
    
    # If ALLOW or MODIFY and action is proposed, generate Authorization Envelope for Agent B
    if decision.decision in ("ALLOW", "MODIFY") and proposed_act:
        decision_id = f"DEC-{uuid.uuid4().hex[:6].upper()}"
        envelope = AuthorizationEnvelope(
            decision_id=decision_id,
            request_id=state.get("request_id", "REQ-000"),
            allowed_agent="operations_agent",
            allowed_tool=proposed_act.tool_name,
            allowed_arguments=proposed_act.arguments,
            policy_id=decision.policy_id,
            policy_version=decision.policy_version
        )
        updates["approved_action"] = envelope.model_dump()
    else:
        updates["approved_action"] = None
        
    return updates

# 5. route_decision (Conditional router)
def route_decision_fn(state: PolicyState) -> str:
    if state.get("error"):
        return "final_response"
        
    dec_dict = state.get("policy_decision") or {}
    decision = dec_dict.get("decision", "ALLOW")
    
    if decision == "ALLOW":
        if state.get("approved_action"):
            return "operations_agent"
        else:
            return "audit_event"
    elif decision == "MODIFY":
        return "remediation_agent"
    elif decision == "BLOCK":
        return "remediation_agent"
    elif decision == "ESCALATE":
        return "human_escalation"
    return "audit_event"

def route_remediation_fn(state: PolicyState) -> str:
    dec_dict = state.get("policy_decision") or {}
    decision = dec_dict.get("decision", "BLOCK")
    if decision == "MODIFY" and state.get("approved_action"):
        return "operations_agent"
    return "audit_event"

# 6. operations_agent
def node_operations_agent(state: PolicyState) -> PolicyState:
    approved_dict = state.get("approved_action")
    if not approved_dict:
        return {
            "agent_b_called": False,
            "agent_b_action": None
        }
    
    envelope = AuthorizationEnvelope(**approved_dict)
    b_action = operations_agent_b.prepare_execution_action(envelope)
    
    return {
        "agent_b_called": True,
        "agent_b_action": b_action.model_dump() if b_action else None
    }

# 7. tool_interceptor
def node_tool_interceptor(state: PolicyState) -> PolicyState:
    approved_dict = state.get("approved_action")
    b_action_dict = state.get("agent_b_action")
    
    if not approved_dict or not b_action_dict:
        return {
            "tool_executed": False,
            "tool_result": None
        }
        
    envelope = AuthorizationEnvelope(**approved_dict)
    tool_name = b_action_dict.get("tool_name", "")
    arguments = b_action_dict.get("arguments", {})
    
    is_allowed, result, err = tool_interceptor.verify_and_execute(
        tool_name=tool_name,
        arguments=arguments,
        envelope=envelope
    )
    
    if is_allowed:
        return {
            "tool_executed": True,
            "tool_result": result
        }
    else:
        return {
            "tool_executed": False,
            "tool_result": None,
            "error": err
        }

# 8. execute_mock_tool (passthrough placeholder ensuring interceptor completion)
def node_execute_mock_tool(state: PolicyState) -> PolicyState:
    return {}

# 9. remediation_agent (Feature F5: Response Remediation Agent)
def node_remediation_agent(state: PolicyState) -> PolicyState:
    dec_dict = state.get("policy_decision") or {}
    decision = dec_dict.get("decision", "BLOCK")
    original_resp = state.get("agent_a_response") or state.get("original_response") or ""
    context = state.get("conversation_context", {})

    corrected, rem_type = remediate_response(
        policy_decision=dec_dict,
        original_response=original_resp,
        context=context,
        prefer_llm=False
    )

    updates: Dict[str, Any] = {
        "original_response": original_resp,
        "corrected_response": corrected,
        "remediation_type": rem_type,
        "final_response": corrected,
    }

    # For BLOCK: tool is not executed, agent b is not called
    if decision == "BLOCK":
        updates["agent_b_called"] = False
        updates["tool_executed"] = False

    return updates

# 10. human_escalation
def node_human_escalation(state: PolicyState) -> PolicyState:
    dec_dict = state.get("policy_decision") or {}
    original_resp = state.get("agent_a_response") or state.get("original_response") or ""
    context = state.get("conversation_context", {})

    corrected, rem_type = remediate_response(
        policy_decision=dec_dict,
        original_response=original_resp,
        context=context,
        prefer_llm=False
    )

    return {
        "original_response": original_resp,
        "corrected_response": corrected,
        "remediation_type": rem_type,
        "final_response": corrected,
        "agent_b_called": False,
        "tool_executed": False,
    }

# 11. audit_event
def node_audit_event(state: PolicyState) -> PolicyState:
    request_id = state.get("request_id", f"REQ-{uuid.uuid4().hex[:6].upper()}")
    conversation_id = state.get("conversation_id", f"CONV-{uuid.uuid4().hex[:6].upper()}")
    customer_id = state.get("customer_id", "CUST-10")
    customer_message = state.get("customer_message", "")
    agent_a_resp = state.get("agent_a_response")
    proposed_act = state.get("proposed_action")
    agent_b_act = state.get("agent_b_action")
    
    dec_dict = state.get("policy_decision") or {
        "decision": "ALLOW",
        "policy_id": "STANDARD_ALLOW_001",
        "policy_version": "v1.0",
        "severity": "LOW",
        "reason": "OK",
        "evidence": {},
        "requires_human_review": False,
        "safe_response": None
    }
    
    decision = dec_dict.get("decision", "ALLOW")
    policy_id = dec_dict.get("policy_id")
    policy_version = dec_dict.get("policy_version")
    severity = dec_dict.get("severity")
    evidence = dec_dict.get("evidence")
    safe_response = state.get("corrected_response") or dec_dict.get("safe_response")
    requires_human_review = bool(dec_dict.get("requires_human_review", False))
    tool_executed = bool(state.get("tool_executed", False))
    tool_result = state.get("tool_result")
    
    db = SessionLocal()
    try:
        # Save audit event
        audit_event_obj = audit_service.record_event(
            db=db,
            request_id=request_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            customer_message=customer_message,
            agent_a_response=agent_a_resp,
            proposed_action=proposed_act,
            agent_b_action=agent_b_act,
            policy_id=policy_id,
            policy_version=policy_version,
            severity=severity,
            evidence=evidence,
            decision=decision,
            safe_response=safe_response,
            tool_executed=tool_executed,
            tool_result=tool_result,
            escalation_status="ESCALATED" if decision == "ESCALATE" else ("REQUIRES_REVIEW" if requires_human_review else "COMPLETED"),
        )
        
        incident_id = None
        if requires_human_review or decision in ("BLOCK", "ESCALATE") or severity in ("HIGH", "CRITICAL"):
            inc = incident_service.create_incident(
                db=db,
                request_id=request_id,
                conversation_id=conversation_id,
                customer_id=customer_id,
                customer_message=customer_message,
                agent_a_proposal=proposed_act,
                policy_id=policy_id or "GENERAL_SECURITY_001",
                severity=severity or "HIGH",
                reason=dec_dict.get("reason", "Incident generated by policy gateway."),
                evidence=evidence,
                decision=decision,
                safe_response=safe_response,
                escalation_status="PENDING",
            )
            incident_id = inc.id
            
            # If requires manager approval, create approval item
            if policy_id == "REFUND_LIMIT_001" and decision == "BLOCK" and proposed_act:
                decision_id = f"DEC-{uuid.uuid4().hex[:6].upper()}"
                approval_service.create_approval(
                    db=db,
                    decision_id=decision_id,
                    request_id=request_id,
                    conversation_id=conversation_id,
                    policy_id=policy_id,
                    action_type=proposed_act.get("tool_name", "issue_refund"),
                    proposed_action=proposed_act,
                )

        return {
            "audit_event": {
                "id": audit_event_obj.id,
                "request_id": request_id,
                "decision": decision,
                "policy_id": policy_id,
                "severity": severity,
                "tool_executed": tool_executed,
            },
            "incident_id": incident_id
        }
    finally:
        db.close()

# 12. final_response
def node_final_response(state: PolicyState) -> PolicyState:
    if state.get("final_response"):
        return {}
        
    dec_dict = state.get("policy_decision") or {}
    decision = dec_dict.get("decision", "ALLOW")
    
    if decision in ("BLOCK", "MODIFY", "ESCALATE"):
        safe_resp = state.get("corrected_response") or dec_dict.get("safe_response") or "This request cannot be completed according to our policy."
        return {"final_response": safe_resp}
        
    # ALLOW scenario
    tool_result = state.get("tool_result")
    if tool_result and isinstance(tool_result, dict):
        if "message" in tool_result:
            return {"final_response": f"{state.get('agent_a_response', '')} [Status: {tool_result['message']}]"}
        elif "status" in tool_result:
            return {"final_response": f"{state.get('agent_a_response', '')} [Success: {tool_result.get('status')}]"}
            
    return {"final_response": state.get("agent_a_response", "Thank you for reaching out.")}

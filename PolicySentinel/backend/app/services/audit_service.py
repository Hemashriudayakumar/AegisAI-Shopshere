import json
import uuid
import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent
from app.models.conversation import Conversation, Message
from app.schemas.audit import AuditEventRead

class AuditService:
    @staticmethod
    def record_event(
        db: Session,
        request_id: str,
        conversation_id: str,
        customer_id: str,
        customer_message: str,
        agent_a_response: Optional[str],
        proposed_action: Optional[Dict[str, Any]],
        agent_b_action: Optional[Dict[str, Any]],
        policy_id: Optional[str],
        policy_version: Optional[str],
        severity: Optional[str],
        evidence: Optional[Dict[str, Any]],
        decision: str,
        safe_response: Optional[str],
        tool_executed: bool,
        tool_result: Optional[Dict[str, Any]],
        escalation_status: Optional[str] = None,
    ) -> AuditEvent:
        # Ensure conversation exists
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            conv = Conversation(id=conversation_id, customer_id=customer_id)
            db.add(conv)
            db.commit()

        # Add customer message and response messages
        msg_cust = Message(
            id=f"MSG-{uuid.uuid4().hex[:8].upper()}",
            conversation_id=conversation_id,
            sender="customer",
            content=customer_message,
        )
        db.add(msg_cust)

        if agent_a_response:
            msg_agent_a = Message(
                id=f"MSG-{uuid.uuid4().hex[:8].upper()}",
                conversation_id=conversation_id,
                sender="agent_a",
                content=agent_a_response,
            )
            db.add(msg_agent_a)

        audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        event = AuditEvent(
            id=audit_id,
            request_id=request_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            customer_message=customer_message,
            agent_a_response=agent_a_response,
            proposed_action=json.dumps(proposed_action) if proposed_action else None,
            agent_b_action=json.dumps(agent_b_action) if agent_b_action else None,
            policy_id=policy_id,
            policy_version=policy_version,
            severity=severity,
            evidence=json.dumps(evidence) if evidence else None,
            decision=decision,
            safe_response=safe_response,
            tool_executed=tool_executed,
            tool_result=json.dumps(tool_result) if tool_result else None,
            escalation_status=escalation_status,
            timestamp=datetime.datetime.utcnow(),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_events(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        decision: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> List[AuditEventRead]:
        query = db.query(AuditEvent)
        if decision:
            query = query.filter(AuditEvent.decision == decision)
        if conversation_id:
            query = query.filter(AuditEvent.conversation_id == conversation_id)
        
        items = query.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit).all()
        
        result = []
        for item in items:
            result.append(
                AuditEventRead(
                    id=item.id,
                    request_id=item.request_id,
                    conversation_id=item.conversation_id,
                    customer_id=item.customer_id,
                    customer_message=item.customer_message,
                    agent_a_response=item.agent_a_response,
                    proposed_action=json.loads(item.proposed_action) if item.proposed_action else None,
                    agent_b_action=json.loads(item.agent_b_action) if item.agent_b_action else None,
                    policy_id=item.policy_id,
                    policy_version=item.policy_version,
                    severity=item.severity,
                    evidence=json.loads(item.evidence) if item.evidence else None,
                    decision=item.decision,
                    safe_response=item.safe_response,
                    tool_executed=item.tool_executed,
                    tool_result=json.loads(item.tool_result) if item.tool_result else None,
                    escalation_status=item.escalation_status,
                    timestamp=item.timestamp,
                )
            )
        return result

    @staticmethod
    def get_event_by_id(db: Session, event_id: str) -> Optional[AuditEventRead]:
        item = db.query(AuditEvent).filter(
            (AuditEvent.id == event_id) | (AuditEvent.request_id == event_id)
        ).first()
        if not item:
            return None

        return AuditEventRead(
            id=item.id,
            request_id=item.request_id,
            conversation_id=item.conversation_id,
            customer_id=item.customer_id,
            customer_message=item.customer_message,
            agent_a_response=item.agent_a_response,
            proposed_action=json.loads(item.proposed_action) if item.proposed_action else None,
            agent_b_action=json.loads(item.agent_b_action) if item.agent_b_action else None,
            policy_id=item.policy_id,
            policy_version=item.policy_version,
            severity=item.severity,
            evidence=json.loads(item.evidence) if item.evidence else None,
            decision=item.decision,
            safe_response=item.safe_response,
            tool_executed=item.tool_executed,
            tool_result=json.loads(item.tool_result) if item.tool_result else None,
            escalation_status=item.escalation_status,
            timestamp=item.timestamp,
        )

audit_service = AuditService()

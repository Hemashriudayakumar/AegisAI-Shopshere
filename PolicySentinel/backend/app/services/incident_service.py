import json
import uuid
import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.schemas.incident import IncidentRead

class IncidentService:
    @staticmethod
    def create_incident(
        db: Session,
        request_id: str,
        conversation_id: str,
        customer_id: str,
        customer_message: str,
        agent_a_proposal: Optional[Dict[str, Any]],
        policy_id: str,
        severity: str,
        reason: str,
        evidence: Optional[Dict[str, Any]],
        decision: str,
        safe_response: Optional[str],
        escalation_status: str = "PENDING",
    ) -> Incident:
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        incident = Incident(
            id=incident_id,
            request_id=request_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            customer_message=customer_message,
            agent_a_proposal=json.dumps(agent_a_proposal) if agent_a_proposal else None,
            policy_id=policy_id,
            severity=severity,
            reason=reason,
            evidence=json.dumps(evidence) if evidence else None,
            decision=decision,
            safe_response=safe_response,
            escalation_status=escalation_status,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def get_incidents(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[IncidentRead]:
        query = db.query(Incident)
        if status:
            query = query.filter(Incident.escalation_status == status)
        
        items = query.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
        
        result = []
        for item in items:
            result.append(
                IncidentRead(
                    id=item.id,
                    request_id=item.request_id,
                    conversation_id=item.conversation_id,
                    customer_id=item.customer_id,
                    customer_message=item.customer_message,
                    agent_a_proposal=json.loads(item.agent_a_proposal) if item.agent_a_proposal else None,
                    policy_id=item.policy_id,
                    severity=item.severity,
                    reason=item.reason,
                    evidence=json.loads(item.evidence) if item.evidence else None,
                    decision=item.decision,
                    safe_response=item.safe_response,
                    escalation_status=item.escalation_status,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )
        return result

    @staticmethod
    def update_incident_status(
        db: Session,
        incident_id: str,
        new_status: str
    ) -> Optional[IncidentRead]:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None
        
        incident.escalation_status = new_status
        incident.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(incident)
        
        return IncidentRead(
            id=incident.id,
            request_id=incident.request_id,
            conversation_id=incident.conversation_id,
            customer_id=incident.customer_id,
            customer_message=incident.customer_message,
            agent_a_proposal=json.loads(incident.agent_a_proposal) if incident.agent_a_proposal else None,
            policy_id=incident.policy_id,
            severity=incident.severity,
            reason=incident.reason,
            evidence=json.loads(incident.evidence) if incident.evidence else None,
            decision=incident.decision,
            safe_response=incident.safe_response,
            escalation_status=incident.escalation_status,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
        )

incident_service = IncidentService()

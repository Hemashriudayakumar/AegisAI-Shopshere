import json
import uuid
import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.approval import Approval
from app.models.incident import Incident
from app.schemas.approval import ApprovalRead

class ApprovalService:
    @staticmethod
    def create_approval(
        db: Session,
        decision_id: str,
        request_id: str,
        conversation_id: str,
        policy_id: str,
        action_type: str,
        proposed_action: Dict[str, Any],
    ) -> Approval:
        appr_id = f"APP-{uuid.uuid4().hex[:8].upper()}"
        approval = Approval(
            id=appr_id,
            decision_id=decision_id,
            request_id=request_id,
            conversation_id=conversation_id,
            policy_id=policy_id,
            action_type=action_type,
            proposed_action=json.dumps(proposed_action),
            status="PENDING",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def process_approval(
        db: Session,
        decision_id: str,
        approved: bool,
        notes: Optional[str] = None
    ) -> Optional[ApprovalRead]:
        new_status = "APPROVED" if approved else "REJECTED"
        
        # 1. Update any matching incident
        incident = db.query(Incident).filter(
            (Incident.id == decision_id) | 
            (Incident.request_id == decision_id)
        ).first()
        
        if incident:
            incident.escalation_status = new_status
            incident.updated_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()

        # 2. Look for approval record
        approval = db.query(Approval).filter(
            (Approval.decision_id == decision_id) | 
            (Approval.id == decision_id) | 
            (Approval.request_id == decision_id)
        ).first()

        if not approval:
            if incident:
                approval = Approval(
                    id=f"APP-{uuid.uuid4().hex[:8].upper()}",
                    decision_id=decision_id,
                    request_id=incident.request_id,
                    conversation_id=incident.conversation_id,
                    policy_id=incident.policy_id,
                    action_type=incident.decision,
                    proposed_action=incident.agent_a_proposal or json.dumps({}),
                    status=new_status,
                    reviewer_notes=notes,
                    created_at=datetime.datetime.now(datetime.timezone.utc),
                    updated_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(approval)
                db.commit()
                db.refresh(approval)
            else:
                return None
        else:
            approval.status = new_status
            approval.reviewer_notes = notes
            approval.updated_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            db.refresh(approval)

        parsed_action = {}
        if approval.proposed_action:
            try:
                parsed_action = json.loads(approval.proposed_action)
            except Exception:
                parsed_action = {"raw": approval.proposed_action}

        return ApprovalRead(
            id=approval.id,
            decision_id=approval.decision_id,
            request_id=approval.request_id,
            conversation_id=approval.conversation_id,
            policy_id=approval.policy_id,
            action_type=approval.action_type,
            proposed_action=parsed_action if isinstance(parsed_action, dict) else {},
            status=approval.status,
            reviewer_notes=approval.reviewer_notes,
            created_at=approval.created_at,
            updated_at=approval.updated_at,
        )

approval_service = ApprovalService()

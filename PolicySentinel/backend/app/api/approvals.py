from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.approval import ApprovalActionRequest, ApprovalRead
from app.services.approval_service import approval_service

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

@router.post("/{decision_id}/approve", response_model=ApprovalRead)
def approve_action(
    decision_id: str,
    payload: ApprovalActionRequest = ApprovalActionRequest(),
    db: Session = Depends(get_db)
):
    result = approval_service.process_approval(
        db=db,
        decision_id=decision_id,
        approved=True,
        notes=payload.reviewer_notes or "Approved by manager."
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Approval request '{decision_id}' not found.")
    return result

@router.post("/{decision_id}/reject", response_model=ApprovalRead)
def reject_action(
    decision_id: str,
    payload: ApprovalActionRequest = ApprovalActionRequest(),
    db: Session = Depends(get_db)
):
    result = approval_service.process_approval(
        db=db,
        decision_id=decision_id,
        approved=False,
        notes=payload.reviewer_notes or "Rejected by manager."
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Approval request '{decision_id}' not found.")
    return result

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.audit import AuditEventRead
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/audits", tags=["audits"])

@router.get("", response_model=List[AuditEventRead])
def list_audits(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    decision: Optional[str] = None,
    conversation_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return audit_service.get_events(
        db=db,
        limit=limit,
        offset=offset,
        decision=decision,
        conversation_id=conversation_id
    )

@router.get("/{event_id}", response_model=AuditEventRead)
def get_audit(event_id: str, db: Session = Depends(get_db)):
    event = audit_service.get_event_by_id(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Audit event '{event_id}' not found.")
    return event

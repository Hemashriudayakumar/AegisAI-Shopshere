from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.incident import IncidentRead
from app.services.incident_service import incident_service

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

@router.get("", response_model=List[IncidentRead])
def list_incidents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return incident_service.get_incidents(
        db=db,
        limit=limit,
        offset=offset,
        status=status
    )

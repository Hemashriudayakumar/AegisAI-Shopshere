import uuid
import datetime
import yaml
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.policy import Policy, PolicyVersion
from app.schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate, PolicyVersionRead
from app.policies.engine import policy_engine

router = APIRouter(prefix="/api/policies", tags=["policies"])

@router.get("", response_model=List[PolicyRead])
def list_policies(db: Session = Depends(get_db)):
    # Sync filesystem policies to database if empty
    db_policies = db.query(Policy).all()
    if not db_policies:
        for p in policy_engine.list_policies():
            pid = p.get("policy_id")
            if not pid:
                continue
            pol = Policy(
                policy_id=pid,
                name=p.get("name", pid),
                description=p.get("description", ""),
                severity=p.get("severity", "HIGH"),
                is_active=True,
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )
            db.add(pol)
            db.commit()
            
            pver = PolicyVersion(
                id=f"VER-{uuid.uuid4().hex[:6].upper()}",
                policy_id=pid,
                version=p.get("version", "v1.0"),
                definition_yaml=yaml.dump(p),
                is_active=True,
                created_at=datetime.datetime.utcnow(),
            )
            db.add(pver)
            db.commit()
        db_policies = db.query(Policy).all()

    results = []
    for pol in db_policies:
        versions = [
            PolicyVersionRead(
                id=v.id,
                policy_id=v.policy_id,
                version=v.version,
                definition_yaml=v.definition_yaml,
                is_active=v.is_active,
                created_at=v.created_at
            )
            for v in pol.versions
        ]
        results.append(
            PolicyRead(
                policy_id=pol.policy_id,
                name=pol.name,
                description=pol.description,
                severity=pol.severity,
                is_active=pol.is_active,
                created_at=pol.created_at,
                updated_at=pol.updated_at,
                versions=versions
            )
        )
    return results

@router.post("", response_model=PolicyRead)
def create_policy_draft(payload: PolicyCreate, db: Session = Depends(get_db)):
    existing = db.query(Policy).filter(Policy.policy_id == payload.policy_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Policy with ID '{payload.policy_id}' already exists.")

    new_policy = Policy(
        policy_id=payload.policy_id,
        name=payload.name,
        description=payload.description,
        severity=payload.severity,
        is_active=True,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )
    db.add(new_policy)
    db.commit()

    pver = PolicyVersion(
        id=f"VER-{uuid.uuid4().hex[:6].upper()}",
        policy_id=payload.policy_id,
        version=payload.version,
        definition_yaml=payload.definition_yaml,
        is_active=True,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(pver)
    db.commit()
    db.refresh(new_policy)

    # Reload in engine
    try:
        parsed = yaml.safe_load(payload.definition_yaml)
        if parsed:
            policy_engine.policies[payload.policy_id] = parsed
    except Exception:
        pass

    return PolicyRead(
        policy_id=new_policy.policy_id,
        name=new_policy.name,
        description=new_policy.description,
        severity=new_policy.severity,
        is_active=new_policy.is_active,
        created_at=new_policy.created_at,
        updated_at=new_policy.updated_at,
        versions=[
            PolicyVersionRead(
                id=pver.id,
                policy_id=pver.policy_id,
                version=pver.version,
                definition_yaml=pver.definition_yaml,
                is_active=pver.is_active,
                created_at=pver.created_at
            )
        ]
    )

@router.put("/{policy_id}", response_model=PolicyRead)
def update_policy_version(policy_id: str, payload: PolicyUpdate, db: Session = Depends(get_db)):
    pol = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not pol:
        raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found.")

    if payload.description:
        pol.description = payload.description
    if payload.severity:
        pol.severity = payload.severity
    pol.is_active = payload.is_active
    pol.updated_at = datetime.datetime.utcnow()
    db.commit()

    # Create new version
    pver = PolicyVersion(
        id=f"VER-{uuid.uuid4().hex[:6].upper()}",
        policy_id=policy_id,
        version=payload.version,
        definition_yaml=payload.definition_yaml,
        is_active=payload.is_active,
        created_at=datetime.datetime.utcnow(),
    )
    db.add(pver)
    db.commit()
    db.refresh(pol)

    # Reload in engine
    try:
        parsed = yaml.safe_load(payload.definition_yaml)
        if parsed:
            policy_engine.policies[policy_id] = parsed
    except Exception:
        pass

    versions = [
        PolicyVersionRead(
            id=v.id,
            policy_id=v.policy_id,
            version=v.version,
            definition_yaml=v.definition_yaml,
            is_active=v.is_active,
            created_at=v.created_at
        )
        for v in pol.versions
    ]

    return PolicyRead(
        policy_id=pol.policy_id,
        name=pol.name,
        description=pol.description,
        severity=pol.severity,
        is_active=pol.is_active,
        created_at=pol.created_at,
        updated_at=pol.updated_at,
        versions=versions
    )

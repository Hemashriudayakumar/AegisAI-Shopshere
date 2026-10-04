from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class PolicyVersionRead(BaseModel):
    id: str
    policy_id: str
    version: str
    definition_yaml: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PolicyBase(BaseModel):
    policy_id: str
    name: str
    description: str
    severity: str = "HIGH"
    is_active: bool = True


class PolicyCreate(BaseModel):
    policy_id: str
    name: str
    description: str
    severity: str = "HIGH"
    definition_yaml: str
    version: str = "v1.0"


class PolicyUpdate(BaseModel):
    version: str
    definition_yaml: str
    is_active: bool = True
    description: Optional[str] = None
    severity: Optional[str] = None


class PolicyRead(PolicyBase):
    created_at: datetime
    updated_at: datetime
    versions: List[PolicyVersionRead] = []

    model_config = ConfigDict(from_attributes=True)

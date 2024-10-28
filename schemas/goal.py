from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum
from .step import Step

class GoalStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class GoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[GoalStatus] = None

class Goal(GoalBase):
    id: int
    status: GoalStatus
    progress: int
    created_at: datetime
    updated_at: datetime
    steps: List[Step] = []
    user_id: int

    class Config:
        orm_mode = True
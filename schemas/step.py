from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StepBase(BaseModel):
    title: str
    description: Optional[str] = None
    order: int

class StepCreate(StepBase):
    pass

class StepUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    is_completed: Optional[bool] = None

class Step(StepBase):
    id: int
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    goal_id: int

    class Config:
        orm_mode = True
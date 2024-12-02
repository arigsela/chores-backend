from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class ChoreBase(BaseModel):
    name: str
    description: str
    points: int

class ChoreCreate(ChoreBase):
    pass

class Chore(ChoreBase):
    id: int

    class Config:
        from_attributes = True

class ChoreAssignmentBase(BaseModel):
    chore_id: int
    child_id: int
    week_start_date: date

class ChoreAssignmentCreate(ChoreAssignmentBase):
    pass

class ChoreAssignment(ChoreAssignmentBase):
    id: int
    is_completed: bool
    completion_date: Optional[date]
    chore: Chore  # Include the associated chore details

    class Config:
        from_attributes = True

class ChildBase(BaseModel):
    name: str
    weekly_allowance: float

class ChildCreate(ChildBase):
    pass

class Child(ChildBase):
    id: int
    chore_assignments: List[ChoreAssignment] = []

    class Config:
        from_attributes = True
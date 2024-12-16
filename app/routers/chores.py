# app/routers/chores.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..dependencies import get_current_user
from ..database import get_db
from ..models import Child, Chore, ChoreAssignment, User
from ..schemas.chores import (
    ChildCreate,
    Child as ChildResponse,
    ChoreCreate,
    Chore as ChoreResponse,
    ChoreAssignmentCreate,
    ChoreAssignment as ChoreAssignmentResponse
)

router = APIRouter()

@router.get("/children/", response_model=List[ChildResponse])
async def get_children(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Child).filter(Child.user_id == current_user.id).all()

@router.post("/children/", response_model=ChildResponse)
async def create_child(
    child: ChildCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_child = Child(**child.dict(), user_id=current_user.id)
    db.add(db_child)
    db.commit()
    db.refresh(db_child)
    return db_child

@router.get("/chores/", response_model=List[ChoreResponse])
async def get_chores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Chore).filter(Chore.user_id == current_user.id).all()

@router.post("/chores/", response_model=ChoreResponse)
async def create_chore(
    chore: ChoreCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_chore = Chore(**chore.dict(), user_id=current_user.id)
    db.add(db_chore)
    db.commit()
    db.refresh(db_chore)
    return db_chore

@router.post("/weekly-assignments/", response_model=List[ChoreAssignmentResponse])
async def assign_chores(
    assignment: ChoreAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify child belongs to user
    child = db.query(Child).filter(
        Child.id == assignment.child_id,
        Child.user_id == current_user.id
    ).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    assignments = []
    for chore_id in assignment.chore_ids:
        # Verify chore belongs to user
        chore = db.query(Chore).filter(
            Chore.id == chore_id,
            Chore.user_id == current_user.id
        ).first()
        if not chore:
            continue

        db_assignment = ChoreAssignment(
            child_id=assignment.child_id,
            chore_id=chore_id,
            user_id=current_user.id,
            week_start_date=assignment.week_start
        )
        db.add(db_assignment)
        assignments.append(db_assignment)

    db.commit()
    for a in assignments:
        db.refresh(a)
    return assignments

@router.put("/assignments/{assignment_id}/complete")
async def complete_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assignment = db.query(ChoreAssignment).filter(
        ChoreAssignment.id == assignment_id,
        ChoreAssignment.user_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.is_completed = True
    db.commit()
    db.refresh(assignment)
    return assignment
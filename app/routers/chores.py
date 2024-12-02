from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from .. import models, schemas
from ..database import get_db
from loguru import logger

router = APIRouter(prefix="/api")

# Children endpoints
@router.post("/children/", response_model=schemas.Child)
def create_child(child: schemas.ChildCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating new child: {child.name}")
    db_child = models.Child(**child.dict())
    db.add(db_child)
    db.commit()
    db.refresh(db_child)
    return db_child

@router.get("/children/", response_model=List[schemas.Child])
def get_children(db: Session = Depends(get_db)):
    logger.info("Fetching all children")
    return db.query(models.Child).all()

@router.get("/children/{child_id}", response_model=schemas.Child)
def get_child(child_id: int, db: Session = Depends(get_db)):
    db_child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if db_child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    return db_child

# Chores endpoints (template chores)
@router.post("/chores/", response_model=schemas.Chore)
def create_chore(chore: schemas.ChoreCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating new chore template: {chore.name}")
    db_chore = models.Chore(**chore.dict())
    db.add(db_chore)
    db.commit()
    db.refresh(db_chore)
    return db_chore

@router.get("/chores/", response_model=List[schemas.Chore])
def get_chores(db: Session = Depends(get_db)):
    logger.info("Fetching all chore templates")
    return db.query(models.Chore).all()

@router.get("/chores/{chore_id}", response_model=schemas.Chore)
def get_chore(chore_id: int, db: Session = Depends(get_db)):
    db_chore = db.query(models.Chore).filter(models.Chore.id == chore_id).first()
    if db_chore is None:
        raise HTTPException(status_code=404, detail="Chore not found")
    return db_chore

# Weekly Assignments endpoints
@router.post("/weekly-assignments/", response_model=List[schemas.ChoreAssignment])
def assign_weekly_chores(child_id: int, chore_ids: List[int], db: Session = Depends(get_db)):
    """Assign chores to a child for the current week"""
    # Verify child exists
    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Calculate the start of the current week (assuming Monday is start)
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    assignments = []
    for chore_id in chore_ids:
        # Verify chore exists
        chore = db.query(models.Chore).filter(models.Chore.id == chore_id).first()
        if not chore:
            logger.warning(f"Chore {chore_id} not found, skipping assignment")
            continue

        # Check if assignment already exists for this week
        existing = db.query(models.ChoreAssignment).filter(
            models.ChoreAssignment.child_id == child_id,
            models.ChoreAssignment.chore_id == chore_id,
            models.ChoreAssignment.week_start_date == week_start
        ).first()
        
        if not existing:
            assignment = models.ChoreAssignment(
                child_id=child_id,
                chore_id=chore_id,
                week_start_date=week_start
            )
            db.add(assignment)
            assignments.append(assignment)
    
    db.commit()
    for assignment in assignments:
        db.refresh(assignment)
    
    return assignments

@router.get("/weekly-assignments/{child_id}", response_model=List[schemas.ChoreAssignment])
def get_weekly_assignments(
    child_id: int, 
    week_start: Optional[date] = None, 
    db: Session = Depends(get_db)
):
    """Get a child's chore assignments for a specific week"""
    # Verify child exists
    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    return db.query(models.ChoreAssignment).filter(
        models.ChoreAssignment.child_id == child_id,
        models.ChoreAssignment.week_start_date == week_start
    ).all()

@router.put("/assignments/{assignment_id}/complete")
def complete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Mark a specific chore assignment as completed"""
    assignment = db.query(models.ChoreAssignment).filter(
        models.ChoreAssignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.is_completed = True
    assignment.completion_date = date.today()
    db.commit()
    db.refresh(assignment)
    
    return {"status": "success", "completed_date": assignment.completion_date}

@router.get("/assignments/history/{child_id}", response_model=List[schemas.ChoreAssignment])
def get_assignment_history(
    child_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get historical chore assignments for a child within a date range"""
    query = db.query(models.ChoreAssignment).filter(
        models.ChoreAssignment.child_id == child_id
    )
    
    if start_date:
        query = query.filter(models.ChoreAssignment.week_start_date >= start_date)
    if end_date:
        query = query.filter(models.ChoreAssignment.week_start_date <= end_date)
    
    return query.order_by(models.ChoreAssignment.week_start_date.desc()).all()

@router.delete("/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Delete a specific chore assignment"""
    assignment = db.query(models.ChoreAssignment).filter(
        models.ChoreAssignment.id == assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(assignment)
    db.commit()
    
    return {"status": "success", "message": "Assignment deleted"}

@router.delete("/children/{child_id}")
def delete_child(child_id: int, db: Session = Depends(get_db)):
    """Delete a child and all their assignments"""
    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    # Delete all assignments first
    db.query(models.ChoreAssignment).filter(
        models.ChoreAssignment.child_id == child_id
    ).delete()
    
    db.delete(child)
    db.commit()
    return {"status": "success"}

@router.delete("/chores/{chore_id}")
def delete_chore(chore_id: int, db: Session = Depends(get_db)):
    """Delete a chore and all its assignments"""
    chore = db.query(models.Chore).filter(models.Chore.id == chore_id).first()
    if not chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    
    # Delete all assignments first
    db.query(models.ChoreAssignment).filter(
        models.ChoreAssignment.chore_id == chore_id
    ).delete()
    
    db.delete(chore)
    db.commit()
    return {"status": "success"}
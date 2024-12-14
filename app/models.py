from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import date
from .database import Base

class Child(Base):
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    weekly_allowance = Column(Float)
    # Instead of direct chore relationship, we'll have assignments
    chore_assignments = relationship("ChoreAssignment", back_populates="child")

class Chore(Base):
    __tablename__ = "chores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(String(255))
    frequency_per_week = Column(Integer, default=1)
    assignments = relationship("ChoreAssignment", back_populates="chore")

class ChoreAssignment(Base):
    __tablename__ = "chore_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"))
    chore_id = Column(Integer, ForeignKey("chores.id"))
    week_start_date = Column(Date, index=True)  # To track which week this assignment belongs to
    is_completed = Column(Boolean, default=False)
    completion_date = Column(Date, nullable=True)
    occurrence_number = Column(Integer, default=1)
    
    # Relationships
    child = relationship("Child", back_populates="chore_assignments")
    chore = relationship("Chore", back_populates="assignments")
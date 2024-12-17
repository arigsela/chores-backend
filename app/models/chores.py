from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from ..database import Base

class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    weekly_allowance = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="children")
    assignments = relationship("ChoreAssignment", back_populates="child")

class Chore(Base):
    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(String(255))
    frequency_per_week = Column(Integer, default=1)  # Added this field
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="chores")
    assignments = relationship("ChoreAssignment", back_populates="chore")

class ChoreAssignment(Base):
    __tablename__ = "chore_assignments"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"))
    chore_id = Column(Integer, ForeignKey("chores.id"))
    is_completed = Column(Boolean, default=False)
    completion_date = Column(Date, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    child = relationship("Child", back_populates="assignments")
    chore = relationship("Chore", back_populates="assignments")
    user = relationship("User", back_populates="assignments")
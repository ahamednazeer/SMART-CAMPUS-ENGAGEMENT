"""Complaint model for maintenance requests."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base


class ComplaintCategory(str, Enum):
    """Categories for complaints."""
    ELECTRICAL = "ELECTRICAL"
    PLUMBING = "PLUMBING"
    CLEANING = "CLEANING"
    FURNITURE = "FURNITURE"
    EQUIPMENT = "EQUIPMENT"
    OTHER = "OTHER"


class ComplaintStatus(str, Enum):
    """Status stages for complaints."""
    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class ComplaintPriority(str, Enum):
    """Priority levels for complaints."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Complaint(Base):
    """Complaint model for maintenance requests."""
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_type = Column(String(20), nullable=False)  # HOSTELLER or DAY_SCHOLAR
    
    # Complaint details
    category = Column(String(20), nullable=False)
    priority = Column(String(10), default="MEDIUM")
    location = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    
    # Status tracking
    status = Column(String(20), default=ComplaintStatus.SUBMITTED)
    
    # Assignment
    assigned_to = Column(String(100), nullable=True)  # Staff name/ID
    assigned_at = Column(DateTime, nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Admin tracking
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    closed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id], backref="complaints")
    verifier = relationship("User", foreign_keys=[verified_by])
    closer = relationship("User", foreign_keys=[closed_by])

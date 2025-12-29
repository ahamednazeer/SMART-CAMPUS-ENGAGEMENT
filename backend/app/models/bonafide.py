"""
Bonafide Certificate model for students.
Handles certificate requests from students and warden/admin approvals.
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base


class CertificateType(str, PyEnum):
    """Types of bonafide certificates available"""
    HOSTEL_BONAFIDE = "HOSTEL_BONAFIDE"  # For hostellers, warden approval
    GENERAL_BONAFIDE = "GENERAL_BONAFIDE"  # For all students, admin approval
    STAY_CERTIFICATE = "STAY_CERTIFICATE"
    CHARACTER_CERTIFICATE = "CHARACTER_CERTIFICATE"


class CertificatePurpose(str, PyEnum):
    """Purpose for requesting the certificate"""
    BANK = "BANK"
    SCHOLARSHIP = "SCHOLARSHIP"
    TRAVEL = "TRAVEL"
    PASSPORT = "PASSPORT"
    VISA = "VISA"
    EMPLOYMENT = "EMPLOYMENT"
    HIGHER_STUDIES = "HIGHER_STUDIES"
    OTHER = "OTHER"


class CertificateStatus(str, PyEnum):
    """Status of certificate request"""
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DOWNLOADED = "DOWNLOADED"


class ApproverType(str, PyEnum):
    """Who can approve this certificate"""
    WARDEN = "WARDEN"  # Hostel certificates
    ADMIN = "ADMIN"  # General certificates


class BonafideCertificate(Base):
    """
    Model for Bonafide Certificate requests.
    Students request certificates, wardens approve/reject.
    """
    __tablename__ = "bonafide_certificates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Student who requested
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Hostel info (snapshot at request time)
    hostel_id = Column(Integer, ForeignKey("hostels.id", ondelete="SET NULL"), nullable=True)
    room_number = Column(String(50), nullable=True)
    
    # Certificate details
    certificate_type = Column(Enum(CertificateType), nullable=False, default=CertificateType.HOSTEL_BONAFIDE)
    purpose = Column(Enum(CertificatePurpose), nullable=False)
    purpose_details = Column(Text, nullable=True)  # Additional details if purpose is OTHER
    
    # Request status
    status = Column(Enum(CertificateStatus), nullable=False, default=CertificateStatus.SUBMITTED)
    rejection_reason = Column(Text, nullable=True)
    
    # Who should approve this certificate
    approver_type = Column(Enum(ApproverType), nullable=False, default=ApproverType.WARDEN)
    
    # Approval details
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Certificate number (generated on approval)
    certificate_number = Column(String(50), unique=True, nullable=True, index=True)
    
    # Download tracking
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime, nullable=True)
    
    # Validity period (if applicable)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("User", foreign_keys=[student_id], backref="certificate_requests")
    hostel = relationship("Hostel", backref="certificates")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<BonafideCertificate(id={self.id}, student_id={self.student_id}, status={self.status})>"

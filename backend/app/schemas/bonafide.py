"""
Pydantic schemas for Bonafide Certificate requests.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models.bonafide import CertificateType, CertificatePurpose, CertificateStatus


# ============ Request Schemas ============

class CertificateRequestCreate(BaseModel):
    """Schema for creating a new certificate request"""
    certificate_type: CertificateType = CertificateType.HOSTEL_BONAFIDE
    purpose: CertificatePurpose
    purpose_details: Optional[str] = Field(None, max_length=500)

    @field_validator('purpose_details')
    @classmethod
    def validate_purpose_details(cls, v, info):
        # Require details if purpose is OTHER
        if info.data.get('purpose') == CertificatePurpose.OTHER and not v:
            raise ValueError('Purpose details required when purpose is OTHER')
        return v


class CertificateApproval(BaseModel):
    """Schema for approving/rejecting a certificate"""
    approved: bool
    rejection_reason: Optional[str] = Field(None, max_length=500)

    @field_validator('rejection_reason')
    @classmethod
    def validate_rejection_reason(cls, v, info):
        if info.data.get('approved') is False and not v:
            raise ValueError('Rejection reason required when rejecting')
        return v


# ============ Response Schemas ============

class CertificateOut(BaseModel):
    """Basic certificate response"""
    id: int
    student_id: int
    hostel_id: Optional[int]
    room_number: Optional[str]
    certificate_type: CertificateType
    purpose: CertificatePurpose
    purpose_details: Optional[str]
    status: CertificateStatus
    rejection_reason: Optional[str]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    certificate_number: Optional[str]
    download_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CertificateWithDetails(CertificateOut):
    """Certificate with student and hostel details for warden view"""
    student_name: Optional[str] = None
    student_register_number: Optional[str] = None
    student_department: Optional[str] = None
    hostel_name: Optional[str] = None


class CertificateSummary(BaseModel):
    """Summary statistics for certificates"""
    total_requests: int
    pending_count: int
    approved_count: int
    rejected_count: int
    downloaded_count: int


class CertificateListOut(BaseModel):
    """Paginated list of certificates"""
    certificates: list[CertificateOut]
    total: int
    page: int
    page_size: int

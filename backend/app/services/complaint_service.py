"""Service for Complaints with AI integration."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.complaint_repository import ComplaintRepository
from app.models.complaint import Complaint, ComplaintCategory, ComplaintStatus, ComplaintPriority
from app.services.ai_service import AIService


class ComplaintService:
    """Service for managing maintenance complaints."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ComplaintRepository(db)
    
    async def get_by_id(self, complaint_id: int) -> Complaint | None:
        """Get complaint by ID."""
        return await self.repo.get_by_id(complaint_id)
    
    async def create_complaint(
        self,
        student_id: int,
        student_type: str,
        location: str,
        description: str,
        category: str | None = None,
        image_url: str | None = None
    ) -> Complaint:
        """Create a new complaint with AI categorization and priority."""
        # Check duplicate
        if category and await self.repo.check_duplicate(student_id, location, category):
            raise ValueError("You already have an open complaint for this location and category")
        
        # AI Smart Detection: Check if this is actually an informational query
        submission_type = await AIService.detect_submission_type(description)
        if submission_type == "QUERY":
            raise ValueError(
                "This looks like an informational question (not a maintenance issue). "
                "Please use the 'Queries' section instead to ask questions about rules, policies, or timings."
            )
        
        # AI categorization if not provided
        if not category:
            category = await self.categorize_complaint(description)
        
        # AI priority assessment
        priority = await self.assess_priority(description, category)
        
        complaint = Complaint(
            student_id=student_id,
            student_type=student_type,
            category=category,
            priority=priority,
            location=location,
            description=description,
            image_url=image_url,
            status=ComplaintStatus.SUBMITTED
        )
        
        return await self.repo.create(complaint)
    
    async def get_my_complaints(self, student_id: int) -> list[Complaint]:
        """Get all complaints for a student."""
        return await self.repo.get_student_complaints(student_id)
    
    async def get_pending_complaints(self, student_type: str | None = None) -> list[Complaint]:
        """Get pending complaints for admin/warden."""
        return await self.repo.get_pending_complaints(student_type)
    
    async def get_resolved_complaints(self, student_type: str | None = None) -> list[Complaint]:
        """Get resolved/rejected complaints."""
        return await self.repo.get_resolved_complaints(student_type)
    
    async def get_complaint(self, complaint_id: int) -> Complaint | None:
        """Get a specific complaint."""
        return await self.repo.get_by_id(complaint_id)
    
    async def verify_complaint(
        self,
        complaint_id: int,
        admin_id: int,
        assigned_to: str | None = None
    ) -> Complaint:
        """Verify complaint and optionally assign to staff."""
        complaint = await self.repo.get_by_id(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        if complaint.status != ComplaintStatus.SUBMITTED:
            raise ValueError("Can only verify submitted complaints")
        
        complaint.status = ComplaintStatus.IN_PROGRESS
        complaint.verified_by = admin_id
        complaint.verified_at = datetime.utcnow()
        
        if assigned_to:
            complaint.assigned_to = assigned_to
            complaint.assigned_at = datetime.utcnow()
        
        return await self.repo.update(complaint)
    
    async def reject_complaint(
        self,
        complaint_id: int,
        admin_id: int,
        reason: str
    ) -> Complaint:
        """Reject a complaint with reason."""
        complaint = await self.repo.get_by_id(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        complaint.status = ComplaintStatus.REJECTED
        complaint.rejection_reason = reason
        complaint.closed_by = admin_id
        complaint.closed_at = datetime.utcnow()
        
        return await self.repo.update(complaint)
    
    async def assign_staff(
        self,
        complaint_id: int,
        admin_id: int,
        staff_name: str
    ) -> Complaint:
        """Assign complaint to maintenance staff."""
        complaint = await self.repo.get_by_id(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        if complaint.status not in [ComplaintStatus.SUBMITTED, ComplaintStatus.IN_PROGRESS]:
            raise ValueError("Cannot assign closed or rejected complaint")
        
        # If was SUBMITTED, move to IN_PROGRESS
        if complaint.status == ComplaintStatus.SUBMITTED:
            complaint.status = ComplaintStatus.IN_PROGRESS
            complaint.verified_by = admin_id
            complaint.verified_at = datetime.utcnow()
        
        complaint.assigned_to = staff_name
        complaint.assigned_at = datetime.utcnow()
        
        return await self.repo.update(complaint)
    
    async def close_complaint(
        self,
        complaint_id: int,
        admin_id: int,
        resolution_notes: str | None = None
    ) -> Complaint:
        """Close a complaint with optional notes."""
        complaint = await self.repo.get_by_id(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        if complaint.status == ComplaintStatus.CLOSED:
            raise ValueError("Complaint already closed")
        
        complaint.status = ComplaintStatus.CLOSED
        complaint.resolution_notes = resolution_notes
        complaint.closed_by = admin_id
        complaint.closed_at = datetime.utcnow()
        
        return await self.repo.update(complaint)
    
    async def categorize_complaint(self, description: str) -> str:
        """Use AI to categorize a complaint."""
        try:
            category = await AIService.categorize_complaint(description)
            return category
        except Exception:
            return ComplaintCategory.OTHER.value
    
    async def assess_priority(self, description: str, category: str) -> str:
        """Use AI to assess complaint priority."""
        try:
            priority = await AIService.assess_complaint_priority(description, category)
            return priority
        except Exception:
            return ComplaintPriority.MEDIUM.value

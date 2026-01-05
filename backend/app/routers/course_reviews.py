"""
Course Review API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.course_review_service import CourseReviewService


router = APIRouter(prefix="/course-reviews", tags=["Course Reviews"])


# ============== Schemas ==============

class ReviewWindowCreate(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    semester: int | None = None
    department: str | None = None


class ReviewCreate(BaseModel):
    course_id: int
    difficulty_rating: int = Field(..., ge=1, le=5)
    clarity_rating: int = Field(..., ge=1, le=5)
    relevance_rating: int = Field(..., ge=1, le=5)
    overall_rating: int = Field(..., ge=1, le=5)
    feedback_text: str | None = None


class ModerationRequest(BaseModel):
    approved: bool
    moderation_notes: str | None = None
    has_personal_attack: bool = False
    has_abusive_content: bool = False


class WindowResponse(BaseModel):
    id: int
    name: str
    start_date: datetime
    end_date: datetime
    semester: int | None
    department: str | None
    is_active: bool
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    id: int
    course_id: int
    difficulty_rating: int
    clarity_rating: int
    relevance_rating: int
    overall_rating: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AggregateResponse(BaseModel):
    course_id: int
    avg_difficulty: float
    avg_clarity: float
    avg_relevance: float
    avg_overall: float
    total_reviews: int
    
    class Config:
        from_attributes = True


# ============== Admin Endpoints ==============

@router.post("/windows", response_model=WindowResponse)
async def create_review_window(
    data: ReviewWindowCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Create a review window (Admin only)."""
    service = CourseReviewService(db)
    window = await service.create_review_window(
        created_by=current_user.id,
        **data.model_dump()
    )
    return window


@router.get("/windows", response_model=list[WindowResponse])
async def get_windows(
    active_only: bool = False,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get all review windows."""
    service = CourseReviewService(db)
    windows = await service.get_windows(active_only)
    return windows


@router.get("/windows/current", response_model=WindowResponse)
async def get_current_window(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the currently active review window."""
    service = CourseReviewService(db)
    window = await service.get_active_window()
    if not window:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active review window"
        )
    return window


# ============== Moderation ==============

@router.get("/pending")
async def get_pending_reviews(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get reviews pending moderation."""
    service = CourseReviewService(db)
    reviews = await service.get_pending_reviews()
    return {
        "reviews": [
            {
                "id": r.id,
                "course_id": r.course_id,
                "feedback_text": r.feedback_text,
                "difficulty_rating": r.difficulty_rating,
                "clarity_rating": r.clarity_rating,
                "relevance_rating": r.relevance_rating,
                "overall_rating": r.overall_rating,
                "created_at": r.created_at
            }
            for r in reviews
        ],
        "count": len(reviews)
    }


@router.post("/{review_id}/moderate")
async def moderate_review(
    review_id: int,
    data: ModerationRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Moderate a review."""
    service = CourseReviewService(db)
    review = await service.moderate_review(
        review_id=review_id,
        approved=data.approved,
        moderated_by=current_user.id,
        moderation_notes=data.moderation_notes,
        has_personal_attack=data.has_personal_attack,
        has_abusive_content=data.has_abusive_content
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return {"message": "Review moderated", "status": review.status.value}


# ============== Student Endpoints ==============

@router.post("", response_model=ReviewResponse)
async def submit_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit a course review (anonymous to faculty)."""
    service = CourseReviewService(db)
    review = await service.submit_review(
        student_id=current_user.id,
        **data.model_dump()
    )
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already reviewed this course"
        )
    
    return review


@router.get("/my-reviews", response_model=list[ReviewResponse])
async def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get reviews submitted by the current student."""
    service = CourseReviewService(db)
    reviews = await service.get_student_reviews(current_user.id)
    return reviews


@router.get("/check/{course_id}")
async def check_reviewed(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if current user has reviewed a course."""
    service = CourseReviewService(db)
    review = await service.get_student_review(current_user.id, course_id)
    return {"reviewed": review is not None}


# ============== Aggregate Statistics (Public) ==============

@router.get("/aggregates", response_model=list[AggregateResponse])
async def get_all_aggregates(
    min_reviews: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregate statistics for all courses."""
    service = CourseReviewService(db)
    aggregates = await service.get_all_course_aggregates(min_reviews=min_reviews)
    return aggregates


@router.get("/aggregates/{course_id}", response_model=AggregateResponse)
async def get_course_aggregate(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregate statistics for a specific course."""
    service = CourseReviewService(db)
    aggregate = await service.get_course_aggregate(course_id)
    
    if not aggregate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reviews for this course"
        )
    
    return aggregate

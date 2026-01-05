"""
Course Review service for anonymous moderated feedback.
"""
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_review import (
    CourseReview, CourseReviewAggregate, ReviewWindow,
    ReviewStatus
)


class CourseReviewService:
    """Service for course review management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== Review Window Management ==============
    
    async def create_review_window(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime,
        semester: int | None = None,
        department: str | None = None,
        created_by: int | None = None
    ) -> ReviewWindow:
        """Create a review window."""
        window = ReviewWindow(
            name=name,
            start_date=start_date,
            end_date=end_date,
            semester=semester,
            department=department,
            created_by=created_by
        )
        self.db.add(window)
        await self.db.flush()
        await self.db.refresh(window)
        return window
    
    async def get_active_window(self) -> ReviewWindow | None:
        """Get the currently active review window."""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(ReviewWindow).where(
                ReviewWindow.start_date <= now,
                ReviewWindow.end_date >= now,
                ReviewWindow.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_windows(self, active_only: bool = False) -> list[ReviewWindow]:
        """Get all review windows."""
        query = select(ReviewWindow)
        if active_only:
            query = query.where(ReviewWindow.is_active == True)
        query = query.order_by(ReviewWindow.start_date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ============== Review Management ==============
    
    async def submit_review(
        self,
        course_id: int,
        student_id: int,
        difficulty_rating: int,
        clarity_rating: int,
        relevance_rating: int,
        overall_rating: int,
        feedback_text: str | None = None
    ) -> CourseReview | None:
        """Submit a course review."""
        # Check if there's an active review window
        window = await self.get_active_window()
        
        # Check if student already reviewed this course
        existing = await self.get_student_review(student_id, course_id)
        if existing:
            return None  # Already reviewed
        
        review = CourseReview(
            course_id=course_id,
            student_id=student_id,
            window_id=window.id if window else None,
            difficulty_rating=min(5, max(1, difficulty_rating)),
            clarity_rating=min(5, max(1, clarity_rating)),
            relevance_rating=min(5, max(1, relevance_rating)),
            overall_rating=min(5, max(1, overall_rating)),
            feedback_text=feedback_text
        )
        self.db.add(review)
        await self.db.flush()
        
        # Update aggregates
        await self._update_aggregate(course_id)
        
        await self.db.refresh(review)
        return review
    
    async def get_student_review(
        self,
        student_id: int,
        course_id: int
    ) -> CourseReview | None:
        """Get a student's review for a course."""
        result = await self.db.execute(
            select(CourseReview).where(
                CourseReview.student_id == student_id,
                CourseReview.course_id == course_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_pending_reviews(self) -> list[CourseReview]:
        """Get all reviews pending moderation."""
        result = await self.db.execute(
            select(CourseReview).where(
                CourseReview.status == ReviewStatus.PENDING,
                CourseReview.feedback_text != None
            ).order_by(CourseReview.created_at)
        )
        return list(result.scalars().all())
    
    async def moderate_review(
        self,
        review_id: int,
        approved: bool,
        moderated_by: int,
        moderation_notes: str | None = None,
        has_personal_attack: bool = False,
        has_abusive_content: bool = False
    ) -> CourseReview | None:
        """Moderate a review."""
        result = await self.db.execute(
            select(CourseReview).where(CourseReview.id == review_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            return None
        
        review.status = ReviewStatus.APPROVED if approved else ReviewStatus.REJECTED
        review.is_moderated = True
        review.moderated_by = moderated_by
        review.moderated_at = datetime.utcnow()
        review.moderation_notes = moderation_notes
        review.has_personal_attack = has_personal_attack
        review.has_abusive_content = has_abusive_content
        
        await self.db.flush()
        
        # Update aggregates if approved
        if approved:
            await self._update_aggregate(review.course_id)
        
        await self.db.refresh(review)
        return review
    
    # ============== Aggregate Statistics ==============
    
    async def _update_aggregate(self, course_id: int):
        """Update aggregate statistics for a course."""
        # Get all approved reviews
        result = await self.db.execute(
            select(
                func.avg(CourseReview.difficulty_rating),
                func.avg(CourseReview.clarity_rating),
                func.avg(CourseReview.relevance_rating),
                func.avg(CourseReview.overall_rating),
                func.count(CourseReview.id)
            ).where(
                CourseReview.course_id == course_id,
                CourseReview.status == ReviewStatus.APPROVED
            )
        )
        row = result.one()
        
        # Get or create aggregate
        agg_result = await self.db.execute(
            select(CourseReviewAggregate).where(
                CourseReviewAggregate.course_id == course_id
            )
        )
        aggregate = agg_result.scalar_one_or_none()
        
        if not aggregate:
            aggregate = CourseReviewAggregate(course_id=course_id)
            self.db.add(aggregate)
        
        aggregate.avg_difficulty = round(row[0] or 0, 2)
        aggregate.avg_clarity = round(row[1] or 0, 2)
        aggregate.avg_relevance = round(row[2] or 0, 2)
        aggregate.avg_overall = round(row[3] or 0, 2)
        aggregate.total_reviews = row[4] or 0
        
        await self.db.flush()
    
    async def get_course_aggregate(
        self,
        course_id: int
    ) -> CourseReviewAggregate | None:
        """Get aggregate review statistics for a course."""
        result = await self.db.execute(
            select(CourseReviewAggregate).where(
                CourseReviewAggregate.course_id == course_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_course_aggregates(
        self,
        department: str | None = None,
        min_reviews: int = 0
    ) -> list[CourseReviewAggregate]:
        """Get aggregates for all courses."""
        query = select(CourseReviewAggregate).where(
            CourseReviewAggregate.total_reviews >= min_reviews
        )
        query = query.order_by(CourseReviewAggregate.avg_overall.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ============== Student Access ==============
    
    async def get_reviewable_courses(
        self,
        student_id: int
    ) -> list[int]:
        """Get course IDs that a student can still review."""
        # Get courses student has reviewed
        result = await self.db.execute(
            select(CourseReview.course_id).where(
                CourseReview.student_id == student_id
            )
        )
        reviewed_course_ids = set(result.scalars().all())
        
        # TODO: Get enrolled courses from CourseEnrollment
        # For now, return empty - this should be joined with enrollment data
        return []
    
    async def get_student_reviews(
        self,
        student_id: int
    ) -> list[CourseReview]:
        """Get all reviews submitted by a student."""
        result = await self.db.execute(
            select(CourseReview).where(
                CourseReview.student_id == student_id
            ).order_by(CourseReview.created_at.desc())
        )
        return list(result.scalars().all())

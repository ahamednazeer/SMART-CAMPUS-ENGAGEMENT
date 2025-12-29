"""Service for Campus Queries with AI integration."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.query_repository import QueryRepository
from app.models.query import Query, QueryCategory, QueryStatus
from app.services.ai_service import AIService


class QueryService:
    """Service for managing student queries."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QueryRepository(db)
    
    async def create_query(
        self,
        student_id: int,
        student_type: str,
        description: str,
        category: str | None = None
    ) -> Query:
        """Create a new query, auto-categorize if category not provided."""
        # Validate no duplicate
        if await self.repo.check_duplicate(student_id, description):
            raise ValueError("You already have an open query with this description")
        
        # AI Smart Detection: Check if this is actually a maintenance complaint
        submission_type = await AIService.detect_submission_type(description)
        if submission_type == "COMPLAINT":
            raise ValueError(
                "This looks like a maintenance issue (repair/cleaning needed). "
                "Please use the 'Complaints' section instead to report facility problems."
            )
        
        # Auto-categorize if needed
        if not category:
            category = await self.categorize_query(description)
        
        query = Query(
            student_id=student_id,
            student_type=student_type,
            category=category,
            description=description,
            status=QueryStatus.OPEN
        )
        
        return await self.repo.create(query)
    
    async def get_my_queries(self, student_id: int) -> list[Query]:
        """Get all queries for a student."""
        return await self.repo.get_student_queries(student_id)
    
    async def get_pending_queries(self, student_type: str | None = None) -> list[Query]:
        """Get pending queries for admin/warden view filtered by student type."""
        return await self.repo.get_pending_queries(student_type)
    
    async def get_resolved_queries(self, student_type: str | None = None) -> list[Query]:
        """Get resolved queries for history view filtered by student type."""
        return await self.repo.get_resolved_queries(student_type)
    
    async def get_query(self, query_id: int) -> Query | None:
        """Get a specific query."""
        return await self.repo.get_by_id(query_id)
    
    async def respond_to_query(
        self,
        query_id: int,
        responder_id: int,
        response: str
    ) -> Query:
        """Respond to a query and mark as resolved."""
        query = await self.repo.get_by_id(query_id)
        if not query:
            raise ValueError("Query not found")
        
        if query.status == QueryStatus.RESOLVED:
            raise ValueError("Query already resolved")
        
        query.response = response
        query.responded_by = responder_id
        query.responded_at = datetime.now(timezone.utc)
        query.status = QueryStatus.RESOLVED
        
        return await self.repo.update(query)
    
    async def categorize_query(self, description: str) -> str:
        """Use AI to categorize a query."""
        try:
            category = await AIService.categorize_query(description)
            return category
        except Exception:
            return QueryCategory.OTHERS.value
    
    async def suggest_response(self, query_id: int) -> str:
        """Generate AI-suggested response for a query."""
        query = await self.repo.get_by_id(query_id)
        if not query:
            raise ValueError("Query not found")
        
        # Get student name from the loaded relationship
        student_name = None
        if query.student:
            student_name = f"{query.student.first_name} {query.student.last_name}"
        
        return await AIService.suggest_query_response(
            query.description,
            query.category,
            query.student_type,
            student_name
        )

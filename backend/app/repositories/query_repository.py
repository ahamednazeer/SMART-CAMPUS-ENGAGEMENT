"""Repository for Query model."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.query import Query, QueryStatus


class QueryRepository:
    """Repository for Query CRUD operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, query: Query) -> Query:
        """Create a new query."""
        self.db.add(query)
        await self.db.flush()
        await self.db.refresh(query)
        return query
    
    async def get_by_id(self, query_id: int) -> Query | None:
        """Get query by ID."""
        result = await self.db.execute(
            select(Query)
            .options(selectinload(Query.student), selectinload(Query.responder))
            .where(Query.id == query_id)
        )
        return result.scalar_one_or_none()
    
    async def get_student_queries(self, student_id: int) -> list[Query]:
        """Get all queries by a student."""
        result = await self.db.execute(
            select(Query)
            .where(Query.student_id == student_id)
            .order_by(Query.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_pending_queries(self, student_type: str | None = None) -> list[Query]:
        """Get pending (open) queries, optionally filtered by student type."""
        stmt = select(Query).options(selectinload(Query.student)).where(Query.status == QueryStatus.OPEN)
        
        if student_type:
            stmt = stmt.where(Query.student_type == student_type)
        
        stmt = stmt.order_by(Query.created_at.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_all_open_queries(self) -> list[Query]:
        """Get all open queries for admin view."""
        result = await self.db.execute(
            select(Query)
            .options(selectinload(Query.student))
            .where(Query.status == QueryStatus.OPEN)
            .order_by(Query.created_at.asc())
        )
        return list(result.scalars().all())
    
    async def get_resolved_queries(self, student_type: str | None = None) -> list[Query]:
        """Get resolved queries, optionally filtered by student type."""
        stmt = select(Query).options(selectinload(Query.student)).where(Query.status == QueryStatus.RESOLVED)
        
        if student_type:
            stmt = stmt.where(Query.student_type == student_type)
        
        stmt = stmt.order_by(Query.responded_at.desc()).limit(50)  # Last 50 resolved
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def update(self, query: Query) -> Query:
        """Update a query."""
        await self.db.flush()
        await self.db.refresh(query)
        return query
    
    async def check_duplicate(self, student_id: int, description: str) -> bool:
        """Check if student has an open query with same description."""
        result = await self.db.execute(
            select(Query)
            .where(
                Query.student_id == student_id,
                Query.status == QueryStatus.OPEN,
                Query.description == description
            )
        )
        return result.scalar_one_or_none() is not None

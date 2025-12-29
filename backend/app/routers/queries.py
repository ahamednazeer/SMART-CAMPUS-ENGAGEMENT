"""Router for Campus Queries."""
from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User, UserRole
from app.services.query_service import QueryService
from app.models.query import QueryCategory, QueryStatus

router = APIRouter(prefix="/queries", tags=["Campus Queries"])


# Schemas
class QueryCreate(BaseModel):
    """Schema for creating a query."""
    description: str
    category: str | None = None  # Optional - AI will auto-categorize


class QueryResponse(BaseModel):
    """Schema for responding to a query."""
    response: str


class QueryOut(BaseModel):
    """Schema for query output."""
    id: int
    student_id: int
    student_type: str
    category: str
    description: str
    status: str
    response: str | None
    responded_by: int | None
    created_at: datetime
    responded_at: datetime | None
    student_name: str | None = None
    
    class Config:
        from_attributes = True


class AISuggestionOut(BaseModel):
    """Schema for AI-suggested response."""
    suggestion: str


# Endpoints

@router.post("", response_model=QueryOut, status_code=status.HTTP_201_CREATED)
async def create_query(
    data: QueryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Raise a new query (students only). AI auto-categorizes if category not provided."""
    if current_user.role not in [UserRole.STUDENT]:
        raise HTTPException(status_code=403, detail="Only students can raise queries")
    
    if not data.description or len(data.description.strip()) < 10:
        raise HTTPException(status_code=400, detail="Query description must be at least 10 characters")
    
    service = QueryService(db)
    
    try:
        query = await service.create_query(
            student_id=current_user.id,
            student_type=current_user.student_category or "DAY_SCHOLAR",
            description=data.description.strip(),
            category=data.category
        )
        
        return QueryOut(
            id=query.id,
            student_id=query.student_id,
            student_type=query.student_type,
            category=query.category,
            description=query.description,
            status=query.status,
            response=query.response,
            responded_by=query.responded_by,
            created_at=query.created_at,
            responded_at=query.responded_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my", response_model=list[QueryOut])
async def get_my_queries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get all queries for the current student."""
    service = QueryService(db)
    queries = await service.get_my_queries(current_user.id)
    
    return [
        QueryOut(
            id=q.id,
            student_id=q.student_id,
            student_type=q.student_type,
            category=q.category,
            description=q.description,
            status=q.status,
            response=q.response,
            responded_by=q.responded_by,
            created_at=q.created_at,
            responded_at=q.responded_at
        )
        for q in queries
    ]


@router.get("/pending", response_model=list[QueryOut])
async def get_pending_queries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Get all pending (open) queries for admin view - DAY_SCHOLAR queries only."""
    service = QueryService(db)
    queries = await service.get_pending_queries(student_type="DAY_SCHOLAR")
    
    return [
        QueryOut(
            id=q.id,
            student_id=q.student_id,
            student_type=q.student_type,
            category=q.category,
            description=q.description,
            status=q.status,
            response=q.response,
            responded_by=q.responded_by,
            created_at=q.created_at,
            responded_at=q.responded_at,
            student_name=f"{q.student.first_name} {q.student.last_name}" if q.student else None
        )
        for q in queries
    ]


@router.get("/admin/resolved", response_model=list[QueryOut])
async def get_admin_resolved_queries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Get resolved queries from day scholars for admin history view."""
    service = QueryService(db)
    queries = await service.get_resolved_queries(student_type="DAY_SCHOLAR")
    
    return [
        QueryOut(
            id=q.id,
            student_id=q.student_id,
            student_type=q.student_type,
            category=q.category,
            description=q.description,
            status=q.status,
            response=q.response,
            responded_by=q.responded_by,
            created_at=q.created_at,
            responded_at=q.responded_at,
            student_name=f"{q.student.first_name} {q.student.last_name}" if q.student else None
        )
        for q in queries
    ]


@router.get("/warden/pending", response_model=list[QueryOut])
async def get_warden_pending_queries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get pending queries from hostellers for warden view."""
    if current_user.role != UserRole.WARDEN:
        raise HTTPException(status_code=403, detail="Only wardens can access this endpoint")
    
    service = QueryService(db)
    queries = await service.get_pending_queries(student_type="HOSTELLER")
    
    return [
        QueryOut(
            id=q.id,
            student_id=q.student_id,
            student_type=q.student_type,
            category=q.category,
            description=q.description,
            status=q.status,
            response=q.response,
            responded_by=q.responded_by,
            created_at=q.created_at,
            responded_at=q.responded_at,
            student_name=f"{q.student.first_name} {q.student.last_name}" if q.student else None
        )
        for q in queries
    ]


@router.get("/{query_id}/suggest", response_model=AISuggestionOut)
async def get_ai_suggestion(
    query_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get AI-suggested response for a query (admin or warden)."""
    if current_user.role not in [UserRole.ADMIN, UserRole.WARDEN]:
        raise HTTPException(status_code=403, detail="Only admins or wardens can access this endpoint")
    
    service = QueryService(db)
    
    try:
        suggestion = await service.suggest_response(query_id)
        return AISuggestionOut(suggestion=suggestion)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{query_id}/respond", response_model=QueryOut)
async def respond_to_query(
    query_id: int,
    data: QueryResponse,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Respond to a query and mark as resolved (admin or warden)."""
    if current_user.role not in [UserRole.ADMIN, UserRole.WARDEN]:
        raise HTTPException(status_code=403, detail="Only admins or wardens can respond")
    
    if not data.response or len(data.response.strip()) < 5:
        raise HTTPException(status_code=400, detail="Response must be at least 5 characters")
    
    service = QueryService(db)
    
    try:
        query = await service.respond_to_query(
            query_id=query_id,
            responder_id=current_user.id,
            response=data.response.strip()
        )
        
        return QueryOut(
            id=query.id,
            student_id=query.student_id,
            student_type=query.student_type,
            category=query.category,
            description=query.description,
            status=query.status,
            response=query.response,
            responded_by=query.responded_by,
            created_at=query.created_at,
            responded_at=query.responded_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/warden/resolved", response_model=list[QueryOut])
async def get_warden_resolved_queries(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get resolved queries from hostellers for warden history view."""
    if current_user.role != UserRole.WARDEN:
        raise HTTPException(status_code=403, detail="Only wardens can access this endpoint")
    
    service = QueryService(db)
    queries = await service.get_resolved_queries(student_type="HOSTELLER")
    
    return [
        QueryOut(
            id=q.id,
            student_id=q.student_id,
            student_type=q.student_type,
            category=q.category,
            description=q.description,
            status=q.status,
            response=q.response,
            responded_by=q.responded_by,
            created_at=q.created_at,
            responded_at=q.responded_at,
            student_name=f"{q.student.first_name} {q.student.last_name}" if q.student else None
        )
        for q in queries
    ]


@router.get("/categories")
async def get_categories():
    """Get available query categories."""
    return [
        {"value": cat.value, "label": cat.value.title()}
        for cat in QueryCategory
    ]

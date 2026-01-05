"""
Knowledge Graph API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.knowledge_graph import DependencyStrength, ProgressStatus
from app.services.knowledge_graph_service import KnowledgeGraphService


router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])


# ============== Schemas ==============

class TopicCreate(BaseModel):
    name: str
    description: str | None = None
    subject_code: str | None = None
    course_id: int | None = None
    semester: int | None = None
    difficulty_level: int = Field(default=1, ge=1, le=5)
    estimated_hours: int | None = None
    keywords: str | None = None


class DependencyCreate(BaseModel):
    prerequisite_id: int
    strength: str = "RECOMMENDED"  # REQUIRED, RECOMMENDED, RELATED
    reason: str | None = None


class ProgressUpdate(BaseModel):
    status: str | None = None  # NOT_STARTED, IN_PROGRESS, COMPLETED, NEEDS_REVIEW
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    confidence_score: int | None = Field(default=None, ge=0, le=100)
    time_spent_minutes: int | None = None


class PositionUpdate(BaseModel):
    x_position: int
    y_position: int


class LearningPathCreate(BaseModel):
    name: str
    description: str | None = None
    department: str | None = None
    target_semester: int | None = None
    topic_ids: list[int] | None = None


class TopicResponse(BaseModel):
    id: int
    name: str
    description: str | None
    subject_code: str | None
    course_id: int | None
    semester: int | None
    difficulty_level: int
    estimated_hours: int | None
    x_position: int | None
    y_position: int | None
    is_active: bool
    
    class Config:
        from_attributes = True


class ProgressResponse(BaseModel):
    id: int
    student_id: int
    topic_id: int
    status: str
    progress_percent: int
    confidence_score: int | None
    time_spent_minutes: int
    
    class Config:
        from_attributes = True


class LearningPathResponse(BaseModel):
    id: int
    name: str
    description: str | None
    department: str | None
    target_semester: int | None
    estimated_hours: int | None
    is_active: bool
    
    class Config:
        from_attributes = True


# ============== Topic Management ==============

@router.post("/topics", response_model=TopicResponse)
async def create_topic(
    data: TopicCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new knowledge topic (Admin/Staff only)."""
    service = KnowledgeGraphService(db)
    topic = await service.create_topic(
        created_by=current_user.id,
        **data.model_dump()
    )
    return topic


@router.get("/topics", response_model=list[TopicResponse])
async def get_topics(
    course_id: int | None = None,
    subject_code: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all topics, optionally filtered by course or subject."""
    service = KnowledgeGraphService(db)
    
    if course_id:
        topics = await service.get_topics_by_course(course_id)
    elif subject_code:
        topics = await service.get_topics_by_subject(subject_code)
    else:
        # Return all topics (limited)
        topics = await service.search_topics("", limit=100)
    
    return topics


@router.get("/topics/search")
async def search_topics(
    q: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search topics by name or keywords."""
    service = KnowledgeGraphService(db)
    topics = await service.search_topics(q, limit)
    return {"topics": topics, "count": len(topics)}


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a topic by ID."""
    service = KnowledgeGraphService(db)
    topic = await service.get_topic(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    return topic


@router.put("/topics/{topic_id}/position")
async def update_topic_position(
    topic_id: int,
    data: PositionUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Update topic position in the graph visualization."""
    service = KnowledgeGraphService(db)
    topic = await service.update_topic_position(
        topic_id=topic_id,
        x_position=data.x_position,
        y_position=data.y_position
    )
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    return {"message": "Position updated"}


# ============== Dependency Management ==============

@router.post("/topics/{topic_id}/dependencies")
async def add_dependency(
    topic_id: int,
    data: DependencyCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Add a prerequisite dependency to a topic."""
    service = KnowledgeGraphService(db)
    
    strength = DependencyStrength.RECOMMENDED
    if data.strength == "REQUIRED":
        strength = DependencyStrength.REQUIRED
    elif data.strength == "RELATED":
        strength = DependencyStrength.RELATED
    
    dependency = await service.add_dependency(
        topic_id=topic_id,
        prerequisite_id=data.prerequisite_id,
        strength=strength,
        reason=data.reason
    )
    return {"message": "Dependency added", "id": dependency.id}


@router.get("/topics/{topic_id}/prerequisites", response_model=list[TopicResponse])
async def get_prerequisites(
    topic_id: int,
    required_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get prerequisite topics for a topic."""
    service = KnowledgeGraphService(db)
    topics = await service.get_prerequisites(topic_id, required_only)
    return topics


@router.get("/topics/{topic_id}/dependents", response_model=list[TopicResponse])
async def get_dependents(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get topics that depend on this topic."""
    service = KnowledgeGraphService(db)
    topics = await service.get_dependent_topics(topic_id)
    return topics


@router.delete("/topics/{topic_id}/dependencies/{prerequisite_id}")
async def remove_dependency(
    topic_id: int,
    prerequisite_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Remove a prerequisite dependency."""
    service = KnowledgeGraphService(db)
    success = await service.remove_dependency(topic_id, prerequisite_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found"
        )
    return {"message": "Dependency removed"}


# ============== Student Progress ==============

@router.get("/my-progress/{topic_id}", response_model=ProgressResponse)
async def get_my_progress(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's progress on a topic."""
    service = KnowledgeGraphService(db)
    progress = await service.get_student_progress(current_user.id, topic_id)
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress recorded"
        )
    return progress


@router.put("/my-progress/{topic_id}", response_model=ProgressResponse)
async def update_my_progress(
    topic_id: int,
    data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's progress on a topic."""
    service = KnowledgeGraphService(db)
    
    status_enum = None
    if data.status:
        status_enum = ProgressStatus(data.status)
    
    progress = await service.update_progress(
        student_id=current_user.id,
        topic_id=topic_id,
        status=status_enum,
        progress_percent=data.progress_percent,
        confidence_score=data.confidence_score,
        time_spent_minutes=data.time_spent_minutes
    )
    return progress


@router.get("/my-graph")
async def get_my_graph(
    course_id: int | None = None,
    subject_code: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the complete knowledge graph with user's progress overlay."""
    service = KnowledgeGraphService(db)
    graph_data = await service.get_student_graph_progress(
        student_id=current_user.id,
        course_id=course_id,
        subject_code=subject_code
    )
    return graph_data


@router.get("/my-weak-areas", response_model=list[TopicResponse])
async def get_weak_areas(
    threshold: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Identify topics where the student needs improvement."""
    service = KnowledgeGraphService(db)
    topics = await service.identify_weak_areas(current_user.id, threshold)
    return topics


@router.get("/suggested-next", response_model=list[TopicResponse])
async def get_suggested_topics(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get suggested next topics based on completed prerequisites."""
    service = KnowledgeGraphService(db)
    topics = await service.suggest_next_topics(current_user.id, limit)
    return topics


# ============== Learning Paths ==============

@router.post("/paths", response_model=LearningPathResponse)
async def create_learning_path(
    data: LearningPathCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Create a learning path (Admin/Staff only)."""
    service = KnowledgeGraphService(db)
    path = await service.create_learning_path(
        created_by=current_user.id,
        **data.model_dump()
    )
    return path


@router.get("/paths", response_model=list[LearningPathResponse])
async def get_learning_paths(
    department: str | None = None,
    target_semester: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available learning paths."""
    service = KnowledgeGraphService(db)
    paths = await service.get_learning_paths(department, target_semester)
    return paths


@router.get("/paths/{path_id}")
async def get_learning_path(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a learning path with its topics."""
    service = KnowledgeGraphService(db)
    path = await service.get_learning_path(path_id)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found"
        )
    
    return {
        "id": path.id,
        "name": path.name,
        "description": path.description,
        "department": path.department,
        "target_semester": path.target_semester,
        "estimated_hours": path.estimated_hours,
        "topics": [
            {"topic_id": t.topic_id, "order": t.order, "notes": t.notes}
            for t in sorted(path.topics, key=lambda x: x.order)
        ]
    }

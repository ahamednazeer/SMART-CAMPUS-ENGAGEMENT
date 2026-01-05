"""
Knowledge Graph service for visual learning maps.
"""
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge_graph import (
    KnowledgeTopic, TopicDependency, StudentTopicProgress,
    LearningPath, LearningPathTopic,
    DependencyStrength, ProgressStatus
)


class KnowledgeGraphService:
    """Service for knowledge graph and learning path management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== Topic Management ==============
    
    async def create_topic(
        self,
        name: str,
        subject_code: str | None = None,
        course_id: int | None = None,
        description: str | None = None,
        semester: int | None = None,
        difficulty_level: int = 1,
        estimated_hours: int | None = None,
        keywords: str | None = None,
        created_by: int | None = None
    ) -> KnowledgeTopic:
        """Create a new knowledge topic."""
        topic = KnowledgeTopic(
            name=name,
            subject_code=subject_code,
            course_id=course_id,
            description=description,
            semester=semester,
            difficulty_level=min(5, max(1, difficulty_level)),
            estimated_hours=estimated_hours,
            keywords=keywords,
            created_by=created_by
        )
        self.db.add(topic)
        await self.db.flush()
        await self.db.refresh(topic)
        return topic
    
    async def get_topic(self, topic_id: int) -> KnowledgeTopic | None:
        """Get a topic by ID with dependencies."""
        result = await self.db.execute(
            select(KnowledgeTopic)
            .options(
                selectinload(KnowledgeTopic.dependencies),
                selectinload(KnowledgeTopic.prerequisite_for)
            )
            .where(KnowledgeTopic.id == topic_id)
        )
        return result.scalar_one_or_none()
    
    async def get_topics_by_course(self, course_id: int) -> list[KnowledgeTopic]:
        """Get all topics for a course."""
        result = await self.db.execute(
            select(KnowledgeTopic).where(
                KnowledgeTopic.course_id == course_id,
                KnowledgeTopic.is_active == True
            ).order_by(KnowledgeTopic.semester, KnowledgeTopic.name)
        )
        return list(result.scalars().all())
    
    async def get_topics_by_subject(self, subject_code: str) -> list[KnowledgeTopic]:
        """Get all topics for a subject."""
        result = await self.db.execute(
            select(KnowledgeTopic).where(
                KnowledgeTopic.subject_code == subject_code,
                KnowledgeTopic.is_active == True
            ).order_by(KnowledgeTopic.difficulty_level)
        )
        return list(result.scalars().all())
    
    async def search_topics(
        self,
        query: str,
        limit: int = 20
    ) -> list[KnowledgeTopic]:
        """Search topics by name or keywords."""
        result = await self.db.execute(
            select(KnowledgeTopic).where(
                or_(
                    KnowledgeTopic.name.ilike(f"%{query}%"),
                    KnowledgeTopic.keywords.ilike(f"%{query}%")
                ),
                KnowledgeTopic.is_active == True
            ).limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_topic_position(
        self,
        topic_id: int,
        x_position: int,
        y_position: int
    ) -> KnowledgeTopic | None:
        """Update topic position in the graph visualization."""
        topic = await self.get_topic(topic_id)
        if not topic:
            return None
        
        topic.x_position = x_position
        topic.y_position = y_position
        await self.db.flush()
        await self.db.refresh(topic)
        return topic
    
    # ============== Dependency Management ==============
    
    async def add_dependency(
        self,
        topic_id: int,
        prerequisite_id: int,
        strength: DependencyStrength = DependencyStrength.RECOMMENDED,
        reason: str | None = None
    ) -> TopicDependency:
        """Add a prerequisite dependency between topics."""
        dependency = TopicDependency(
            topic_id=topic_id,
            prerequisite_id=prerequisite_id,
            strength=strength,
            reason=reason
        )
        self.db.add(dependency)
        await self.db.flush()
        await self.db.refresh(dependency)
        return dependency
    
    async def get_prerequisites(
        self,
        topic_id: int,
        required_only: bool = False
    ) -> list[KnowledgeTopic]:
        """Get prerequisite topics for a topic."""
        query = select(KnowledgeTopic).join(
            TopicDependency,
            TopicDependency.prerequisite_id == KnowledgeTopic.id
        ).where(TopicDependency.topic_id == topic_id)
        
        if required_only:
            query = query.where(TopicDependency.strength == DependencyStrength.REQUIRED)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_dependent_topics(self, topic_id: int) -> list[KnowledgeTopic]:
        """Get topics that depend on this topic."""
        result = await self.db.execute(
            select(KnowledgeTopic).join(
                TopicDependency,
                TopicDependency.topic_id == KnowledgeTopic.id
            ).where(TopicDependency.prerequisite_id == topic_id)
        )
        return list(result.scalars().all())
    
    async def remove_dependency(
        self,
        topic_id: int,
        prerequisite_id: int
    ) -> bool:
        """Remove a dependency."""
        result = await self.db.execute(
            select(TopicDependency).where(
                TopicDependency.topic_id == topic_id,
                TopicDependency.prerequisite_id == prerequisite_id
            )
        )
        dependency = result.scalar_one_or_none()
        if not dependency:
            return False
        
        await self.db.delete(dependency)
        await self.db.flush()
        return True
    
    # ============== Student Progress ==============
    
    async def get_student_progress(
        self,
        student_id: int,
        topic_id: int
    ) -> StudentTopicProgress | None:
        """Get a student's progress on a topic."""
        result = await self.db.execute(
            select(StudentTopicProgress).where(
                StudentTopicProgress.student_id == student_id,
                StudentTopicProgress.topic_id == topic_id
            )
        )
        return result.scalar_one_or_none()
    
    async def update_progress(
        self,
        student_id: int,
        topic_id: int,
        status: ProgressStatus | None = None,
        progress_percent: int | None = None,
        confidence_score: int | None = None,
        time_spent_minutes: int | None = None
    ) -> StudentTopicProgress:
        """Update or create student progress on a topic."""
        progress = await self.get_student_progress(student_id, topic_id)
        
        if not progress:
            progress = StudentTopicProgress(
                student_id=student_id,
                topic_id=topic_id,
                started_at=datetime.utcnow()
            )
            self.db.add(progress)
        
        if status:
            progress.status = status
            if status == ProgressStatus.COMPLETED:
                progress.completed_at = datetime.utcnow()
                progress.progress_percent = 100
        
        if progress_percent is not None:
            progress.progress_percent = min(100, max(0, progress_percent))
        
        if confidence_score is not None:
            progress.confidence_score = min(100, max(0, confidence_score))
        
        if time_spent_minutes:
            progress.time_spent_minutes += time_spent_minutes
        
        progress.last_activity_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(progress)
        return progress
    
    async def get_student_graph_progress(
        self,
        student_id: int,
        course_id: int | None = None,
        subject_code: str | None = None
    ) -> list[dict]:
        """Get complete graph with student progress overlay."""
        # Get topics
        topic_query = select(KnowledgeTopic).where(KnowledgeTopic.is_active == True)
        if course_id:
            topic_query = topic_query.where(KnowledgeTopic.course_id == course_id)
        if subject_code:
            topic_query = topic_query.where(KnowledgeTopic.subject_code == subject_code)
        
        topic_result = await self.db.execute(topic_query)
        topics = list(topic_result.scalars().all())
        
        # Get student progress for these topics
        topic_ids = [t.id for t in topics]
        progress_result = await self.db.execute(
            select(StudentTopicProgress).where(
                StudentTopicProgress.student_id == student_id,
                StudentTopicProgress.topic_id.in_(topic_ids)
            )
        )
        progress_map = {p.topic_id: p for p in progress_result.scalars().all()}
        
        # Get dependencies
        dep_result = await self.db.execute(
            select(TopicDependency).where(
                TopicDependency.topic_id.in_(topic_ids)
            )
        )
        dependencies = list(dep_result.scalars().all())
        
        # Build graph data
        nodes = []
        for topic in topics:
            progress = progress_map.get(topic.id)
            nodes.append({
                "id": topic.id,
                "name": topic.name,
                "subject_code": topic.subject_code,
                "difficulty": topic.difficulty_level,
                "x": topic.x_position,
                "y": topic.y_position,
                "status": progress.status.value if progress else "NOT_STARTED",
                "progress_percent": progress.progress_percent if progress else 0,
                "confidence_score": progress.confidence_score if progress else None
            })
        
        edges = [
            {
                "from": d.prerequisite_id,
                "to": d.topic_id,
                "strength": d.strength.value
            }
            for d in dependencies
        ]
        
        return {"nodes": nodes, "edges": edges}
    
    async def identify_weak_areas(
        self,
        student_id: int,
        threshold: int = 50
    ) -> list[KnowledgeTopic]:
        """Identify topics where student is weak (low confidence)."""
        result = await self.db.execute(
            select(KnowledgeTopic).join(
                StudentTopicProgress,
                StudentTopicProgress.topic_id == KnowledgeTopic.id
            ).where(
                StudentTopicProgress.student_id == student_id,
                or_(
                    StudentTopicProgress.confidence_score < threshold,
                    StudentTopicProgress.status == ProgressStatus.NEEDS_REVIEW
                )
            )
        )
        return list(result.scalars().all())
    
    # ============== Learning Paths ==============
    
    async def create_learning_path(
        self,
        name: str,
        description: str | None = None,
        department: str | None = None,
        target_semester: int | None = None,
        topic_ids: list[int] | None = None,
        created_by: int | None = None
    ) -> LearningPath:
        """Create a learning path."""
        path = LearningPath(
            name=name,
            description=description,
            department=department,
            target_semester=target_semester,
            created_by=created_by
        )
        self.db.add(path)
        await self.db.flush()
        
        # Add topics if provided
        if topic_ids:
            for i, topic_id in enumerate(topic_ids):
                path_topic = LearningPathTopic(
                    path_id=path.id,
                    topic_id=topic_id,
                    order=i
                )
                self.db.add(path_topic)
            await self.db.flush()
        
        await self.db.refresh(path)
        return path
    
    async def get_learning_path(self, path_id: int) -> LearningPath | None:
        """Get a learning path with topics."""
        result = await self.db.execute(
            select(LearningPath)
            .options(selectinload(LearningPath.topics))
            .where(LearningPath.id == path_id)
        )
        return result.scalar_one_or_none()
    
    async def get_learning_paths(
        self,
        department: str | None = None,
        target_semester: int | None = None
    ) -> list[LearningPath]:
        """Get available learning paths."""
        query = select(LearningPath).where(LearningPath.is_active == True)
        
        if department:
            query = query.where(LearningPath.department == department)
        if target_semester:
            query = query.where(LearningPath.target_semester == target_semester)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def suggest_next_topics(
        self,
        student_id: int,
        limit: int = 5
    ) -> list[KnowledgeTopic]:
        """Suggest next topics based on completed prerequisites."""
        # Get completed topics
        completed_result = await self.db.execute(
            select(StudentTopicProgress.topic_id).where(
                StudentTopicProgress.student_id == student_id,
                StudentTopicProgress.status == ProgressStatus.COMPLETED
            )
        )
        completed_ids = set(completed_result.scalars().all())
        
        if not completed_ids:
            # Return beginner topics
            result = await self.db.execute(
                select(KnowledgeTopic).where(
                    KnowledgeTopic.is_active == True,
                    KnowledgeTopic.difficulty_level == 1
                ).limit(limit)
            )
            return list(result.scalars().all())
        
        # Find topics where all required prerequisites are completed
        # This is a simplified version - a more complex query would be needed for production
        result = await self.db.execute(
            select(KnowledgeTopic).where(
                KnowledgeTopic.is_active == True,
                ~KnowledgeTopic.id.in_(completed_ids)
            ).order_by(KnowledgeTopic.difficulty_level).limit(limit)
        )
        return list(result.scalars().all())

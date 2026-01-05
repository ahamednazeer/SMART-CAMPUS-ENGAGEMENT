"""
Whiteboard service for collaborative real-time drawing.
"""
import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.whiteboard import (
    WhiteboardSession, WhiteboardParticipant, WhiteboardSnapshot,
    WhiteboardStatus, WhiteboardPermission
)


# Color palette for participant identification
DRAW_COLORS = [
    "#FF5733", "#33FF57", "#3357FF", "#FF33F5", "#F5FF33",
    "#33FFF5", "#FF8033", "#8033FF", "#33FF80", "#FF3380"
]


class WhiteboardService:
    """Service for collaborative whiteboard management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== Session Management ==============
    
    async def create_session(
        self,
        title: str,
        created_by: int,
        description: str | None = None,
        course_id: int | None = None,
        subject_code: str | None = None,
        topic: str | None = None,
        enable_voice: bool = False
    ) -> WhiteboardSession:
        """Create a new whiteboard session."""
        voice_room_url = None
        if enable_voice:
            room_id = f"whiteboard-{uuid.uuid4().hex[:8]}"
            voice_room_url = f"https://meet.jit.si/{room_id}"
        
        session = WhiteboardSession(
            title=title,
            description=description,
            course_id=course_id,
            subject_code=subject_code,
            topic=topic,
            created_by=created_by,
            voice_room_url=voice_room_url
        )
        self.db.add(session)
        await self.db.flush()
        
        # Add creator as participant with EXPLAIN permission
        participant = WhiteboardParticipant(
            session_id=session.id,
            user_id=created_by,
            permission=WhiteboardPermission.EXPLAIN,
            draw_color=DRAW_COLORS[0]
        )
        self.db.add(participant)
        await self.db.flush()
        
        await self.db.refresh(session)
        return session
    
    async def get_session(self, session_id: int) -> WhiteboardSession | None:
        """Get a whiteboard session by ID."""
        result = await self.db.execute(
            select(WhiteboardSession)
            .options(
                selectinload(WhiteboardSession.participants),
                selectinload(WhiteboardSession.snapshots)
            )
            .where(WhiteboardSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_sessions(
        self,
        course_id: int | None = None,
        user_id: int | None = None
    ) -> list[WhiteboardSession]:
        """Get active whiteboard sessions."""
        query = select(WhiteboardSession).where(
            WhiteboardSession.status == WhiteboardStatus.ACTIVE
        )
        
        if course_id:
            query = query.where(WhiteboardSession.course_id == course_id)
        
        if user_id:
            query = query.join(WhiteboardParticipant).where(
                WhiteboardParticipant.user_id == user_id
            )
        
        query = query.order_by(WhiteboardSession.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def close_session(
        self,
        session_id: int,
        final_canvas: dict | None = None
    ) -> WhiteboardSession | None:
        """Close a whiteboard session and save final state."""
        session = await self.get_session(session_id)
        if not session or session.status != WhiteboardStatus.ACTIVE:
            return None
        
        session.status = WhiteboardStatus.CLOSED
        session.is_readonly = True
        session.closed_at = datetime.utcnow()
        
        if final_canvas:
            session.canvas_data = final_canvas
        
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def get_closed_sessions(
        self,
        course_id: int | None = None,
        topic: str | None = None,
        limit: int = 20
    ) -> list[WhiteboardSession]:
        """Get closed sessions for revision."""
        query = select(WhiteboardSession).where(
            WhiteboardSession.status == WhiteboardStatus.CLOSED
        )
        
        if course_id:
            query = query.where(WhiteboardSession.course_id == course_id)
        if topic:
            query = query.where(WhiteboardSession.topic.ilike(f"%{topic}%"))
        
        query = query.order_by(WhiteboardSession.closed_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    # ============== Participant Management ==============
    
    async def invite_participant(
        self,
        session_id: int,
        user_id: int,
        permission: WhiteboardPermission,
        invited_by: int
    ) -> WhiteboardParticipant | None:
        """Invite a user to a whiteboard session."""
        session = await self.get_session(session_id)
        if not session or session.status != WhiteboardStatus.ACTIVE:
            return None
        
        # Check if already a participant
        existing = await self.get_participant(session_id, user_id)
        if existing:
            return existing
        
        # Assign a unique color
        colors_used = [p.draw_color for p in session.participants if p.draw_color]
        available_colors = [c for c in DRAW_COLORS if c not in colors_used]
        draw_color = available_colors[0] if available_colors else DRAW_COLORS[len(session.participants) % len(DRAW_COLORS)]
        
        participant = WhiteboardParticipant(
            session_id=session_id,
            user_id=user_id,
            permission=permission,
            draw_color=draw_color,
            invited_by=invited_by
        )
        self.db.add(participant)
        await self.db.flush()
        await self.db.refresh(participant)
        return participant
    
    async def get_participant(
        self,
        session_id: int,
        user_id: int
    ) -> WhiteboardParticipant | None:
        """Get a participant by session and user."""
        result = await self.db.execute(
            select(WhiteboardParticipant).where(
                WhiteboardParticipant.session_id == session_id,
                WhiteboardParticipant.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def update_permission(
        self,
        session_id: int,
        user_id: int,
        permission: WhiteboardPermission
    ) -> WhiteboardParticipant | None:
        """Update a participant's permission."""
        participant = await self.get_participant(session_id, user_id)
        if not participant:
            return None
        
        participant.permission = permission
        await self.db.flush()
        await self.db.refresh(participant)
        return participant
    
    async def can_draw(self, session_id: int, user_id: int) -> bool:
        """Check if a user can draw on the whiteboard."""
        session = await self.get_session(session_id)
        if not session or session.is_readonly:
            return False
        
        participant = await self.get_participant(session_id, user_id)
        if not participant:
            return False
        
        return participant.permission in [WhiteboardPermission.DRAW, WhiteboardPermission.EXPLAIN]
    
    # ============== Snapshot Management ==============
    
    async def save_snapshot(
        self,
        session_id: int,
        canvas_data: dict,
        name: str | None = None,
        created_by: int | None = None
    ) -> WhiteboardSnapshot:
        """Save a snapshot of the whiteboard state."""
        snapshot = WhiteboardSnapshot(
            session_id=session_id,
            canvas_data=canvas_data,
            name=name,
            created_by=created_by
        )
        self.db.add(snapshot)
        await self.db.flush()
        await self.db.refresh(snapshot)
        return snapshot
    
    async def get_snapshots(self, session_id: int) -> list[WhiteboardSnapshot]:
        """Get all snapshots for a session."""
        result = await self.db.execute(
            select(WhiteboardSnapshot)
            .where(WhiteboardSnapshot.session_id == session_id)
            .order_by(WhiteboardSnapshot.created_at)
        )
        return list(result.scalars().all())
    
    async def get_snapshot(self, snapshot_id: int) -> WhiteboardSnapshot | None:
        """Get a specific snapshot."""
        result = await self.db.execute(
            select(WhiteboardSnapshot).where(WhiteboardSnapshot.id == snapshot_id)
        )
        return result.scalar_one_or_none()

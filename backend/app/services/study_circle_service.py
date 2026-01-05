"""
Study Circle service for Discord-style subject communities.
"""
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.study_circle import (
    StudyCircle, CircleChannel, CircleMember, CircleMessage,
    ChannelType, MemberRole
)
from app.models.course import CourseEnrollment


class StudyCircleService:
    """Service for study circle management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== Circle Management ==============
    
    async def create_circle(
        self,
        name: str,
        created_by: int,
        course_id: int | None = None,
        subject_code: str | None = None,
        semester: int | None = None,
        department: str | None = None,
        description: str | None = None,
        has_voice_room: bool = False
    ) -> StudyCircle:
        """Create a new study circle with default channels."""
        circle = StudyCircle(
            name=name,
            description=description,
            course_id=course_id,
            subject_code=subject_code,
            semester=semester,
            department=department,
            has_voice_room=has_voice_room,
            created_by=created_by
        )
        self.db.add(circle)
        await self.db.flush()
        
        # Create default channels
        default_channels = [
            ("general", "General discussion", ChannelType.TEXT, 0),
            ("announcements", "Important announcements", ChannelType.ANNOUNCEMENT, 1),
            ("doubts", "Ask your doubts here", ChannelType.TEXT, 2),
            ("resources", "Share study resources", ChannelType.TEXT, 3),
        ]
        
        for name, desc, channel_type, pos in default_channels:
            channel = CircleChannel(
                circle_id=circle.id,
                name=name,
                description=desc,
                channel_type=channel_type,
                is_readonly=(channel_type == ChannelType.ANNOUNCEMENT),
                position=pos
            )
            self.db.add(channel)
        
        await self.db.flush()
        await self.db.refresh(circle)
        return circle
    
    async def get_circle(self, circle_id: int) -> StudyCircle | None:
        """Get a study circle by ID."""
        result = await self.db.execute(
            select(StudyCircle)
            .options(selectinload(StudyCircle.channels))
            .where(StudyCircle.id == circle_id)
        )
        return result.scalar_one_or_none()
    
    async def get_circles_by_course(self, course_id: int) -> list[StudyCircle]:
        """Get all circles for a course."""
        result = await self.db.execute(
            select(StudyCircle).where(
                StudyCircle.course_id == course_id,
                StudyCircle.is_active == True
            )
        )
        return list(result.scalars().all())
    
    async def get_student_circles(self, student_id: int) -> list[StudyCircle]:
        """Get all circles a student is a member of."""
        result = await self.db.execute(
            select(StudyCircle)
            .join(CircleMember, CircleMember.circle_id == StudyCircle.id)
            .where(
                CircleMember.user_id == student_id,
                StudyCircle.is_active == True
            )
            .options(selectinload(StudyCircle.channels))
            .order_by(StudyCircle.name)
        )
        return list(result.scalars().all())
    
    async def auto_enroll_student(self, student_id: int) -> list[StudyCircle]:
        """Auto-enroll student in circles based on their course enrollments."""
        # Get student's enrolled courses
        course_result = await self.db.execute(
            select(CourseEnrollment.course_id).where(
                CourseEnrollment.student_id == student_id,
                CourseEnrollment.is_active == True
            )
        )
        course_ids = list(course_result.scalars().all())
        
        # Get circles for those courses
        circles_result = await self.db.execute(
            select(StudyCircle).where(
                StudyCircle.course_id.in_(course_ids),
                StudyCircle.is_active == True
            )
        )
        circles = list(circles_result.scalars().all())
        
        enrolled_circles = []
        for circle in circles:
            # Check if already a member
            existing = await self.get_membership(student_id, circle.id)
            if not existing:
                await self.add_member(circle.id, student_id)
                enrolled_circles.append(circle)
        
        return enrolled_circles
    
    # ============== Channel Management ==============
    
    async def create_channel(
        self,
        circle_id: int,
        name: str,
        description: str | None = None,
        channel_type: ChannelType = ChannelType.TEXT,
        is_readonly: bool = False
    ) -> CircleChannel:
        """Create a new channel in a circle."""
        # Get max position
        result = await self.db.execute(
            select(func.max(CircleChannel.position)).where(
                CircleChannel.circle_id == circle_id
            )
        )
        max_pos = result.scalar() or 0
        
        channel = CircleChannel(
            circle_id=circle_id,
            name=name,
            description=description,
            channel_type=channel_type,
            is_readonly=is_readonly,
            position=max_pos + 1
        )
        self.db.add(channel)
        await self.db.flush()
        await self.db.refresh(channel)
        return channel
    
    async def get_channel(self, channel_id: int) -> CircleChannel | None:
        """Get a channel by ID."""
        result = await self.db.execute(
            select(CircleChannel).where(CircleChannel.id == channel_id)
        )
        return result.scalar_one_or_none()
    
    async def get_circle_channels(self, circle_id: int) -> list[CircleChannel]:
        """Get all channels in a circle."""
        result = await self.db.execute(
            select(CircleChannel)
            .where(CircleChannel.circle_id == circle_id)
            .order_by(CircleChannel.position)
        )
        return list(result.scalars().all())
    
    # ============== Member Management ==============
    
    async def add_member(
        self,
        circle_id: int,
        user_id: int,
        role: MemberRole = MemberRole.MEMBER
    ) -> CircleMember:
        """Add a member to a circle."""
        member = CircleMember(
            circle_id=circle_id,
            user_id=user_id,
            role=role
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member
    
    async def get_membership(
        self,
        user_id: int,
        circle_id: int
    ) -> CircleMember | None:
        """Get a user's membership in a circle."""
        result = await self.db.execute(
            select(CircleMember).where(
                CircleMember.user_id == user_id,
                CircleMember.circle_id == circle_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_circle_members(self, circle_id: int) -> list[CircleMember]:
        """Get all members of a circle."""
        result = await self.db.execute(
            select(CircleMember).where(CircleMember.circle_id == circle_id)
        )
        return list(result.scalars().all())
    
    async def set_moderator(
        self,
        circle_id: int,
        user_id: int,
        is_moderator: bool = True
    ) -> CircleMember | None:
        """Set or remove moderator role for a member."""
        member = await self.get_membership(user_id, circle_id)
        if not member:
            return None
        
        member.role = MemberRole.MODERATOR if is_moderator else MemberRole.MEMBER
        await self.db.flush()
        await self.db.refresh(member)
        return member
    
    async def mute_member(
        self,
        circle_id: int,
        user_id: int,
        duration_minutes: int,
        muted_by: int
    ) -> CircleMember | None:
        """Mute a member for a specified duration."""
        member = await self.get_membership(user_id, circle_id)
        if not member:
            return None
        
        member.is_muted = True
        member.muted_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        member.muted_by = muted_by
        await self.db.flush()
        await self.db.refresh(member)
        return member
    
    async def unmute_member(
        self,
        circle_id: int,
        user_id: int
    ) -> CircleMember | None:
        """Unmute a member."""
        member = await self.get_membership(user_id, circle_id)
        if not member:
            return None
        
        member.is_muted = False
        member.muted_until = None
        member.muted_by = None
        await self.db.flush()
        await self.db.refresh(member)
        return member
    
    async def is_user_muted(self, user_id: int, circle_id: int) -> bool:
        """Check if a user is currently muted."""
        member = await self.get_membership(user_id, circle_id)
        if not member:
            return False
        
        if not member.is_muted:
            return False
        
        # Check if mute duration has expired
        if member.muted_until and member.muted_until < datetime.utcnow():
            member.is_muted = False
            member.muted_until = None
            await self.db.flush()
            return False
        
        return True
    
    # ============== Message Management ==============
    
    async def post_message(
        self,
        channel_id: int,
        user_id: int,
        content: str,
        parent_id: int | None = None
    ) -> CircleMessage:
        """Post a message to a channel."""
        message = CircleMessage(
            channel_id=channel_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id
        )
        self.db.add(message)
        await self.db.flush()
        
        # Update thread count on parent if reply
        if parent_id:
            parent = await self.get_message(parent_id)
            if parent:
                parent.thread_count += 1
                await self.db.flush()
        
        await self.db.refresh(message)
        return message
    
    async def get_message(self, message_id: int) -> CircleMessage | None:
        """Get a message by ID."""
        result = await self.db.execute(
            select(CircleMessage).where(
                CircleMessage.id == message_id,
                CircleMessage.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    async def get_channel_messages(
        self,
        channel_id: int,
        limit: int = 50,
        before_id: int | None = None,
        parent_id: int | None = None
    ) -> list[CircleMessage]:
        """Get messages in a channel with pagination."""
        query = select(CircleMessage).where(
            CircleMessage.channel_id == channel_id,
            CircleMessage.is_deleted == False
        )
        
        # For threads, get only replies to parent
        if parent_id:
            query = query.where(CircleMessage.parent_id == parent_id)
        else:
            # For main channel, get only top-level messages
            query = query.where(CircleMessage.parent_id == None)
        
        if before_id:
            query = query.where(CircleMessage.id < before_id)
        
        query = query.order_by(CircleMessage.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_pinned_messages(self, channel_id: int) -> list[CircleMessage]:
        """Get all pinned messages in a channel."""
        result = await self.db.execute(
            select(CircleMessage).where(
                CircleMessage.channel_id == channel_id,
                CircleMessage.is_pinned == True,
                CircleMessage.is_deleted == False
            ).order_by(CircleMessage.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def pin_message(
        self,
        message_id: int,
        pinned_by: int
    ) -> CircleMessage | None:
        """Pin a message."""
        message = await self.get_message(message_id)
        if not message:
            return None
        
        message.is_pinned = True
        message.pinned_by = pinned_by
        await self.db.flush()
        await self.db.refresh(message)
        return message
    
    async def unpin_message(self, message_id: int) -> CircleMessage | None:
        """Unpin a message."""
        message = await self.get_message(message_id)
        if not message:
            return None
        
        message.is_pinned = False
        message.pinned_by = None
        await self.db.flush()
        await self.db.refresh(message)
        return message
    
    async def delete_message(
        self,
        message_id: int,
        deleted_by: int
    ) -> bool:
        """Soft delete a message."""
        message = await self.get_message(message_id)
        if not message:
            return False
        
        message.is_deleted = True
        message.deleted_by = deleted_by
        await self.db.flush()
        return True
    
    async def search_messages(
        self,
        circle_id: int,
        query: str,
        limit: int = 20
    ) -> list[CircleMessage]:
        """Search messages in a circle."""
        # Get all channels in the circle
        channels = await self.get_circle_channels(circle_id)
        channel_ids = [c.id for c in channels]
        
        result = await self.db.execute(
            select(CircleMessage).where(
                CircleMessage.channel_id.in_(channel_ids),
                CircleMessage.content.ilike(f"%{query}%"),
                CircleMessage.is_deleted == False
            )
            .order_by(CircleMessage.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

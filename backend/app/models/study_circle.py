"""
Study Circle models for Discord-style subject rooms.
"""
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ChannelType(str, enum.Enum):
    """Channel type enumeration."""
    TEXT = "TEXT"
    ANNOUNCEMENT = "ANNOUNCEMENT"


class MemberRole(str, enum.Enum):
    """Member role in a study circle."""
    MEMBER = "MEMBER"
    MODERATOR = "MODERATOR"


class StudyCircle(Base):
    """Study Circle - subject-based community."""
    
    __tablename__ = "study_circles"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(255))  # e.g., "CS201 - Data Structures"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Link to course (optional)
    course_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    # Alternative: direct subject code if no course link
    subject_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Voice room configuration
    has_voice_room: Mapped[bool] = mapped_column(Boolean, default=False)
    voice_room_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Jitsi URL
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    channels = relationship("CircleChannel", back_populates="circle", cascade="all, delete-orphan")
    members = relationship("CircleMember", back_populates="circle", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<StudyCircle {self.name}>"


class CircleChannel(Base):
    """Text channel within a study circle."""
    
    __tablename__ = "circle_channels"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    circle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("study_circles.id", ondelete="CASCADE"), index=True
    )
    
    name: Mapped[str] = mapped_column(String(100))  # e.g., "general", "doubts", "resources"
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    channel_type: Mapped[ChannelType] = mapped_column(
        Enum(ChannelType), default=ChannelType.TEXT
    )
    
    # Only moderators can post in announcement channels
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False)
    
    position: Mapped[int] = mapped_column(Integer, default=0)  # For ordering
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    circle = relationship("StudyCircle", back_populates="channels")
    messages = relationship("CircleMessage", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<CircleChannel {self.name}>"


class CircleMember(Base):
    """Membership in a study circle."""
    
    __tablename__ = "circle_members"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    circle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("study_circles.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.MEMBER)
    
    # Mute status
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    muted_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    circle = relationship("StudyCircle", back_populates="members")
    
    def __repr__(self) -> str:
        return f"<CircleMember user={self.user_id} circle={self.circle_id}>"


class CircleMessage(Base):
    """Message in a study circle channel."""
    
    __tablename__ = "circle_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("circle_channels.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    content: Mapped[str] = mapped_column(Text)
    
    # Thread support
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("circle_messages.id", ondelete="CASCADE"), nullable=True
    )
    thread_count: Mapped[int] = mapped_column(Integer, default=0)  # Cached reply count
    
    # Moderation
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    pinned_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    channel = relationship("CircleChannel", back_populates="messages")
    replies = relationship("CircleMessage", backref="parent", remote_side=[id])
    
    def __repr__(self) -> str:
        return f"<CircleMessage id={self.id} channel={self.channel_id}>"

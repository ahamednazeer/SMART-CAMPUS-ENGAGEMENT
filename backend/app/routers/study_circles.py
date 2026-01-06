"""
Study Circle API endpoints - Discord-style subject communities.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.study_circle import ChannelType, MemberRole
from app.services.study_circle_service import StudyCircleService


router = APIRouter(prefix="/study-circles", tags=["Study Circles"])


# ============== Schemas ==============

class CircleCreate(BaseModel):
    name: str
    description: str | None = None
    course_id: int | None = None
    subject_code: str | None = None
    semester: int | None = None
    department: str | None = None
    has_voice_room: bool = False


class CircleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    course_id: int | None = None
    subject_code: str | None = None
    has_voice_room: bool | None = None
    is_active: bool | None = None


class ChannelCreate(BaseModel):
    name: str
    description: str | None = None
    channel_type: str = "TEXT"
    is_readonly: bool = False


class MessageCreate(BaseModel):
    content: str
    parent_id: int | None = None


class MuteRequest(BaseModel):
    duration_minutes: int = 30


class CircleResponse(BaseModel):
    id: int
    name: str
    description: str | None
    course_id: int | None
    subject_code: str | None
    has_voice_room: bool
    voice_room_url: str | None
    is_active: bool
    
    class Config:
        from_attributes = True


class ChannelResponse(BaseModel):
    id: int
    circle_id: int
    name: str
    description: str | None
    channel_type: str
    is_readonly: bool
    position: int
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    channel_id: int
    user_id: int | None
    content: str
    parent_id: int | None
    thread_count: int
    is_pinned: bool
    created_at: datetime
    user_name: str | None = None
    user_initials: str | None = None
    
    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    id: int
    circle_id: int
    user_id: int
    role: str
    is_muted: bool
    joined_at: datetime
    
    class Config:
        from_attributes = True


# ============== Circle Management ==============

@router.post("", response_model=CircleResponse)
async def create_circle(
    data: CircleCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new study circle (Admin/Staff only)."""
    service = StudyCircleService(db)
    circle = await service.create_circle(
        created_by=current_user.id,
        **data.model_dump()
    )
    return circle


@router.get("", response_model=list[CircleResponse])
async def get_my_circles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all study circles the user is a member of."""
    service = StudyCircleService(db)
    circles = await service.get_student_circles(current_user.id)
    return circles


@router.get("/all", response_model=list[CircleResponse])
async def get_all_circles(
    active_only: bool = True,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Get all study circles (Admin/Staff only)."""
    service = StudyCircleService(db)
    circles = await service.get_all_circles(active_only=active_only)
    return circles


@router.post("/auto-enroll")
async def auto_enroll(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Auto-enroll in circles based on course enrollments."""
    service = StudyCircleService(db)
    circles = await service.auto_enroll_student(current_user.id)
    return {
        "message": f"Enrolled in {len(circles)} circles",
        "circles": [{"id": c.id, "name": c.name} for c in circles]
    }
@router.get("/{circle_id}", response_model=CircleResponse)
async def get_circle(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a study circle by ID."""
    service = StudyCircleService(db)
    
    # Check membership
    member = await service.get_membership(current_user.id, circle_id)
    if not member and current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this circle"
        )
    
    circle = await service.get_circle(circle_id)
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found"
        )
    return circle


@router.put("/{circle_id}", response_model=CircleResponse)
async def update_circle(
    circle_id: int,
    data: CircleUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Update a study circle (Admin/Staff only)."""
    service = StudyCircleService(db)
    circle = await service.update_circle(
        circle_id=circle_id,
        **data.model_dump(exclude_unset=True)
    )
    if not circle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found"
        )
    return circle


@router.delete("/{circle_id}")
async def delete_circle(
    circle_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Delete a study circle (Admin/Staff only)."""
    service = StudyCircleService(db)
    success = await service.delete_circle(circle_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Circle not found"
        )
    return {"message": "Circle deleted successfully"}


# ============== Channel Endpoints ==============

@router.get("/{circle_id}/channels", response_model=list[ChannelResponse])
async def get_channels(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all channels in a circle."""
    service = StudyCircleService(db)
    channels = await service.get_circle_channels(circle_id)
    return channels


@router.post("/{circle_id}/channels", response_model=ChannelResponse)
async def create_channel(
    circle_id: int,
    data: ChannelCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new channel (Admin/Staff only)."""
    service = StudyCircleService(db)
    channel_type = ChannelType.ANNOUNCEMENT if data.channel_type == "ANNOUNCEMENT" else ChannelType.TEXT
    channel = await service.create_channel(
        circle_id=circle_id,
        name=data.name,
        description=data.description,
        channel_type=channel_type,
        is_readonly=data.is_readonly
    )
    return channel


# ============== Message Endpoints ==============

@router.get("/{circle_id}/channels/{channel_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    circle_id: int,
    channel_id: int,
    limit: int = 50,
    before_id: int | None = None,
    parent_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages in a channel."""
    service = StudyCircleService(db)
    messages = await service.get_channel_messages(
        channel_id=channel_id,
        limit=limit,
        before_id=before_id,
        parent_id=parent_id
    )
    return messages


@router.get("/{circle_id}/channels/{channel_id}/pinned", response_model=list[MessageResponse])
async def get_pinned_messages(
    circle_id: int,
    channel_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pinned messages in a channel."""
    service = StudyCircleService(db)
    messages = await service.get_pinned_messages(channel_id)
    return messages


@router.post("/{circle_id}/channels/{channel_id}/messages", response_model=MessageResponse)
async def post_message(
    circle_id: int,
    channel_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Post a message to a channel."""
    service = StudyCircleService(db)
    
    # Check if muted
    if await service.is_user_muted(current_user.id, circle_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are muted in this circle"
        )
    
    # Check channel readonly
    channel = await service.get_channel(channel_id)
    if channel and channel.is_readonly:
        member = await service.get_membership(current_user.id, circle_id)
        if not member or member.role != MemberRole.MODERATOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is a read-only channel"
            )
    
    message = await service.post_message(
        channel_id=channel_id,
        user_id=current_user.id,
        content=data.content,
        parent_id=data.parent_id
    )
    return message


@router.post("/{circle_id}/messages/{message_id}/pin")
async def pin_message(
    circle_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pin a message (Moderator only)."""
    service = StudyCircleService(db)
    
    # Check moderator role
    member = await service.get_membership(current_user.id, circle_id)
    if not member or member.role != MemberRole.MODERATOR:
        if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only moderators can pin messages"
            )
    
    message = await service.pin_message(message_id, current_user.id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return {"message": "Message pinned"}


@router.delete("/{circle_id}/messages/{message_id}/pin")
async def unpin_message(
    circle_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unpin a message (Moderator only)."""
    service = StudyCircleService(db)
    message = await service.unpin_message(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return {"message": "Message unpinned"}


@router.delete("/{circle_id}/messages/{message_id}")
async def delete_message(
    circle_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a message (own message or moderator)."""
    service = StudyCircleService(db)
    
    message = await service.get_message(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check permission
    if message.user_id != current_user.id:
        member = await service.get_membership(current_user.id, circle_id)
        if not member or member.role != MemberRole.MODERATOR:
            if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete this message"
                )
    
    await service.delete_message(message_id, current_user.id)
    return {"message": "Message deleted"}


# ============== Member Management ==============

@router.get("/{circle_id}/members", response_model=list[MemberResponse])
async def get_members(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all members of a circle."""
    service = StudyCircleService(db)
    members = await service.get_circle_members(circle_id)
    return members


@router.post("/{circle_id}/members/{user_id}/mute")
async def mute_member(
    circle_id: int,
    user_id: int,
    data: MuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mute a member (Moderator only)."""
    service = StudyCircleService(db)
    
    # Check moderator role
    member = await service.get_membership(current_user.id, circle_id)
    if not member or member.role != MemberRole.MODERATOR:
        if current_user.role not in [UserRole.ADMIN, UserRole.STAFF]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only moderators can mute members"
            )
    
    muted = await service.mute_member(
        circle_id=circle_id,
        user_id=user_id,
        duration_minutes=data.duration_minutes,
        muted_by=current_user.id
    )
    if not muted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return {"message": f"Member muted for {data.duration_minutes} minutes"}


@router.delete("/{circle_id}/members/{user_id}/mute")
async def unmute_member(
    circle_id: int,
    user_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Unmute a member (Admin/Staff only)."""
    service = StudyCircleService(db)
    await service.unmute_member(circle_id, user_id)
    return {"message": "Member unmuted"}


@router.post("/{circle_id}/members/{user_id}/moderator")
async def set_moderator(
    circle_id: int,
    user_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Make a member a moderator (Admin/Staff only)."""
    service = StudyCircleService(db)
    member = await service.set_moderator(circle_id, user_id, True)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return {"message": "Member promoted to moderator"}


# ============== Search ==============

@router.get("/{circle_id}/search")
async def search_messages(
    circle_id: int,
    q: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search messages in a circle."""
    service = StudyCircleService(db)
    messages = await service.search_messages(circle_id, q, limit)
    return {"results": messages, "count": len(messages)}

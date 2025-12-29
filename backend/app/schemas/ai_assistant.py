"""Schemas for AI Assistant module."""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class AIModule(str, Enum):
    """Modules where AI can operate."""
    DASHBOARD = "dashboard"
    READING = "reading"
    QUIZ = "quiz"
    ATTENDANCE = "attendance"
    HOSTEL = "hostel"
    OUTPASS = "outpass"
    QUERIES = "queries"
    COMPLAINTS = "complaints"
    PROFILE = "profile"
    CERTIFICATES = "certificates"
    STREAK = "streak"
    FACULTY = "faculty"
    NOTIFICATIONS = "notifications"
    SETTINGS = "settings"


class ActionChip(BaseModel):
    """Action chip for navigation suggestions."""
    label: str
    url: str


class ChatMessage(BaseModel):
    """A single message in the chat history."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request schema for AI chat."""
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[ChatMessage] = []
    module: AIModule = AIModule.DASHBOARD
    pdf_id: Optional[int] = None
    context: Optional[str] = None  # Additional context like page content


class ChatResponse(BaseModel):
    """Response schema for AI chat."""
    response: str
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    action_chips: List[ActionChip] = []


class AIContextRequest(BaseModel):
    """Request to check AI context for a module."""
    module: AIModule


class AIContextResponse(BaseModel):
    """Response with AI availability status for a module."""
    is_available: bool
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    module: AIModule
    can_explain_pdf: bool = False
    active_pdf_id: Optional[int] = None


class QuizStatusResponse(BaseModel):
    """Response for quiz mode status check."""
    has_active_quiz: bool
    quiz_id: Optional[int] = None
    ai_blocked: bool = False
    message: str = ""

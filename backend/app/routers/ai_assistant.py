"""Router for AI Assistant endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.services.ai_assistant_service import AIAssistantService
from app.schemas.ai_assistant import (
    AIModule, ChatRequest, ChatResponse, 
    AIContextResponse, QuizStatusResponse
)
from app.services.stt_service import STTService


router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def require_student(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Require user to be a student (STUDENT, HOSTELLER, or DAY_SCHOLAR)."""
    allowed_roles = {UserRole.STUDENT, UserRole.HOSTELLER, UserRole.DAY_SCHOLAR}
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI Assistant is only available for students"
        )
    return current_user


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_student)]
):
    """
    Send a message to the AI Assistant.
    
    The AI will respond based on the current module context and user permissions.
    AI is blocked during active quizzes to maintain academic integrity.
    """
    response = await AIAssistantService.chat(
        user=current_user,
        message=request.message,
        module=request.module,
        db=db,
        history=request.history,
        pdf_id=request.pdf_id,
        additional_context=request.context
    )
    
    if response.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=response.blocked_reason or "AI Assistant is not available"
        )
    
    return response


@router.get("/context/{module}", response_model=AIContextResponse)
async def get_context(
    module: AIModule,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_student)],
    pdf_id: int | None = None
):
    """
    Get AI Assistant availability and context for a specific module.
    
    Use this to determine if the AI should be shown/hidden on a page.
    """
    return await AIAssistantService.get_context(
        user=current_user,
        module=module,
        db=db,
        pdf_id=pdf_id
    )


@router.get("/quiz-status", response_model=QuizStatusResponse)
async def get_quiz_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_student)]
):
    """
    Check if the user has an active quiz attempt.
    
    If a quiz is active, AI Assistant should be completely hidden.
    """
    return await AIAssistantService.get_quiz_status(
        user=current_user,
        db=db
    )


@router.get("/health")
async def ai_health_check():
    """
    Check if AI service is healthy and available.
    
    Returns the health status and cache statistics.
    Can be called without authentication for monitoring.
    """
    is_healthy = await AIAssistantService._check_ai_health()
    cache_size = len(AIAssistantService._response_cache.cache)
    
    return {
        "healthy": is_healthy,
        "cache_size": cache_size,
        "cache_max_size": AIAssistantService._response_cache.max_size,
        "cache_ttl_seconds": AIAssistantService._response_cache.ttl
    }


@router.post("/explain-pdf", response_model=ChatResponse)
async def explain_pdf(
    pdf_id: int,
    question: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_student)]
):
    """
    Ask the AI to explain content from a specific PDF.
    
    This endpoint is specifically for the reading module.
    The AI will use the PDF content to provide explanations.
    """
    response = await AIAssistantService.explain_pdf_content(
        user=current_user,
        pdf_id=pdf_id,
        question=question,
        db=db
    )
    
    if response.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=response.blocked_reason or "AI Assistant is not available"
        )
    
    return response


@router.post("/classify-intent")
async def classify_intent(
    message: str,
    current_user: Annotated[User, Depends(require_student)]
):
    """
    Classify user intent to guide them to the correct module.
    
    Returns whether the message seems like a QUERY, COMPLAINT, or GENERAL question.
    """
    intent = await AIAssistantService.classify_intent(message)
    return {"intent": intent}


@router.post("/stt")
async def speech_to_text(
    audio: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(require_student)]
):
    """
    Transcribe uploaded audio to text using a local Whisper model.
    
    Supports offline voice input. Accepts audio files (WebM/WAV).
    """
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file"
            )
        
        transcript = await STTService.transcribe(audio_bytes)
        return {"text": transcript}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )

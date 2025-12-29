from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.quiz_service import QuizService
from app.services.ai_service import AIQuizService
from app.repositories.pdf_repository import PDFRepository
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizOut, QuizFullOut, QuizStudentOut,
    AttemptSubmit, AttemptOut, AttemptResultOut
)

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


class AIGenerateRequest(BaseModel):
    """Request for AI quiz generation."""
    pdf_id: int
    num_questions: int = 5
    title: str | None = None


@router.post("/generate", status_code=status.HTTP_200_OK)
async def generate_quiz_from_pdf(
    data: AIGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Generate quiz questions from PDF using AI (admin only)."""
    # Get PDF
    pdf_repo = PDFRepository(db)
    pdf = await pdf_repo.get_by_id(data.pdf_id)
    if pdf is None:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    try:
        # Extract text from PDF
        text = await AIQuizService.extract_text_from_pdf(pdf.file_path)
        
        if not text or len(text.strip()) < 100:
            raise HTTPException(
                status_code=400, 
                detail="PDF has insufficient text content for quiz generation"
            )
        
        # Generate quiz using AI
        title = data.title or f"Quiz: {pdf.title}"
        quiz_data = await AIQuizService.generate_quiz_from_text(
            text=text,
            num_questions=data.num_questions,
            title=title
        )
        
        # Add pdf_id to response
        quiz_data["pdf_id"] = data.pdf_id
        
        return quiz_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Quiz generation error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("", response_model=QuizFullOut, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    data: QuizCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)]
):
    """Create a new quiz (admin only)."""
    service = QuizService(db)
    return await service.create_quiz(data, current_user.id)


@router.get("/pdf/{pdf_id}", response_model=list[QuizOut])
async def get_pdf_quizzes(
    pdf_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)]
):
    """Get all quizzes for a PDF."""
    service = QuizService(db)
    return await service.get_pdf_quizzes(pdf_id)


@router.get("/{quiz_id}", response_model=QuizFullOut)
async def get_quiz(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get quiz with questions (admin only)."""
    service = QuizService(db)
    try:
        return await service.get_quiz_full(quiz_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{quiz_id}/student", response_model=QuizStudentOut)
async def get_quiz_for_student(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get quiz for student (without correct answers)."""
    service = QuizService(db)
    try:
        return await service.get_quiz_for_student(quiz_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{quiz_id}", response_model=QuizOut)
async def update_quiz(
    quiz_id: int,
    data: QuizUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Update a quiz (admin only)."""
    service = QuizService(db)
    try:
        return await service.update_quiz(quiz_id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{quiz_id}/publish", response_model=QuizOut)
async def publish_quiz(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Publish a quiz (admin only)."""
    service = QuizService(db)
    try:
        return await service.publish_quiz(quiz_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Delete a quiz (admin only)."""
    service = QuizService(db)
    try:
        await service.delete_quiz(quiz_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{quiz_id}/start", response_model=AttemptOut)
async def start_attempt(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Start a quiz attempt."""
    service = QuizService(db)
    try:
        return await service.start_attempt(current_user.id, quiz_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/submit", response_model=AttemptResultOut)
async def submit_attempt(
    data: AttemptSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Submit quiz answers."""
    service = QuizService(db)
    try:
        return await service.submit_attempt(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my/attempts", response_model=list[AttemptOut])
async def get_my_attempts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get current user's quiz attempts."""
    service = QuizService(db)
    return await service.get_student_attempts(current_user.id)


@router.get("/admin/results", response_model=list[AttemptOut])
async def get_all_results(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get all quiz attempts (admin only)."""
    service = QuizService(db)
    return await service.get_all_attempts()


@router.get("/admin/results/{quiz_id}", response_model=list[AttemptOut])
async def get_quiz_results(
    quiz_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)]
):
    """Get all attempts for a specific quiz (admin only)."""
    service = QuizService(db)
    return await service.get_quiz_attempts(quiz_id)

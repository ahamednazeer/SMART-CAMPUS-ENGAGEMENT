"""
Flashcard Battle API endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.flashcard import BattleType
from app.services.flashcard_service import FlashcardService


router = APIRouter(prefix="/flashcards", tags=["Flashcard Battles"])


# ============== Schemas ==============

class FlashcardSetCreate(BaseModel):
    title: str
    description: str | None = None
    course_id: int | None = None
    subject_code: str | None = None
    topic: str | None = None


class FlashcardCreate(BaseModel):
    question: str
    answer: str
    hint: str | None = None
    options: list[str] | None = None
    correct_option: int | None = None
    difficulty: int = 1


class BulkFlashcardCreate(BaseModel):
    cards: list[FlashcardCreate]


class BattleCreate(BaseModel):
    set_id: int
    battle_type: str = "PUBLIC"  # FRIEND, RANDOM, PUBLIC
    num_questions: int = 10
    time_per_question: int = 15


class AnswerSubmit(BaseModel):
    question_index: int
    answer: int
    time_ms: int


class FlashcardSetResponse(BaseModel):
    id: int
    title: str
    description: str | None
    course_id: int | None
    subject_code: str | None
    topic: str | None
    total_cards: int
    times_played: int
    is_published: bool
    is_ai_generated: bool
    
    class Config:
        from_attributes = True


class FlashcardResponse(BaseModel):
    id: int
    set_id: int
    question: str
    answer: str
    hint: str | None
    options: list | None
    correct_option: int | None
    difficulty: int
    
    class Config:
        from_attributes = True


class BattleResponse(BaseModel):
    id: int
    set_id: int
    battle_type: str
    status: str
    num_questions: int
    time_per_question: int
    current_question: int
    started_at: datetime | None
    ended_at: datetime | None
    
    class Config:
        from_attributes = True


# ============== Flashcard Set Endpoints ==============

@router.post("/sets", response_model=FlashcardSetResponse)
async def create_set(
    data: FlashcardSetCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Create a new flashcard set (Admin/Staff only)."""
    service = FlashcardService(db)
    flashcard_set = await service.create_set(
        created_by=current_user.id,
        **data.model_dump()
    )
    return flashcard_set


@router.get("/sets", response_model=list[FlashcardSetResponse])
async def get_sets(
    course_id: int | None = None,
    subject_code: str | None = None,
    topic: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all published flashcard sets."""
    service = FlashcardService(db)
    sets = await service.get_published_sets(
        course_id=course_id,
        subject_code=subject_code,
        topic=topic
    )
    return sets


@router.get("/sets/{set_id}", response_model=FlashcardSetResponse)
async def get_set(
    set_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a flashcard set by ID."""
    service = FlashcardService(db)
    flashcard_set = await service.get_set(set_id)
    if not flashcard_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found"
        )
    return flashcard_set


@router.post("/sets/{set_id}/publish")
async def publish_set(
    set_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Publish a flashcard set."""
    service = FlashcardService(db)
    flashcard_set = await service.publish_set(set_id)
    if not flashcard_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found"
        )
    return {"message": "Set published"}


# ============== Flashcard Endpoints ==============

@router.post("/sets/{set_id}/cards", response_model=FlashcardResponse)
async def add_card(
    set_id: int,
    data: FlashcardCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Add a flashcard to a set."""
    service = FlashcardService(db)
    card = await service.add_card(set_id=set_id, **data.model_dump())
    return card


@router.post("/sets/{set_id}/cards/bulk")
async def bulk_add_cards(
    set_id: int,
    data: BulkFlashcardCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.STAFF])),
    db: AsyncSession = Depends(get_db)
):
    """Add multiple flashcards to a set."""
    service = FlashcardService(db)
    cards = await service.bulk_add_cards(
        set_id=set_id,
        cards=[c.model_dump() for c in data.cards]
    )
    return {"message": f"Added {len(cards)} cards", "count": len(cards)}


@router.get("/sets/{set_id}/cards", response_model=list[FlashcardResponse])
async def get_cards(
    set_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all cards in a set."""
    service = FlashcardService(db)
    cards = await service.get_set_cards(set_id)
    return cards


# ============== Battle Endpoints ==============

@router.post("/battles", response_model=BattleResponse)
async def create_battle(
    data: BattleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new battle."""
    service = FlashcardService(db)
    
    battle_type = BattleType.PUBLIC
    if data.battle_type == "FRIEND":
        battle_type = BattleType.FRIEND
    elif data.battle_type == "RANDOM":
        battle_type = BattleType.RANDOM
    
    battle = await service.create_battle(
        set_id=data.set_id,
        created_by=current_user.id,
        battle_type=battle_type,
        num_questions=data.num_questions,
        time_per_question=data.time_per_question
    )
    return battle


@router.get("/battles/find-random")
async def find_random_battle(
    set_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Find a random waiting battle to join."""
    service = FlashcardService(db)
    battle = await service.find_random_battle(current_user.id, set_id)
    if not battle:
        return {"message": "No battles available", "battle": None}
    return {"battle_id": battle.id}


@router.post("/battles/{battle_id}/join")
async def join_battle(
    battle_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join an existing battle."""
    service = FlashcardService(db)
    participant = await service.join_battle(battle_id, current_user.id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join this battle"
        )
    return {"message": "Joined battle", "participant_id": participant.id}


@router.post("/battles/{battle_id}/start")
async def start_battle(
    battle_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a battle."""
    service = FlashcardService(db)
    battle = await service.start_battle(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start this battle"
        )
    return {"message": "Battle started", "started_at": battle.started_at}


@router.get("/battles/{battle_id}", response_model=BattleResponse)
async def get_battle(
    battle_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get battle details."""
    service = FlashcardService(db)
    battle = await service.get_battle(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )
    return battle


@router.get("/battles/{battle_id}/question/{index}")
async def get_battle_question(
    battle_id: int,
    index: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific question in the battle."""
    service = FlashcardService(db)
    battle = await service.get_battle(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Battle not found"
        )
    
    if index >= len(battle.question_order):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question index"
        )
    
    card_id = battle.question_order[index]
    cards = await service.get_set_cards(battle.set_id)
    card = next((c for c in cards if c.id == card_id), None)
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Don't expose the correct answer
    return {
        "index": index,
        "total": len(battle.question_order),
        "question": card.question,
        "options": card.options,
        "hint": card.hint,
        "time_limit": battle.time_per_question
    }


@router.post("/battles/{battle_id}/answer")
async def submit_answer(
    battle_id: int,
    data: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit an answer for a battle question."""
    service = FlashcardService(db)
    result = await service.submit_answer(
        battle_id=battle_id,
        user_id=current_user.id,
        question_index=data.question_index,
        answer=data.answer,
        time_ms=data.time_ms
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.post("/battles/{battle_id}/end")
async def end_battle(
    battle_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """End a battle and get results."""
    service = FlashcardService(db)
    battle = await service.end_battle(battle_id)
    if not battle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot end this battle"
        )
    
    # Get participant scores
    participants = [
        {
            "user_id": p.user_id,
            "score": p.score,
            "correct_answers": p.correct_answers,
            "is_winner": p.is_winner
        }
        for p in battle.participants
    ]
    
    return {
        "message": "Battle ended",
        "participants": participants
    }


# ============== Leaderboard & Stats ==============

@router.get("/leaderboard")
async def get_leaderboard(
    period: str = "WEEKLY",
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the flashcard leaderboard."""
    service = FlashcardService(db)
    leaderboard = await service.get_leaderboard(period, limit)
    return {
        "period": period,
        "entries": [
            {
                "user_id": e.user_id,
                "total_battles": e.total_battles,
                "wins": e.wins,
                "total_score": e.total_score,
                "rank": e.rank
            }
            for e in leaderboard
        ]
    }


@router.get("/my-stats")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's battle statistics."""
    service = FlashcardService(db)
    stats = await service.get_user_battle_stats(current_user.id)
    return stats

"""
Flashcard service for competitive micro-learning battles.
"""
import random
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.flashcard import (
    FlashcardSet, Flashcard, FlashcardBattle, BattleParticipant, FlashcardLeaderboard,
    BattleType, BattleStatus
)


class FlashcardService:
    """Service for flashcard and battle management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ============== Flashcard Set Management ==============
    
    async def create_set(
        self,
        title: str,
        created_by: int,
        description: str | None = None,
        course_id: int | None = None,
        subject_code: str | None = None,
        topic: str | None = None,
        is_ai_generated: bool = False
    ) -> FlashcardSet:
        """Create a new flashcard set."""
        flashcard_set = FlashcardSet(
            title=title,
            description=description,
            course_id=course_id,
            subject_code=subject_code,
            topic=topic,
            created_by=created_by,
            is_ai_generated=is_ai_generated
        )
        self.db.add(flashcard_set)
        await self.db.flush()
        await self.db.refresh(flashcard_set)
        return flashcard_set
    
    async def get_set(self, set_id: int) -> FlashcardSet | None:
        """Get a flashcard set by ID with cards."""
        result = await self.db.execute(
            select(FlashcardSet)
            .options(selectinload(FlashcardSet.cards))
            .where(FlashcardSet.id == set_id)
        )
        return result.scalar_one_or_none()
    
    async def get_published_sets(
        self,
        course_id: int | None = None,
        subject_code: str | None = None,
        topic: str | None = None
    ) -> list[FlashcardSet]:
        """Get all published flashcard sets with optional filters."""
        query = select(FlashcardSet).where(FlashcardSet.is_published == True)
        
        if course_id:
            query = query.where(FlashcardSet.course_id == course_id)
        if subject_code:
            query = query.where(FlashcardSet.subject_code == subject_code)
        if topic:
            query = query.where(FlashcardSet.topic.ilike(f"%{topic}%"))
        
        query = query.order_by(FlashcardSet.times_played.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def publish_set(self, set_id: int) -> FlashcardSet | None:
        """Publish a flashcard set."""
        flashcard_set = await self.get_set(set_id)
        if not flashcard_set:
            return None
        
        flashcard_set.is_published = True
        await self.db.flush()
        await self.db.refresh(flashcard_set)
        return flashcard_set
    
    # ============== Flashcard Management ==============
    
    async def add_card(
        self,
        set_id: int,
        question: str,
        answer: str,
        hint: str | None = None,
        options: list[str] | None = None,
        correct_option: int | None = None,
        difficulty: int = 1
    ) -> Flashcard:
        """Add a flashcard to a set."""
        # Get max order
        result = await self.db.execute(
            select(func.max(Flashcard.order)).where(Flashcard.set_id == set_id)
        )
        max_order = result.scalar() or 0
        
        card = Flashcard(
            set_id=set_id,
            question=question,
            answer=answer,
            hint=hint,
            options=options,
            correct_option=correct_option,
            difficulty=difficulty,
            order=max_order + 1
        )
        self.db.add(card)
        await self.db.flush()
        
        # Update card count
        flashcard_set = await self.get_set(set_id)
        if flashcard_set:
            flashcard_set.total_cards += 1
            await self.db.flush()
        
        await self.db.refresh(card)
        return card
    
    async def bulk_add_cards(
        self,
        set_id: int,
        cards: list[dict]
    ) -> list[Flashcard]:
        """Add multiple flashcards to a set."""
        result = await self.db.execute(
            select(func.max(Flashcard.order)).where(Flashcard.set_id == set_id)
        )
        max_order = result.scalar() or 0
        
        created_cards = []
        for i, card_data in enumerate(cards):
            card = Flashcard(
                set_id=set_id,
                question=card_data["question"],
                answer=card_data["answer"],
                hint=card_data.get("hint"),
                options=card_data.get("options"),
                correct_option=card_data.get("correct_option"),
                difficulty=card_data.get("difficulty", 1),
                order=max_order + i + 1
            )
            self.db.add(card)
            created_cards.append(card)
        
        await self.db.flush()
        
        # Update card count
        flashcard_set = await self.get_set(set_id)
        if flashcard_set:
            flashcard_set.total_cards += len(cards)
            await self.db.flush()
        
        return created_cards
    
    async def get_set_cards(self, set_id: int) -> list[Flashcard]:
        """Get all cards in a set."""
        result = await self.db.execute(
            select(Flashcard)
            .where(Flashcard.set_id == set_id)
            .order_by(Flashcard.order)
        )
        return list(result.scalars().all())
    
    # ============== Battle Management ==============
    
    async def create_battle(
        self,
        set_id: int,
        created_by: int,
        battle_type: BattleType,
        num_questions: int = 10,
        time_per_question: int = 15
    ) -> FlashcardBattle:
        """Create a new flashcard battle."""
        # Get cards from set
        cards = await self.get_set_cards(set_id)
        
        # Select and shuffle question order
        card_ids = [c.id for c in cards]
        if len(card_ids) > num_questions:
            card_ids = random.sample(card_ids, num_questions)
        random.shuffle(card_ids)
        
        battle = FlashcardBattle(
            set_id=set_id,
            battle_type=battle_type,
            status=BattleStatus.WAITING,
            num_questions=min(num_questions, len(card_ids)),
            time_per_question=time_per_question,
            question_order=card_ids,
            created_by=created_by
        )
        self.db.add(battle)
        await self.db.flush()
        
        # Add creator as participant
        participant = BattleParticipant(
            battle_id=battle.id,
            user_id=created_by
        )
        self.db.add(participant)
        await self.db.flush()
        
        await self.db.refresh(battle)
        return battle
    
    async def get_battle(self, battle_id: int) -> FlashcardBattle | None:
        """Get a battle by ID."""
        result = await self.db.execute(
            select(FlashcardBattle)
            .options(selectinload(FlashcardBattle.participants))
            .where(FlashcardBattle.id == battle_id)
        )
        return result.scalar_one_or_none()
    
    async def join_battle(
        self,
        battle_id: int,
        user_id: int
    ) -> BattleParticipant | None:
        """Join an existing battle."""
        battle = await self.get_battle(battle_id)
        if not battle or battle.status != BattleStatus.WAITING:
            return None
        
        # Check if already joined
        existing = await self.get_participant(battle_id, user_id)
        if existing:
            return existing
        
        participant = BattleParticipant(
            battle_id=battle_id,
            user_id=user_id
        )
        self.db.add(participant)
        await self.db.flush()
        await self.db.refresh(participant)
        return participant
    
    async def find_random_battle(
        self,
        user_id: int,
        set_id: int | None = None
    ) -> FlashcardBattle | None:
        """Find a random waiting battle to join."""
        query = select(FlashcardBattle).where(
            FlashcardBattle.status == BattleStatus.WAITING,
            FlashcardBattle.created_by != user_id
        )
        
        if set_id:
            query = query.where(FlashcardBattle.set_id == set_id)
        
        # Get battles created in the last 5 minutes
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        query = query.where(FlashcardBattle.created_at >= cutoff)
        
        result = await self.db.execute(query)
        battles = list(result.scalars().all())
        
        if battles:
            return random.choice(battles)
        return None
    
    async def start_battle(self, battle_id: int) -> FlashcardBattle | None:
        """Start a battle."""
        battle = await self.get_battle(battle_id)
        if not battle or battle.status != BattleStatus.WAITING:
            return None
        
        battle.status = BattleStatus.IN_PROGRESS
        battle.started_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(battle)
        return battle
    
    async def get_participant(
        self,
        battle_id: int,
        user_id: int
    ) -> BattleParticipant | None:
        """Get a participant in a battle."""
        result = await self.db.execute(
            select(BattleParticipant).where(
                BattleParticipant.battle_id == battle_id,
                BattleParticipant.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def submit_answer(
        self,
        battle_id: int,
        user_id: int,
        question_index: int,
        answer: int,
        time_ms: int
    ) -> dict:
        """Submit an answer for a battle question."""
        battle = await self.get_battle(battle_id)
        if not battle or battle.status != BattleStatus.IN_PROGRESS:
            return {"error": "Battle not in progress"}
        
        participant = await self.get_participant(battle_id, user_id)
        if not participant:
            return {"error": "Not a participant"}
        
        # Get the card for this question
        card_id = battle.question_order[question_index]
        result = await self.db.execute(
            select(Flashcard).where(Flashcard.id == card_id)
        )
        card = result.scalar_one_or_none()
        
        if not card:
            return {"error": "Question not found"}
        
        # Check answer
        is_correct = (card.correct_option == answer)
        
        # Update participant answers
        answers = participant.answers or {}
        answers[str(question_index)] = {
            "answer": answer,
            "correct": is_correct,
            "time_ms": time_ms
        }
        participant.answers = answers
        
        if is_correct:
            participant.correct_answers += 1
            # Score based on speed (faster = more points)
            speed_bonus = max(0, 1000 - time_ms) // 100
            participant.score += 10 + speed_bonus
        
        participant.total_time_ms += time_ms
        
        await self.db.flush()
        
        return {
            "is_correct": is_correct,
            "correct_answer": card.correct_option,
            "score_earned": 10 + max(0, 1000 - time_ms) // 100 if is_correct else 0
        }
    
    async def end_battle(self, battle_id: int) -> FlashcardBattle | None:
        """End a battle and determine winner."""
        battle = await self.get_battle(battle_id)
        if not battle:
            return None
        
        battle.status = BattleStatus.COMPLETED
        battle.ended_at = datetime.utcnow()
        
        # Determine winner
        participants = battle.participants
        if len(participants) >= 2:
            sorted_participants = sorted(
                participants,
                key=lambda p: (p.score, -p.total_time_ms),
                reverse=True
            )
            sorted_participants[0].is_winner = True
            for p in sorted_participants[1:]:
                p.is_winner = False
        
        # Update set play count
        flashcard_set = await self.get_set(battle.set_id)
        if flashcard_set:
            flashcard_set.times_played += 1
        
        await self.db.flush()
        await self.db.refresh(battle)
        return battle
    
    # ============== Leaderboard ==============
    
    async def get_leaderboard(
        self,
        period_type: str = "WEEKLY",
        limit: int = 10
    ) -> list[FlashcardLeaderboard]:
        """Get the leaderboard for a period."""
        result = await self.db.execute(
            select(FlashcardLeaderboard)
            .where(FlashcardLeaderboard.period_type == period_type)
            .order_by(FlashcardLeaderboard.rank)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_user_leaderboard(
        self,
        user_id: int,
        score: int,
        won: bool
    ):
        """Update a user's leaderboard entry."""
        now = datetime.utcnow()
        
        # Get or create weekly leaderboard entry
        result = await self.db.execute(
            select(FlashcardLeaderboard).where(
                FlashcardLeaderboard.user_id == user_id,
                FlashcardLeaderboard.period_type == "WEEKLY"
            )
        )
        entry = result.scalar_one_or_none()
        
        if not entry:
            entry = FlashcardLeaderboard(
                user_id=user_id,
                period_type="WEEKLY",
                period_start=now - timedelta(days=now.weekday())
            )
            self.db.add(entry)
        
        entry.total_battles += 1
        entry.total_score += score
        if won:
            entry.wins += 1
        
        await self.db.flush()
    
    async def get_user_battle_stats(self, user_id: int) -> dict:
        """Get a user's battle statistics."""
        # Total battles
        result = await self.db.execute(
            select(func.count(BattleParticipant.id)).where(
                BattleParticipant.user_id == user_id
            )
        )
        total_battles = result.scalar() or 0
        
        # Wins
        result = await self.db.execute(
            select(func.count(BattleParticipant.id)).where(
                BattleParticipant.user_id == user_id,
                BattleParticipant.is_winner == True
            )
        )
        wins = result.scalar() or 0
        
        # Average score
        result = await self.db.execute(
            select(func.avg(BattleParticipant.score)).where(
                BattleParticipant.user_id == user_id
            )
        )
        avg_score = result.scalar() or 0
        
        return {
            "total_battles": total_battles,
            "wins": wins,
            "losses": total_battles - wins,
            "win_rate": (wins / total_battles * 100) if total_battles > 0 else 0,
            "average_score": round(avg_score, 1)
        }

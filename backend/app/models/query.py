"""Query model for student informational queries."""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class QueryCategory(str, PyEnum):
    """Categories for student queries."""
    RULES = "RULES"
    TIMINGS = "TIMINGS"
    POLICY = "POLICY"
    OTHERS = "OTHERS"


class QueryStatus(str, PyEnum):
    """Status of a query."""
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class Query(Base):
    """Student query for information about rules, policies, timings, etc."""
    
    __tablename__ = "queries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    
    # Student type for routing (HOSTELLER or DAY_SCHOLAR)
    student_type: Mapped[str] = mapped_column(String(20))
    
    # Query details
    category: Mapped[str] = mapped_column(
        Enum(QueryCategory, name="querycategory", create_type=True),
        default=QueryCategory.OTHERS
    )
    description: Mapped[str] = mapped_column(Text)
    
    # Status
    status: Mapped[str] = mapped_column(
        Enum(QueryStatus, name="querystatus", create_type=True),
        default=QueryStatus.OPEN
    )
    
    # Response from admin/warden
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id], backref="queries")
    responder = relationship("User", foreign_keys=[responded_by])
    
    def __repr__(self) -> str:
        return f"<Query {self.id} - {self.category} - {self.status}>"

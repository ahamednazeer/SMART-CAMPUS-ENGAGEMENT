from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking all user actions."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    action: Mapped[str] = mapped_column(String(50))  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type: Mapped[str] = mapped_column(String(50))  # user, pdf, quiz, streak, etc.
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.resource_type}>"

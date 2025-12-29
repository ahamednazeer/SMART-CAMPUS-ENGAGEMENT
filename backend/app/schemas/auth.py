from pydantic import BaseModel, EmailStr
from app.models.user import UserRole, StudentCategory


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    """User response schema (public data)."""
    id: int
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    student_category: StudentCategory | None = None
    register_number: str | None = None
    department: str | None = None
    batch: str | None = None
    is_active: bool
    
    class Config:
        from_attributes = True


# Update forward reference
TokenResponse.model_rebuild()

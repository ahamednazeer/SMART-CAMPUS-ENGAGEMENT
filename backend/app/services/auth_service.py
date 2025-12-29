from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    async def authenticate(self, credentials: LoginRequest) -> TokenResponse:
        """Authenticate user and return token."""
        user = await self.user_repo.get_by_username(credentials.username)
        
        if user is None:
            raise ValueError("Invalid username or password")
        
        if not verify_password(credentials.password, user.password_hash):
            raise ValueError("Invalid username or password")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )
        
        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )
    
    async def get_current_user_info(self, user: User) -> UserResponse:
        """Get current user information."""
        return UserResponse.model_validate(user)

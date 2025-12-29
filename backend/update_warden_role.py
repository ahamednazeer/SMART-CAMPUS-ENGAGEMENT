"""
Script to update a user's role to WARDEN.
Run with: python3 update_warden_role.py <email>
"""
import asyncio
import sys
from sqlalchemy import select, update
from app.core.database import async_session_maker
from app.models.user import User, UserRole

async def update_user_role_to_warden(email: str):
    async with async_session_maker() as session:
        # Find the user
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"User with email {email} not found!")
            return False
        
        print(f"Found user: {user.first_name} {user.last_name}, current role: {user.role}")
        
        # Update role to WARDEN
        user.role = UserRole.WARDEN
        await session.commit()
        
        print(f"Updated {email} role to WARDEN")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        email = "warden@gmail.com"  # Default
    else:
        email = sys.argv[1]
    
    asyncio.run(update_user_role_to_warden(email))

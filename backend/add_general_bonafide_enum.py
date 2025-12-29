"""
Migration script to add GENERAL_BONAFIDE to certificatetype enum.
Run with: python3 add_general_bonafide_enum.py
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_session_maker

async def add_general_bonafide_enum():
    async with async_session_maker() as session:
        print("Adding GENERAL_BONAFIDE to certificatetype enum...")
        
        try:
            # Add the new enum value
            await session.execute(text("""
                ALTER TYPE certificatetype ADD VALUE IF NOT EXISTS 'GENERAL_BONAFIDE'
            """))
            print(" Added GENERAL_BONAFIDE to certificatetype enum")
            
            await session.commit()
            print("\n Migration complete!")
            
        except Exception as e:
            print(f" Error: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(add_general_bonafide_enum())

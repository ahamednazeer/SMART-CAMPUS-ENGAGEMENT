"""
Migration script to add approver_type column to bonafide_certificates table.
Run with: python3 add_approver_type.py
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_session_maker

async def add_approver_type_column():
    async with async_session_maker() as session:
        print("Adding approver_type column to bonafide_certificates table...")
        
        try:
            # First, create the enum type if it doesn't exist
            await session.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE approvertype AS ENUM ('WARDEN', 'ADMIN');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            print(" Created approvertype enum (or already exists)")
            
            # Add the column with default value
            await session.execute(text("""
                ALTER TABLE bonafide_certificates 
                ADD COLUMN IF NOT EXISTS approver_type approvertype NOT NULL DEFAULT 'WARDEN'
            """))
            print(" Added approver_type column with default 'WARDEN'")
            
            await session.commit()
            print("\n Migration complete!")
            
        except Exception as e:
            print(f" Error: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(add_approver_type_column())

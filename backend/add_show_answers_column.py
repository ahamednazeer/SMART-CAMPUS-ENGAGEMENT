"""
Async migration script to add show_answers_after_completion column to quizzes table.
Uses the app's database connection.
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def run_migration():
    try:
        async with engine.begin() as conn:
            # Check if column exists
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'quizzes' AND column_name = 'show_answers_after_completion'
            """))
            
            if result.fetchone():
                print("Column 'show_answers_after_completion' already exists in quizzes table")
            else:
                # Add the column
                await conn.execute(text("""
                    ALTER TABLE quizzes 
                    ADD COLUMN show_answers_after_completion BOOLEAN NOT NULL DEFAULT FALSE
                """))
                print(" Added 'show_answers_after_completion' column to quizzes table")
            
            await conn.commit()
        
        print("\n Migration complete!")
        
    except Exception as e:
        print(f" Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())

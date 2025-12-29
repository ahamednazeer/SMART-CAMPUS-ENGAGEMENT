"""
Migration script to create queries table.
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def run_migration():
    try:
        async with engine.begin() as conn:
            # Check if table exists
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_name = 'queries'
            """))
            
            if result.fetchone():
                print("Table 'queries' already exists")
            else:
                # Create enum types first
                await conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE querycategory AS ENUM ('RULES', 'TIMINGS', 'POLICY', 'OTHERS');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                await conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE querystatus AS ENUM ('OPEN', 'RESOLVED');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                # Create the table
                await conn.execute(text("""
                    CREATE TABLE queries (
                        id SERIAL PRIMARY KEY,
                        student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        student_type VARCHAR(20) NOT NULL,
                        category querycategory NOT NULL DEFAULT 'OTHERS',
                        description TEXT NOT NULL,
                        status querystatus NOT NULL DEFAULT 'OPEN',
                        response TEXT,
                        responded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                        responded_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                
                # Create index
                await conn.execute(text("""
                    CREATE INDEX idx_queries_student_id ON queries(student_id)
                """))
                await conn.execute(text("""
                    CREATE INDEX idx_queries_status ON queries(status)
                """))
                
                print(" Created 'queries' table with indexes")
            
            await conn.commit()
        
        print("\n Migration complete!")
        
    except Exception as e:
        print(f" Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())

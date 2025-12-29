"""Migration script to create complaints table."""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def create_complaints_table():
    """Create the complaints table with enums and indexes."""
    async with engine.begin() as conn:
        # Create enums
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE complaintcategory AS ENUM (
                    'ELECTRICAL', 'PLUMBING', 'CLEANING', 'FURNITURE', 'EQUIPMENT', 'OTHER'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE complaintstatus AS ENUM (
                    'SUBMITTED', 'IN_PROGRESS', 'CLOSED', 'REJECTED'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE complaintpriority AS ENUM (
                    'LOW', 'MEDIUM', 'HIGH', 'URGENT'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        # Create table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS complaints (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES users(id),
                student_type VARCHAR(20) NOT NULL,
                category VARCHAR(20) NOT NULL,
                priority VARCHAR(10) DEFAULT 'MEDIUM',
                location VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                image_url VARCHAR(500),
                status VARCHAR(20) DEFAULT 'SUBMITTED',
                assigned_to VARCHAR(100),
                assigned_at TIMESTAMP,
                resolution_notes TEXT,
                rejection_reason TEXT,
                verified_by INTEGER REFERENCES users(id),
                verified_at TIMESTAMP,
                closed_by INTEGER REFERENCES users(id),
                closed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_complaints_student ON complaints(student_id);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_complaints_student_type ON complaints(student_type);
        """))
        
        print(" Complaints table created successfully!")


if __name__ == "__main__":
    asyncio.run(create_complaints_table())

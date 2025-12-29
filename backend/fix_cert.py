"""
Fix the existing certificate - set hostel_id to the correct hostel.
"""
import asyncio
from sqlalchemy import select, update
from app.core.database import async_session_maker
from app.models.bonafide import BonafideCertificate
from app.models.hostel import HostelAssignment

async def fix_certificate():
    async with async_session_maker() as session:
        # Get certificate ID 1
        result = await session.execute(
            select(BonafideCertificate).where(BonafideCertificate.id == 1)
        )
        cert = result.scalar_one_or_none()
        
        if not cert:
            print("Certificate not found!")
            return
        
        print(f"Certificate: ID={cert.id}, Student ID={cert.student_id}, Hostel ID={cert.hostel_id}")
        
        # Find student's hostel assignment
        result = await session.execute(
            select(HostelAssignment).where(
                HostelAssignment.student_id == cert.student_id,
                HostelAssignment.is_active == True
            )
        )
        assignment = result.scalar_one_or_none()
        
        if assignment:
            print(f"Found assignment: Hostel ID={assignment.hostel_id}, Room ID={assignment.room_id}")
            
            # Update certificate
            cert.hostel_id = assignment.hostel_id
            await session.commit()
            print(f" Updated certificate hostel_id to {assignment.hostel_id}")
        else:
            # Just set to hostel ID 1 (ROSE)
            print("No assignment found, setting hostel_id to 1 (ROSE)")
            cert.hostel_id = 1
            await session.commit()
            print(" Updated certificate hostel_id to 1")

if __name__ == "__main__":
    asyncio.run(fix_certificate())

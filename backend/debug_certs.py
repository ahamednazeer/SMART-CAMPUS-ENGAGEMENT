"""
Debug script for certificate feature.
"""
import asyncio
from sqlalchemy import select, text
from app.core.database import async_session_maker, engine
from app.models.user import User, UserRole
from app.models.bonafide import BonafideCertificate

async def debug():
    async with async_session_maker() as session:
        print("\n=== DEBUGGING CERTIFICATE FEATURE ===\n")
        
        # 1. Check if bonafide_certificates table exists
        print("1. Checking if bonafide_certificates table exists...")
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM bonafide_certificates")
            )
            count = result.scalar()
            print(f"    Table exists! {count} certificate(s) found.\n")
        except Exception as e:
            print(f"    Table doesn't exist! Error: {e}\n")
            print("   >>> You need to restart the backend to create the table.\n")
            return
        
        # 2. List all certificates
        print("2. All certificates in database:")
        certs = await session.execute(select(BonafideCertificate))
        for cert in certs.scalars().all():
            print(f"   - ID: {cert.id}, Student ID: {cert.student_id}, "
                  f"Hostel ID: {cert.hostel_id}, Status: {cert.status}")
        
        # 3. Check warden user
        print("\n3. Checking warden user (warden@gmail.com):")
        result = await session.execute(
            select(User).where(User.email == "warden@gmail.com")
        )
        warden = result.scalar_one_or_none()
        if warden:
            print(f"    Found warden: {warden.first_name}, Role: {warden.role}")
            if warden.role != UserRole.WARDEN:
                print(f"   ⚠️  Role is NOT WARDEN! It's {warden.role}")
                print("   >>> Updating role to WARDEN now...")
                warden.role = UserRole.WARDEN
                await session.commit()
                print("    Updated!")
        else:
            print("    warden@gmail.com not found!")
        
        # 4. Check if warden is assigned to a hostel
        print("\n4. Checking if warden is assigned to a hostel:")
        from app.models.hostel import Hostel
        result = await session.execute(
            select(Hostel).where(Hostel.warden_id == warden.id if warden else None)
        )
        hostel = result.scalar_one_or_none()
        if hostel:
            print(f"    Warden manages hostel: {hostel.name} (ID: {hostel.id})")
            
            # Check if there are certificates for this hostel
            print(f"\n5. Certificates for hostel {hostel.name}:")
            certs = await session.execute(
                select(BonafideCertificate).where(BonafideCertificate.hostel_id == hostel.id)
            )
            for cert in certs.scalars().all():
                print(f"   - ID: {cert.id}, Student ID: {cert.student_id}, Status: {cert.status}")
        else:
            print("    Warden is not assigned to any hostel!")
        
        print("\n=== DEBUG COMPLETE ===\n")

if __name__ == "__main__":
    asyncio.run(debug())

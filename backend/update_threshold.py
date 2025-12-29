import asyncio
from app.core.database import async_session_maker
from app.models.attendance import CampusGeofence
from sqlalchemy import select

async def update_threshold():
    async with async_session_maker() as session:
        result = await session.execute(select(CampusGeofence).where(CampusGeofence.is_primary == True))
        geofence = result.scalar_one_or_none()
        
        if geofence:
            print(f"Updating threshold from {geofence.accuracy_threshold}m to 200m...")
            geofence.accuracy_threshold = 200.0
            await session.commit()
            print("Done!")
        else:
            print("No primary geofence found.")

if __name__ == "__main__":
    asyncio.run(update_threshold())

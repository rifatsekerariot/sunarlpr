import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory
from app.models.models import User, Camera
from app.core.security import get_password_hash

async def seed_data():
    async with async_session_factory() as session:
        # Check if Admin exists
        from sqlalchemy import select
        result = await session.execute(select(User).filter(User.username == "admin"))
        admin = result.scalars().first()
        
        if not admin:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="ADMIN",
                is_active=True
            )
            session.add(admin)
            print("Admin user seeded: admin / admin123")
            
        # Check if cameras exist
        result = await session.execute(select(Camera))
        cameras = result.scalars().all()
        
        if not cameras:
            # Seed 1 default camera matching the camera-worker UUID config
            cam = Camera(
                id="8f8f8f8f-8f8f-8f8f-8f8f-8f8f8f8f8f8f",
                name="Ana Kapı Giriş",
                location="Ana Giriş Noktası",
                direction="IN",
                rtsp_url="simulation_rtsp_url",
                is_active=True
            )
            session.add(cam)
            print("Default camera seeded: 8f8f8f8f-8f8f-8f8f-8f8f-8f8f8f8f8f8f")
            
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_data())

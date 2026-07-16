import asyncio
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.models import User, Camera
from app.core.security import get_password_hash


async def seed_data():
    async with async_session_factory() as session:
        # Seed admin user
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
        else:
            print("Admin user already exists.")

        # Seed default camera
        result = await session.execute(select(Camera))
        cameras = result.scalars().all()

        if not cameras:
            cam = Camera(
                id="8f8f8f8f-8f8f-8f8f-8f8f-8f8f8f8f8f8f",
                name="Ana Kapı Giriş",
                location="Ana Giriş Noktası",
                direction="IN",
                rtsp_url="simulation_rtsp_url",
                is_active=True
            )
            session.add(cam)
            print("Default camera seeded.")
        else:
            print("Cameras already exist.")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_data())

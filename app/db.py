from app.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client["assessment"]

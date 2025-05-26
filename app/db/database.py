from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# MongoDB client instance
client = None
db = None

async def connect_to_mongo():
    """Create database connection."""
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    print("Connected to MongoDB")

async def close_mongo_connection():
    """Close database connection."""
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")

def get_database():
    """Return database instance."""
    return db
import os
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_CLIENT_ID = os.getenv("MONGODB_CLIENT_ID")

client = MongoClient(MONGODB_CLIENT_ID)

db = client.IntrolixDb

feed_data = db.feedData

async def startup_db_client(app):
    app.mongodb_client = AsyncIOMotorClient(MONGODB_CLIENT_ID)
    app.mongodb = app.mongodb_client.get_database("IntrolixDb")
    print("MongoDB connected.")

async def shutdown_db_client(app):
    app.mongodb_client.close()
    print("Database disconnected.")
    
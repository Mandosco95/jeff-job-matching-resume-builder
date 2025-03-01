from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="User Management API", 
              description="Simple API for user management",
              version="1.0.0")

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
db = None

@app.on_event("startup")
async def startup_db_client():
    global db
    try:
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL)
        # Verify the connection
        await client.admin.command('ping')
        db = client.streamlit_demo
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    if db:
        logger.info("Closing MongoDB connection...")
        db.client.close()
        logger.info("MongoDB connection closed")

# User Models
class UserCreate(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: str
    name: str

@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user"""
    # Insert user
    result = await db.users.insert_one({"name": user.name})
    
    # Return created user
    return {
        "id": str(result.inserted_id),
        "name": user.name
    }

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserCreate):
    """Update a user's name"""
    try:
        # Update user
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"name": user.name}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user_id,
            "name": user.name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run("main:app", host=host, port=port, reload=debug) 
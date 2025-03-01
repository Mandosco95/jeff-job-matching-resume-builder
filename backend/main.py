from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import random
from datetime import datetime, timedelta
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

app = FastAPI(title="Streamlit Demo API", 
              description="A simple API for demonstration with Streamlit",
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

# Data models
class DataPoint(BaseModel):
    date: str
    value: float
    category: str

class DataResponse(BaseModel):
    data: List[DataPoint]
    count: int
    message: str

class PredictionRequest(BaseModel):
    input_value: float
    category: str

class PredictionResponse(BaseModel):
    predicted_value: float
    confidence: float
    message: str

# Available categories
categories = ["A", "B", "C"]

@app.get("/")
def read_root():
    return {"message": "Welcome to the Streamlit Demo API"}

@app.get("/api/data", response_model=DataResponse)
async def get_data(category: Optional[str] = None, limit: int = 50):
    """Get sample data, optionally filtered by category"""
    query = {}
    if category:
        if category not in categories:
            raise HTTPException(status_code=400, detail=f"Category must be one of {categories}")
        query["category"] = category
    
    cursor = db.data_points.find(query).limit(limit)
    data = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string for each document
    for item in data:
        item["_id"] = str(item["_id"])
    
    return {
        "data": data,
        "count": len(data),
        "message": f"Retrieved {len(data)} data points"
    }

@app.post("/api/data")
async def create_data_point(data_point: DataPoint):
    """Create a new data point"""
    if data_point.category not in categories:
        raise HTTPException(status_code=400, detail=f"Category must be one of {categories}")
    
    result = await db.data_points.insert_one(data_point.dict())
    return {"id": str(result.inserted_id), "message": "Data point created successfully"}

@app.post("/api/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """Make a simple prediction based on input value"""
    # This is a dummy prediction - in a real app, you'd use a model
    predicted_value = request.input_value * 1.5 if request.category == "A" else request.input_value * 0.8
    confidence = random.uniform(0.7, 0.99)
    
    return {
        "predicted_value": round(predicted_value, 2),
        "confidence": round(confidence, 4),
        "message": f"Prediction for category {request.category} completed"
    }

@app.get("/api/categories")
def get_categories():
    """Get available categories"""
    return {"categories": categories}

@app.get("/api/health")
async def health_check():
    """Check the health of the API and database connection"""
    try:
        await db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )

# Initialize sample data in MongoDB
@app.on_event("startup")
async def init_db():
    # Check if we already have data
    count = await db.data_points.count_documents({})
    if count == 0:
        # Generate sample data
        sample_data = []
        start_date = datetime.now() - timedelta(days=30)
        for i in range(100):
            sample_data.append({
                "date": (start_date + timedelta(days=i//3)).strftime("%Y-%m-%d"),
                "value": round(random.uniform(10, 100), 2),
                "category": random.choice(categories)
            })
        # Insert sample data
        await db.data_points.insert_many(sample_data)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run("main:app", host=host, port=port, reload=debug) 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import random
from datetime import datetime, timedelta

app = FastAPI(title="Streamlit Demo API", 
              description="A simple API for demonstration with Streamlit",
              version="1.0.0")

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

# Sample data storage
sample_data = []
categories = ["A", "B", "C"]

# Generate some sample data
start_date = datetime.now() - timedelta(days=30)
for i in range(100):
    sample_data.append({
        "date": (start_date + timedelta(days=i//3)).strftime("%Y-%m-%d"),
        "value": round(random.uniform(10, 100), 2),
        "category": random.choice(categories)
    })

@app.get("/")
def read_root():
    return {"message": "Welcome to the Streamlit Demo API"}

@app.get("/api/data", response_model=DataResponse)
def get_data(category: Optional[str] = None, limit: int = 50):
    """Get sample data, optionally filtered by category"""
    filtered_data = sample_data
    
    if category:
        if category not in categories:
            raise HTTPException(status_code=400, detail=f"Category must be one of {categories}")
        filtered_data = [item for item in sample_data if item["category"] == category]
    
    result = filtered_data[:limit]
    
    return {
        "data": result,
        "count": len(result),
        "message": f"Retrieved {len(result)} data points"
    }

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
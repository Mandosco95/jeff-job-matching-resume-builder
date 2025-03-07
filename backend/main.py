from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import os
import base64
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging
from openai import AsyncOpenAI
import json
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Resume Parser API", 
             description="API for parsing resumes using OpenAI",
             version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

db = None
client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    timeout=60.0  # Increased timeout for longer operations
)

@app.on_event("startup")
async def startup_db_client():
    global db
    try:
        logger.info("Connecting to MongoDB...")
        mongo_client = AsyncIOMotorClient(MONGODB_URL)
        # Verify the connection
        await mongo_client.admin.command('ping')
        db = mongo_client.resume_parser
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

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the API is running.
    """
    return {
        "status": "healthy",
        "message": "API is running"
    }

class ResumeResponse(BaseModel):
    filename: str
    extracted_text: str
    parsed_data: dict
    additional_info: Optional[str] = None

async def process_file_with_openai(file_content: bytes, filename: str, additional_info: Optional[str] = None) -> dict:
    """
    Process the file content using OpenAI's API.
    """
    try:
        # Extract text from the file based on its type
        file_extension = filename.split('.')[-1].lower()
        extracted_text = ""

        if file_extension == 'pdf':
            from PyPDF2 import PdfReader
            pdf_reader = PdfReader(io.BytesIO(file_content))
            extracted_text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        elif file_extension == 'docx':
            import docx
            doc = docx.Document(io.BytesIO(file_content))
            extracted_text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        elif file_extension == 'txt':
            extracted_text = file_content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Create messages for the chat completion
        messages = [
            {
                "role": "system",
                "content": """You are an expert resume parser. Extract key information from the resume including:
                - Personal Information (name, contact details)
                - Education
                - Work Experience
                - Skills
                - Projects
                - Certifications
                Please structure the information clearly and maintain the original formatting where relevant."""
            },
            {
                "role": "user",
                "content": extracted_text + (f"\nAdditional Information: {additional_info}" if additional_info else "")
            }
        ]

        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4096
        )

        # Extract the response text
        extracted_text = response.choices[0].message.content

        # Parse the extracted text into structured data
        parsed_data = {
            "personal_info": {},
            "education": [],
            "work_experience": [],
            "skills": [],
            "projects": [],
            "certifications": []
        }

        # Additional processing to structure the data
        try:
            # Use another OpenAI call to structure the data
            structure_messages = [
                {
                    "role": "system",
                    "content": "You are a data structuring expert. Convert the following resume text into a structured JSON format with these categories: personal_info, education, work_experience, skills, projects, and certifications."
                },
                {
                    "role": "user",
                    "content": extracted_text
                }
            ]

            structure_response = await client.chat.completions.create(
                model="gpt-4o",
                messages=structure_messages,
                response_format={"type": "json_object"}
            )

            parsed_data = json.loads(structure_response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error structuring data: {str(e)}")

        return {
            "filename": filename,
            "extracted_text": extracted_text,
            "parsed_data": parsed_data,
            "additional_info": additional_info
        }

    except Exception as e:
        logger.error(f"Error processing file with OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume", response_model=ResumeResponse, tags=["Resume"])
async def process_resume(
    background_tasks: BackgroundTasks,
    cv_file: UploadFile = File(...),
    additional_info: Optional[str] = Form(None)
):
    """
    Process a resume file and extract information using OpenAI.
    """
    try:
        # Read file content
        file_content = await cv_file.read()
        
        # Process the file with OpenAI
        result = await process_file_with_openai(file_content, cv_file.filename, additional_info)
        
        # Store in MongoDB asynchronously
        background_tasks.add_task(
            store_resume_data,
            result
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def store_resume_data(data: dict):
    """
    Store the processed resume data in MongoDB.
    """
    try:
        await db.resumes.insert_one(data)
        logger.info(f"Stored resume data for file: {data['filename']}")
    except Exception as e:
        logger.error(f"Error storing resume data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, Dict
import os
import io
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging

# For file processing
import PyPDF2
import docx
import tempfile

# Add these imports at the top
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from reportlab.pdfgen import canvas
from io import BytesIO
import json

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

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        Dict with status and message.
    """
    return {
        "status": "healthy",
        "message": "API is running"
    }

# User Models
class UserCreate(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: str
    name: str

class CVResponse(BaseModel):
    id: str
    filename: str
    extracted_text: str
    additional_info: str

class CustomizeDocumentsRequest(BaseModel):
    job_description: str
    user_id: str

class DocumentGenerator:
    def __init__(self):
        self.llm = OpenAI(temperature=0.7)
        
        self.cv_prompt = PromptTemplate(
            input_variables=["job_description", "user_experience"],
            template="""
            Based on the following job description:
            {job_description}
            
            And the user's experience:
            {user_experience}
            
            Generate a tailored CV that highlights relevant skills and experience.
            Format the response as a JSON with sections: summary, skills, experience, education.
            """
        )
        
        self.cover_letter_prompt = PromptTemplate(
            input_variables=["job_description", "user_experience"],
            template="""
            Based on the following job description:
            {job_description}
            
            And the user's experience:
            {user_experience}
            
            Write a compelling cover letter that demonstrates why the candidate is perfect for this role.
            Format the response as a JSON with sections: opening, body_paragraphs, closing.
            """
        )
    
    def generate_cv(self, job_description: str, user_experience: dict) -> str:
        prompt = self.cv_prompt.format(
            job_description=job_description,
            user_experience=json.dumps(user_experience)
        )
        response = self.llm(prompt)
        return json.loads(response)
    
    def generate_cover_letter(self, job_description: str, user_experience: dict) -> str:
        prompt = self.cover_letter_prompt.format(
            job_description=job_description,
            user_experience=json.dumps(user_experience)
        )
        response = self.llm(prompt)
        return json.loads(response)
    
    def create_pdf(self, content: dict, document_type: str) -> bytes:
        buffer = BytesIO()
        c = canvas.Canvas(buffer)
        
        if document_type == "cv":
            # Format CV PDF
            c.drawString(100, 800, "Professional Summary")
            c.drawString(100, 780, content["summary"])
            
            c.drawString(100, 740, "Skills")
            y = 720
            for skill in content["skills"]:
                c.drawString(120, y, f"• {skill}")
                y -= 20
                
            # Add other sections...
            
        else:  # cover letter
            # Format Cover Letter PDF
            c.drawString(100, 800, content["opening"])
            
            y = 760
            for paragraph in content["body_paragraphs"]:
                c.drawString(100, y, paragraph)
                y -= 40
                
            c.drawString(100, y-20, content["closing"])
        
        c.save()
        return buffer.getvalue()

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

# Function to extract text from different file formats
def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from PDF, DOCX, or TXT files"""
    file_extension = filename.split('.')[-1].lower()
    
    try:
        if file_extension == 'pdf':
            # Process PDF file
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
            return text
            
        elif file_extension == 'docx':
            # Process DOCX file
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp.write(file_content)
                temp_path = temp.name
            
            doc = docx.Document(temp_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            # Clean up temp file
            os.unlink(temp_path)
            return text
            
        elif file_extension == 'txt':
            # Process TXT file
            return file_content.decode('utf-8')
            
        else:
            return f"Unsupported file format: {file_extension}"
            
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {str(e)}")
        return f"Error processing file: {str(e)}"

@app.post("/api/cv", response_model=CVResponse)
async def process_cv(
    cv_file: UploadFile = File(...),
    additional_info: str = Form(...)
):
    """
    Process CV file and additional information
    - Extract text from CV file (PDF, DOCX, or TXT)
    - Save extracted text and additional info to MongoDB
    """
    try:
        # Read file content
        file_content = await cv_file.read()
        # Print file content for debugging
        print(f"File content: {file_content[:100]}...")  # Print first 100 bytes to avoid overwhelming logs
        # Extract text from file
        extracted_text = extract_text_from_file(file_content, cv_file.filename)
        
        # Save to MongoDB
        cv_data = {
            "filename": cv_file.filename,
            "extracted_text": extracted_text,
            "additional_info": additional_info,
            "file_size": len(file_content),
            "created_at": ObjectId().generation_time
        }
        
        result = await db.cv_documents.insert_one(cv_data)
        
        return {
            "id": str(result.inserted_id),
            "filename": cv_file.filename,
            "extracted_text": extracted_text,
            "additional_info": additional_info
        }
        
    except Exception as e:
        logger.error(f"Error processing CV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")

@app.post("/customize-documents")
async def customize_documents(request: CustomizeDocumentsRequest):
    try:
        # Get user experience from database
        user_experience = await db.users.find_one(
            {"_id": ObjectId(request.user_id)},
            {"experience": 1, "education": 1, "skills": 1}
        )
        
        if not user_experience:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Initialize document generator
        generator = DocumentGenerator()
        
        # Generate customized content
        cv_content = generator.generate_cv(
            request.job_description,
            user_experience
        )
        
        cover_letter_content = generator.generate_cover_letter(
            request.job_description,
            user_experience
        )
        
        # Convert to PDFs
        cv_pdf = generator.create_pdf(cv_content, "cv")
        cover_letter_pdf = generator.create_pdf(cover_letter_content, "cover_letter")
        
        return {
            "success": True,
            "cv_content": cv_pdf,
            "cover_letter_content": cover_letter_pdf
        }
        
    except Exception as e:
        logger.error(f"Error customizing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run("main:app", host=host, port=port, reload=debug) 
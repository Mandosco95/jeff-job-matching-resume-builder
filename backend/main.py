from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging
from openai import AsyncOpenAI
import json
import io
from datetime import datetime, date
from jobspy import scrape_jobs
from fastapi.responses import JSONResponse
import math
from bson import json_util
from utils.pdf_generator import PDFGenerator
import base64
import requests
import httpx
import constants
import tempfile
import subprocess
import re

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
    parsed_data: dict
    extracted_text: str
    additional_info: Optional[str] = None
    skills_keywords: Optional[str] = None
    filename: str
    skills: List[str]

class JobSearchParams(BaseModel):
    """
    Parameters for job search request
    """
    search_term: str
    location: str = "United States"  # default location
    results_wanted: int = 20  # default number of results
    country_indeed: str = "USA"  # default country for Indeed

class JobResponse(BaseModel):
    """
    Response model for job search results
    """
    total_jobs: int
    timestamp: datetime
    search_params: dict
    message: str

class ChatRequest(BaseModel):
    question: str

class CustomizeDocumentsRequest(BaseModel):
    job_description: str

class ResumeRequest(BaseModel):
    additional_info: Optional[str] = None
    skills_keywords: Optional[str] = None

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
                - Skills (provide a clear, comma-separated list)
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
                    "content": "You are a data structuring expert. Convert the following resume text into a structured JSON format with these categories: personal_info, education, work_experience, skills, projects, and certifications. Ensure skills are provided as a clear list."
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

        skills_list = parsed_data.get("skills", [])

        return {
            "filename": filename,
            "extracted_text": extracted_text,
            "parsed_data": parsed_data,
            "skills": skills_list,
            "additional_info": additional_info
        }

    except Exception as e:
        logger.error(f"Error processing file with OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def store_resume_data(data: dict):
    """
    Store the processed resume data in MongoDB.
    """
    try:
        # Insert the data into the 'resumes' collection
        await db.resumes.insert_one(data)
        logger.info(f"Stored resume data for file: {data['filename']}")
    except Exception as e:
        logger.error(f"Error storing resume data: {str(e)}")

@app.post("/api/resume", response_model=ResumeResponse, tags=["Resume"])
async def parse_resume(
    request: Request,
    cv_file: UploadFile,
    additional_info: Optional[str] = Form(None),
    roles_keywords: Optional[str] = Form(None)
):
    try:
        logger.info(f"Starting resume parsing for file: {cv_file.filename}")
        logger.info(f"Roles keywords received: {roles_keywords}")

        # Read file content
        file_content = await cv_file.read()
        
        # Process the file with OpenAI
        result = await process_file_with_openai(file_content, cv_file.filename, additional_info)
        
        # Store in MongoDB with the updated field name
        resume_data = {
            "parsed_data": result["parsed_data"],
            "extracted_text": result["extracted_text"],
            "additional_info": additional_info,
            "roles_keywords": roles_keywords,
            "filename": cv_file.filename,
            "skills": result["skills"]
        }

        # Insert into MongoDB
        await db.resumes.insert_one(resume_data)
        logger.info("Resume data saved to MongoDB")

        # Automatically trigger job search if roles_keywords is provided
        if roles_keywords:
            logger.info(f"Initiating job search for roles: {roles_keywords}")
            try:
                base_url = os.getenv("BACKEND_URL")
                search_url = f"{base_url}/api/jobs/search"
                logger.info(f"Making request to: {search_url}")
                
                search_payload = {
                    "search_term": roles_keywords,
                    "location": "United States",
                    "results_wanted": 20
                }
                logger.info(f"Search payload: {search_payload}")

                async with httpx.AsyncClient(follow_redirects=True) as client:
                    search_response = await client.post(
                        search_url,
                        json=search_payload
                    )
                
                logger.info(f"Job search API response status: {search_response.status_code}")
                
                if search_response.status_code == 200:
                    search_result = search_response.json()
                    logger.info("Job search completed successfully")
                    # Include job search results in the response
                    return {
                        "parsed_data": result["parsed_data"],
                        "extracted_text": result["extracted_text"],
                        "additional_info": additional_info,
                        "roles_keywords": roles_keywords,
                        "filename": cv_file.filename,
                        "skills": result["skills"],
                        "job_search": {
                            "status": "success",
                            "message": search_result.get("message", "Jobs search completed")
                        }
                    }
                else:
                    logger.error(f"Job search failed with status {search_response.status_code}: {search_response.text}")
                    return {
                        "parsed_data": result["parsed_data"],
                        "extracted_text": result["extracted_text"],
                        "additional_info": additional_info,
                        "roles_keywords": roles_keywords,
                        "filename": cv_file.filename,
                        "skills": result["skills"],
                        "job_search": {
                            "status": "error",
                            "message": f"Job search failed: {search_response.text}"
                        }
                    }
            except Exception as search_error:
                logger.error(f"Error during job search: {str(search_error)}")
                return {
                    "parsed_data": result["parsed_data"],
                    "extracted_text": result["extracted_text"],
                    "additional_info": additional_info,
                    "roles_keywords": roles_keywords,
                    "filename": cv_file.filename,
                    "skills": result["skills"],
                    "job_search": {
                        "status": "error",
                        "message": str(search_error)
                    }
                }
        else:
            logger.info("No roles keywords provided, skipping job search")
        
        # Return response without job search if no roles_keywords
        return {
            "parsed_data": result["parsed_data"],
            "extracted_text": result["extracted_text"],
            "additional_info": additional_info,
            "roles_keywords": roles_keywords,
            "filename": cv_file.filename,
            "skills": result["skills"]
        }

    except Exception as e:
        logger.error(f"Error in resume parsing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/search", response_model=JobResponse, tags=["Jobs"])
async def search_and_store_jobs(params: JobSearchParams):
    """
    Search jobs from LinkedIn and Indeed, then store them in MongoDB.
    """
    try:
        logger.info(f"Starting job search with parameters: {params.dict()}")
        
        # Scrape jobs using JobSpy (only LinkedIn and Indeed)
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed"],
            search_term=params.search_term,
            location=params.location,
            results_wanted=params.results_wanted,
            country_indeed=params.country_indeed,
            hours_old=72,  # Get jobs posted in the last 72 hours
            linkedin_fetch_description=True
        )

        # Convert jobs to a list of dictionaries and add timestamp
        jobs_list = jobs.to_dict(orient='records')
        timestamp = datetime.utcnow()
        
        # Enhance job records with additional metadata and handle date serialization
        enhanced_jobs = []
        for job in jobs_list:
            # Convert any date objects to datetime for MongoDB compatibility
            job_dict = dict(job)  # Create a copy of the job dictionary
            for key, value in job_dict.items():
                if isinstance(value, date) and not isinstance(value, datetime):
                    job_dict[key] = datetime.combine(value, datetime.min.time())
            
            job_dict['timestamp'] = timestamp
            job_dict['search_term'] = params.search_term
            job_dict['search_location'] = params.location
            enhanced_jobs.append(job_dict)

        # Store in MongoDB
        if enhanced_jobs:
            try:
                await db.jobs.insert_many(enhanced_jobs)
                logger.info(f"Successfully stored {len(enhanced_jobs)} jobs in database")
            except Exception as e:
                logger.error(f"Error storing jobs in database: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to store jobs in database")

        return JobResponse(
            total_jobs=len(enhanced_jobs),
            timestamp=timestamp,
            search_params=params.dict(),
            message=f"Successfully scraped and stored {len(enhanced_jobs)} jobs"
        )

    except Exception as e:
        logger.error(f"Error in job search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def clean_mongo_data(data):
    """Clean MongoDB data by handling NaN values, ObjectId, and dates."""
    if isinstance(data, dict):
        return {k: clean_mongo_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_mongo_data(item) for item in data]
    elif isinstance(data, float) and (math.isnan(data) or math.isinf(data)):
        return None
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    else:
        return data

@app.get("/api/jobs/recent", tags=["Jobs"])
async def get_recent_jobs(
    search_term: Optional[str] = None,
    limit: int = 50
):
    """
    Retrieve recent jobs from the database.
    """
    try:
        # Build the query
        query = {}
        if search_term:
            query["search_term"] = search_term

        # Get jobs from MongoDB
        cursor = db.jobs.find(query).sort("timestamp", -1).limit(limit)
        jobs = await cursor.to_list(length=limit)
        
        # Clean the data directly without using dumps/loads
        cleaned_jobs = clean_mongo_data(jobs)
        
        response_data = {
            "total_jobs": len(cleaned_jobs),
            "jobs": cleaned_jobs
        }

        # Use json_util.dumps to handle MongoDB-specific types
        return JSONResponse(
            content=json.loads(json_util.dumps(response_data))
        )

    except Exception as e:
        logger.error(f"Error retrieving jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/jobs/clear", tags=["Jobs"])
async def clear_jobs_collection():
    """
    Clear all jobs from the database.
    """
    try:
        result = await db.jobs.delete_many({})
        return {
            "message": f"Successfully deleted {result.deleted_count} jobs from the database"
        }
    except Exception as e:
        logger.error(f"Error clearing jobs collection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat", tags=["Chat"])
async def chat_with_resume(request: ChatRequest):
    """
    Handle chat requests and generate responses based on the last resume data.
    """
    try:
        question = request.question
        # Fetch the last resume data from MongoDB
        user_resume = await db.resumes.find().sort("_id", -1).limit(1).to_list(1)
        if not user_resume:
            raise HTTPException(status_code=404, detail="No resume found")

        # Extract the resume data
        resume_data = user_resume[0]['parsed_data']

        # Prepare messages for OpenAI
        messages = [
            {
                "role": "system",
                "content": "You are an AI assistant that provides answers based on the user's resume."
            },
            {
                "role": "user",
                "content": question
            },
            {
                "role": "assistant",
                "content": f"Resume details: {resume_data}"
            }
        ]

        # Call OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=150
        )

        # Extract the response text
        answer = response.choices[0].message.content

        return {"answer": answer}

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def clean_latex_content_using_llm(latex_content: str) -> str:
    """Clean LaTeX content using LLM."""
    messages = [
        {"role": "system", "content": "The following is a LaTeX document. While converting it to PDF, got some errors using pdflatex command. So I need you to clean it up such that it can be compiled using pdflatex command without any errors. Do not change the content, only clean it up. Only provide the cleaned up LaTeX code, nothing else. While cleaning make sure to remove all the errors and warnings that pdflatex command would throw. Remove unnecessary `\\` and `\\vspace` commands. Make sure to keep the content as is and only clean it up."},
        {"role": "user", "content": latex_content}
    ]
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000
    )
    return response.choices[0].message.content


async def get_pdf_from_latex(latex_content: str, retry: bool = True) -> bytes:
    """Convert LaTeX content to PDF using a temporary file."""
    try:
        match = re.search(r"```latex(.*?)```", latex_content, re.DOTALL)

        if not match:
            raise ValueError("LaTeX code block not found in the response.")

        latex_content = match.group(1).strip()

        # Create a temporary directory to contain all LaTeX files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temp file path in the temp directory
            temp_file_path = os.path.join(temp_dir, 'resume.tex')
            logger.info(f"Writing LaTeX content to: {temp_file_path}")
            
            # Write LaTeX content to file
            with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
                temp_file.write(latex_content)

            # Run pdflatex in the temp directory
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', temp_file_path],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception immediately
            )
            
            # Log the output for debugging
            if process.stdout:
                logger.info(f"pdflatex stdout: {process.stdout}")
            if process.stderr:
                logger.error(f"pdflatex stderr: {process.stderr}")
            
            # Check if compilation was successful
            if process.returncode != 0:
                raise Exception(f"pdflatex compilation failed with return code {process.returncode}")
            
            # Get path to generated PDF
            pdf_path = os.path.join(temp_dir, 'resume.pdf')
            logger.info(f"Looking for PDF at: {pdf_path}")
            
            # Read the PDF if it exists
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_content = pdf_file.read()
                logger.info("Successfully generated PDF")
                return pdf_content
            else:
                raise Exception("PDF file was not generated")
                
    except Exception as e:
        if retry:
            logger.info("Retrying after cleaning LaTeX content using LLM")
            cleaned_latex_content = await clean_latex_content_using_llm(latex_content)
            logger.info(f"Cleaned LaTeX content: {cleaned_latex_content}")
            return await get_pdf_from_latex(cleaned_latex_content, retry=False)
        
        logger.error(f"Error converting LaTeX to PDF: {str(e)}")
        logger.error(f"LaTeX content start: {latex_content[:100]}")
        logger.error(f"LaTeX content end: {latex_content[-100:]}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/customize-documents", tags=["Documents"])
async def customize_documents(request: CustomizeDocumentsRequest):
    try:
        # 1. Get the user's resume data from MongoDB
        # Fetch the last resume data from MongoDB
        user_resume = await db.resumes.find().sort("_id", -1).limit(1).to_list(1)
        if user_resume:
            user_resume = user_resume[0]

        if not user_resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # 2. Call OpenAI to customize resume
        resume_messages = [
            {
                "role": "system",
                "content": constants.RESUME_PROMPT
            },
            {
                "role": "user",
                "content": f"""Job Description: {request.job_description}
                Original Resume data: {json.dumps(user_resume['parsed_data'])}
                Please create a professional, ATS-friendly resume following the format above."""
            }
        ]

        resume_response = await client.chat.completions.create(
            model="gpt-4o",
            messages=resume_messages,
            max_tokens=2000
        )
        
        # 3. Call OpenAI to generate cover letter
        cl_messages = [
            {
                "role": "system",
                "content": constants.COVER_LETTER_FORMAT
            },
            {
                "role": "user",
                "content": f"""Job Description: {request.job_description}
                Candidate Resume: {json.dumps(user_resume['parsed_data'])}
                Please write a professional cover letter in LaTeX format."""
            }
        ]

        cl_response = await client.chat.completions.create(
            model="gpt-4o",
            messages=cl_messages,
            max_tokens=1000
        )

        # 4. Convert responses to PDFs
        resume_pdf = await get_pdf_from_latex(resume_response.choices[0].message.content)
        cl_pdf = await get_pdf_from_latex(cl_response.choices[0].message.content)

        # Encode PDFs
        resume_b64 = base64.b64encode(resume_pdf).decode()
        cl_b64 = base64.b64encode(cl_pdf).decode()

        return {
            "success": True,
            "cv_content": resume_b64,
            "cover_letter_content": cl_b64
        }

    except Exception as e:
        logger.error(f"Error customizing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
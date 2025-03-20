import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

def display_resume_data(data):
    """Display parsed resume data in a structured format"""
    st.subheader("Parsed Resume Data")
    
    # Display Personal Information
    if "personal_info" in data:
        st.write("### Personal Information")
        for key, value in data["personal_info"].items():
            st.write(f"**{key.title()}:** {value}")
    
    # Display Education
    if "education" in data:
        st.write("### Education")
        for edu in data["education"]:
            if isinstance(edu, dict):
                for key, value in edu.items():
                    st.write(f"**{key.title()}:** {value}")
            else:
                st.write(edu)
            st.write("---")
    
    # Display Work Experience
    if "work_experience" in data:
        st.write("### Work Experience")
        for exp in data["work_experience"]:
            if isinstance(exp, dict):
                for key, value in exp.items():
                    st.write(f"**{key.title()}:** {value}")
            else:
                st.write(exp)
            st.write("---")
    
    # Display Skills
    if "skills" in data:
        st.write("### Skills")
        if isinstance(data["skills"], list):
            for skill in data["skills"]:
                st.write(f"- {skill}")
        else:
            st.write(data["skills"])
    
    # Display Projects
    if "projects" in data:
        st.write("### Projects")
        for project in data["projects"]:
            if isinstance(project, dict):
                for key, value in project.items():
                    st.write(f"**{key.title()}:** {value}")
            else:
                st.write(project)
            st.write("---")
    
    # Display Certifications
    if "certifications" in data:
        st.write("### Certifications")
        for cert in data["certifications"]:
            if isinstance(cert, dict):
                for key, value in cert.items():
                    st.write(f"**{key.title()}:** {value}")
            else:
                st.write(cert)
            st.write("---")


def main():
    st.header("Upload Your Resume")
    st.markdown("### Upload your resume and get it parsed using AI")
        
    # Direct CV upload without extra click
    uploaded_file = st.file_uploader("", 
                                    type=["pdf", "docx", "txt"],
                                    label_visibility="collapsed")
    
    if uploaded_file is not None:
        # Display success message and file info
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
    
    # Text area for additional information
    additional_info = st.text_area(
        "Add any additional information you'd like the AI to consider:",
        height=100
    )

    # Input field for roles keywords
    roles_keywords = st.text_input(
        "Enter roles keywords you are looking for (space-separated):",
        placeholder="e.g., Software Engineer Data Scientist Product Manager"
    )
    
    # Submit button
    if st.button("Parse Resume", use_container_width=False):
        if uploaded_file is not None:
            # First, clear all jobs
            with st.spinner("Clearing previous jobs..."):
                try:
                    # Call the clear jobs API
                    clear_response = requests.delete(f"{API_URL}/api/jobs/clear")
                    if clear_response.status_code == 200:
                        st.success("Successfully cleared all jobs!")
                    else:
                        st.error(f"Error clearing jobs: {clear_response.status_code} - {clear_response.text}")
                        return
                except Exception as e:
                    st.error(f"Error connecting to the clear jobs endpoint: {str(e)}")
                    return

            # Then proceed with resume parsing
            with st.spinner("Processing your resume..."):
                try:
                    # Prepare the files and data for the API request
                    files = {
                        'cv_file': (uploaded_file.name, uploaded_file.getvalue(), f'application/{uploaded_file.type}')
                    }
                    data = {
                        'additional_info': additional_info if additional_info else "",
                        'roles_keywords': roles_keywords if roles_keywords else ""
                    }
                    
                    # Make the API request
                    response = requests.post(f"{API_URL}/api/resume", files=files, data=data)
                    
                    # Check if request was successful
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Resume parsed successfully!")
                        
                        # Display parsed data in tabs
                        tab1, tab2 = st.tabs(["Parsed Data", "Raw Text"])
                        
                        with tab1:
                            display_resume_data(result["parsed_data"])
                        
                        with tab2:
                            st.text_area("Extracted Text", result["extracted_text"], height=300)
                            
                            if result.get("additional_info"):
                                st.write("### Additional Information Provided")
                                st.write(result["additional_info"])

                        # Display job search results if available
                        if "job_search" in result:
                            if result["job_search"]["status"] == "success":
                                st.success(result["job_search"]["message"])
                            else:
                                st.error(f"Job search error: {result['job_search']['message']}")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Error connecting to the backend: {str(e)}")
        else:
            st.warning("Please upload your resume before submitting.")

if __name__ == "__main__":
    main() 
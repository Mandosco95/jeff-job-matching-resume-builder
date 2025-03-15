import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import math

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

def view_jobs():
    st.title("Job Listings")
    
    # Add search functionality
    with st.form("job_search_form"):
        search_term = st.text_input("Search Term (e.g., 'software engineer')")
        location = st.text_input("Location", value="United States")
        results_wanted = st.number_input("Number of Results", min_value=1, max_value=100, value=20)
        
        search_button = st.form_submit_button("Search Jobs")
        
        if search_button:
            try:
                # Call the backend API to search for jobs
                response = requests.post(
                    f"{API_URL}/api/jobs/search",
                    json={
                        "search_term": search_term,
                        "location": location,
                        "results_wanted": results_wanted
                    }
                )
                
                if response.status_code == 200:
                    st.success(response.json()["message"])
                else:
                    st.error(f"Error searching jobs: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Fetch and display recent jobs
    try:
        response = requests.get(f"{API_URL}/api/jobs/recent")
        if response.status_code == 200:
            jobs_data = response.json()
            
            if jobs_data["total_jobs"] > 0:
                st.subheader(f"Found {jobs_data['total_jobs']} Jobs")
                
                # Create a form for job selection
                with st.form("job_selection_form"):
                    selected_jobs = []
                    
                    for job in jobs_data["jobs"]:
                        # Create a unique key for each checkbox
                        job_id = job["_id"]
                        
                        # Create an expander for each job
                        with st.expander(f"{job['title']} at {job.get('company', 'N/A')}"):
                            # Display job details
                            st.write(f"**Location:** {job.get('location', 'N/A')}")
                            st.write(f"**Job Type:** {job.get('job_type', 'N/A')}")
                            st.write(f"**Posted:** {job.get('timestamp', 'N/A')}")
                            
                            if job.get('description'):
                                st.write("**Description:**")
                                st.write(job['description'])
                            
                            # Add checkbox for selection
                            if st.checkbox("Select this job", key=f"job_{job_id}"):
                                selected_jobs.append(job)
                    
                    # Submit button for selected jobs
                    if st.form_submit_button("Submit Selected Jobs"):
                        if selected_jobs:
                            st.success(f"Selected {len(selected_jobs)} jobs")
                            # Here you can add logic to handle the selected jobs
                            # For example, store them in a different collection or process them
                            st.json(selected_jobs)
                        else:
                            st.warning("Please select at least one job")
            else:
                st.info("No jobs found. Try searching for jobs first.")
                
    except Exception as e:
        st.error(f"Error fetching jobs: {str(e)}")

def clean_job_data(job):
    """Clean job data by replacing NaN values with None"""
    cleaned = {}
    for key, value in job.items():
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned

def view_saved_jobs():
    st.title("Saved Jobs")
    
    try:
        # Add debug information
        st.info("Fetching jobs from database...")
        
        # Fetch all jobs from the database
        response = requests.get(f"{API_URL}/api/jobs/recent")
        
        # Debug: Show raw response
        st.write("API Response Status:", response.status_code)
        
        if response.status_code == 200:
            jobs_data = response.json()
            
            # Debug: Show raw data
            st.write("Total jobs in response:", jobs_data["total_jobs"])
            
            if jobs_data["total_jobs"] > 0:
                # Add search and filter options
                search_term = st.text_input("Search in saved jobs", "")
                
                # Add sorting options
                sort_by = st.selectbox(
                    "Sort by",
                    ["Newest First", "Company Name", "Job Title"]
                )
                
                # Filter and sort jobs
                jobs = [clean_job_data(job) for job in jobs_data["jobs"]]
                
                # Debug: Show sample job
                if len(jobs) > 0:
                    st.write("Sample job data:", jobs[0])
                
                # Apply search filter if search term is provided
                if search_term:
                    jobs = [
                        job for job in jobs
                        if search_term.lower() in str(job.get('title', '')).lower() or 
                           search_term.lower() in str(job.get('company', '')).lower() or
                           search_term.lower() in str(job.get('location', '')).lower()
                    ]
                
                # Apply sorting
                if sort_by == "Company Name":
                    jobs.sort(key=lambda x: str(x.get('company', '')).lower())
                elif sort_by == "Job Title":
                    jobs.sort(key=lambda x: str(x.get('title', '')).lower())
                
                # Display total count
                st.subheader(f"Found {len(jobs)} Saved Jobs")
                
                # Display jobs in a clean format
                for job in jobs:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"### {job.get('title', 'No Title')}")
                            st.markdown(f"**Company:** {job.get('company', 'N/A')}")
                            st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                            
                            # Show job details in an expander
                            with st.expander("Show Details"):
                                st.markdown(f"**Job Type:** {job.get('job_type', 'N/A')}")
                                st.markdown(f"**Search Term:** {job.get('search_term', 'N/A')}")
                                
                                if job.get('description'):
                                    st.markdown("**Description:**")
                                    st.markdown(str(job['description']))
                                
                                # Display salary information if available
                                if job.get('min_amount') is not None or job.get('max_amount') is not None:
                                    st.markdown("**Salary Range:**")
                                    if job.get('min_amount') is not None:
                                        st.markdown(f"Minimum: {job['min_amount']}")
                                    if job.get('max_amount') is not None:
                                        st.markdown(f"Maximum: {job['max_amount']}")
                                
                                # Display timestamp in a readable format
                                if job.get('timestamp'):
                                    try:
                                        timestamp = datetime.fromisoformat(str(job['timestamp']).replace('Z', '+00:00'))
                                        st.markdown(f"**Posted:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                                    except Exception as e:
                                        st.markdown(f"**Posted:** {job['timestamp']}")
                        
                        with col2:
                            if job.get('job_url'):
                                st.markdown(f"[Apply Now]({job['job_url']})")
                        
                        st.markdown("---")
            else:
                st.warning("No jobs found in the database. Try searching for jobs first.")
        else:
            st.error(f"Error fetching jobs: {response.text}")
                
    except Exception as e:
        st.error(f"Error fetching saved jobs: {str(e)}")
        # Add more detailed error information
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")

def main():
    st.title("Resume Parser")
    
    # Sidebar menu
    st.sidebar.title("Navigation")
    options = ["Upload Resume", "View History", "Jobs", "Saved Jobs"]
    choice = st.sidebar.selectbox("Choose an option", options)
    
    if choice == "Upload Resume":
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
        
        # Submit button
        if st.button("Parse Resume", use_container_width=False):
            if uploaded_file is not None:
                # Send to backend API
                with st.spinner("Processing your resume..."):
                    try:
                        # Prepare the files and data for the API request
                        files = {
                            'cv_file': (uploaded_file.name, uploaded_file.getvalue(), f'application/{uploaded_file.type}')
                        }
                        data = {
                            'additional_info': additional_info if additional_info else ""
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
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except Exception as e:
                        st.error(f"Error connecting to the backend: {str(e)}")
            else:
                st.warning("Please upload your resume before submitting.")
    elif choice == "View History":
        st.header("Resume History")
        st.write("This section is under development.")
    elif choice == "Jobs":
        view_jobs()
    elif choice == "Saved Jobs":
        view_saved_jobs()

if __name__ == "__main__":
    main() 
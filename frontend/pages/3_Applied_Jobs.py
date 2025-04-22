import streamlit as st
import requests
from datetime import datetime
import math
from dotenv import load_dotenv
import os
import base64
import io

# Load environment variables
load_dotenv()

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("Applied Jobs")

def clean_job_data(job):
    """Clean job data by replacing NaN values with None"""
    cleaned = {}
    for key, value in job.items():
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned

def download_pdf(pdf_bytes, filename, label):
    """Helper function to create a download link with proper filename"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{label}</a>'
    return href

def display_applied_jobs(applied_data):
    """Helper function to display applied jobs"""
    for application in applied_data["applications"]:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                job = application.get("job_details", {})
                st.markdown(f"### {job.get('title', 'No Title')}")
                st.markdown(f"**Company:** {job.get('company', 'N/A')}")
                st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                st.markdown(f"**Applied Date:** {application.get('application_date', 'N/A')}")
                
                # Add download buttons for resume and cover letter
                col1a, col1b = st.columns(2)
                with col1a:
                    if application.get('resume_text'):
                        resume_bytes = base64.b64decode(application['resume_text'])
                        st.markdown(
                            download_pdf(resume_bytes, f"{job.get('company', 'company')}_resume.pdf", "📄 Download Resume"),
                            unsafe_allow_html=True
                        )
                with col1b:
                    if application.get('cover_letter_text'):
                        cl_bytes = base64.b64decode(application['cover_letter_text'])
                        st.markdown(
                            download_pdf(cl_bytes, f"{job.get('company', 'company')}_cover_letter.pdf", "📝 Download Cover Letter"),
                            unsafe_allow_html=True
                        )
                
                # Show job details in an expander
                with st.expander("Show Job Details"):
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
                    st.markdown(f"[View Job Posting]({job['job_url']})")
            
            st.markdown("---")

# Main execution
try:
    with st.spinner("Fetching applied jobs..."):
        applied_response = requests.get(f"{API_URL}/api/jobs/applied")
        if applied_response.status_code == 200:
            applied_jobs_data = applied_response.json()
            if applied_jobs_data["applications"]:
                display_applied_jobs(applied_jobs_data)
            else:
                st.info("No applied jobs found.")
        else:
            st.error(f"Error fetching applied jobs: {applied_response.text}")
except Exception as e:
    st.error(f"Error fetching saved jobs: {str(e)}")
    import traceback
    st.error(f"Detailed error: {traceback.format_exc()}") 
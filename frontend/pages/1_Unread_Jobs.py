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

st.title("Unread Jobs")

def fetch_unread_jobs():
    """Fetch unread jobs from the API with caching"""
    try:
        response = requests.get(f"{API_URL}/api/jobs/recent?is_read=false")
        if response.status_code == 200:
            return response.json()
        return {"jobs": []}
    except Exception as e:
        st.error(f"Error fetching unread jobs: {str(e)}")
        return {"jobs": []}

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

def display_jobs(jobs_data):
    """Helper function to display jobs"""
    # Extract unique company names for the filter
    all_jobs = [clean_job_data(job) for job in jobs_data["jobs"]]
    company_names = sorted(list(set(job.get('company', 'N/A') for job in all_jobs if job.get('company'))))
    company_names.insert(0, "All Companies") # Add 'All Companies' option
    
    # Add company filter dropdown
    selected_company = st.selectbox(
        "Filter by Company",
        company_names,
        key="company_filter_unread"
    )

    # Filter jobs based on selected company
    if selected_company == "All Companies":
        jobs = all_jobs
    else:
        jobs = [job for job in all_jobs if job.get('company') == selected_company]

    # Display total count of filtered jobs
    st.markdown(f"<h4 style='font-size: 14px;'>Found {len(jobs)} Unread Jobs</h4>", unsafe_allow_html=True)
    
    # Display jobs in a clean format
    if not jobs:
        st.info(f"No unread jobs found for {selected_company}.")
    else:
        for job in jobs:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {job.get('title', 'No Title')}")
                    st.markdown(f"**Company:** {job.get('company', 'N/A')}")
                    st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                    
                    # Create a form for each job
                    with st.form(key=f"form_{job.get('_id', '')}"):
                        # Add text area for additional instructions
                        additional_instructions = st.text_area(
                            "Additional Instructions for CV/Cover Letter",
                            key=f"instructions_{job.get('_id', '')}",
                            help="Add any specific instructions or requirements for customizing your CV and cover letter for this job"
                        )
                        
                        # Add toggle for document selection
                        col1e, col1f, col1g = st.columns([1, 1, 1])
                        with col1e:
                            apply_to_cv = st.checkbox("Apply to CV", key=f"apply_cv_{job.get('_id', '')}", value=True)
                        with col1f:
                            apply_to_cl = st.checkbox("Apply to Cover Letter", key=f"apply_cl_{job.get('_id', '')}", value=True)
                        
                        # Add Generate CV button
                        if st.form_submit_button("Generate CV"):
                            with st.spinner('Generating customized CV and Cover Letter...'):
                                try:
                                    response = requests.post(
                                        f"{API_URL}/customize-documents",
                                        json={
                                            "job_description": job.get('description', ''),
                                            "id": job.get('id', ''),
                                            "additional_instructions": additional_instructions,
                                            "apply_to_cv": apply_to_cv,
                                            "apply_to_cl": apply_to_cl
                                        }
                                    )
                                    
                                    if response.status_code == 200:
                                        data = response.json()
                                        st.success("Documents generated successfully!")
                                        
                                        # Store the generated documents in session state
                                        state_key = f"docs_{job.get('_id', '')}"
                                        st.session_state[state_key] = data
                                    else:
                                        st.error("Failed to generate documents. Please try again.")
                                except Exception as e:
                                    st.error(f"Error generating documents: {str(e)}")
                    
                    # Add download links if documents are available
                    state_key = f"docs_{job.get('_id', '')}"
                    if state_key in st.session_state:
                        data = st.session_state[state_key]
                        col1a, col1b, col1c, col1d = st.columns([1, 1, 1, 1])
                        with col1a:
                            if st.button("Applied", key=f"applied_{job.get('_id', '')}"):
                                try:
                                    # Get the generated documents
                                    docs = st.session_state[state_key]
                                    
                                    # Send application request
                                    response = requests.post(
                                        f"{API_URL}/api/jobs/apply",
                                        json={
                                            "job_id": str(job.get('_id')),
                                            "resume_text": docs.get('cv_content', ''),
                                            "cover_letter_text": docs.get('cover_letter_content', '')
                                        }
                                    )
                                    
                                    if response.status_code == 200:
                                        st.success("Successfully applied for the job!")
                                        # Remove the documents from session state to prevent re-application
                                        del st.session_state[state_key]
                                        st.rerun()
                                    else:
                                        st.error("Failed to apply for the job")
                                except Exception as e:
                                    st.error(f"Error applying for job: {str(e)}")
                        
                        # Display download links for available documents
                        if 'cv_content' in data:
                            with col1b:
                                cv_bytes = base64.b64decode(data['cv_content'])
                                st.markdown(
                                    download_pdf(cv_bytes, data.get('resume_filename', 'customized_cv.pdf'), "📄 Download CV"),
                                    unsafe_allow_html=True
                                )
                        
                        if 'cover_letter_content' in data:
                            with col1c:
                                cl_bytes = base64.b64decode(data['cover_letter_content'])
                                st.markdown(
                                    download_pdf(cl_bytes, data.get('cover_letter_filename', 'cover_letter.pdf'), "📝 Download Cover Letter"),
                                    unsafe_allow_html=True
                                )
                    else:
                        st.button("Applied", key=f"applied_{job.get('_id', '')}", disabled=True, 
                                 help="Generate CV and Cover Letter first")
                    
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

# Main execution
with st.spinner("Fetching unread jobs..."):
    unread_jobs_data = fetch_unread_jobs()
    if unread_jobs_data["jobs"]:
        display_jobs(unread_jobs_data)
    else:
        st.info("No unread jobs found.") 
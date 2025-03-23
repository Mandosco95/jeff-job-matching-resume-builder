import streamlit as st
import requests
from datetime import datetime
import math
from dotenv import load_dotenv
import os
import base64

# Load environment variables
load_dotenv()

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")


st.title("View Automation")

def clean_job_data(job):
    """Clean job data by replacing NaN values with None"""
    cleaned = {}
    for key, value in job.items():
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned

def display_pdf_viewer(pdf_base64, title):
    """Helper function to display PDF content"""
    pdf_display = F'<iframe src="data:application/pdf;base64,{pdf_base64}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(f"### {title}")
    st.markdown(pdf_display, unsafe_allow_html=True)

def view_saved_jobs():
    st.header("Saved Jobs")
    
    # Add clear jobs button in a container at the top
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("Clear All Jobs", type="primary", use_container_width=True):
                try:
                    response = requests.delete(f"{API_URL}/api/jobs/clear")
                    if response.status_code == 200:
                        st.success("Successfully cleared all jobs!")
                        st.rerun()  # Rerun the app to refresh the jobs list
                    else:
                        st.error(f"Error clearing jobs: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    try:
        # Fetch all jobs from the database
        with st.spinner("Fetching saved jobs..."):
            response = requests.get(f"{API_URL}/api/jobs/recent")
        
        if response.status_code == 200:
            jobs_data = response.json()

            
            if jobs_data["total_jobs"] > 0:
                # Add search and filter options
                search_term = st.text_input("Search in saved jobs", "")
                
                # Add remote jobs filter
                show_remote_only = st.checkbox("Show Remote Jobs Only")
                
                # Add sorting options
                sort_by = st.selectbox(
                    "Sort by",
                    ["Newest First", "Company Name", "Job Title"]
                )
                
                # Filter and sort jobs
                jobs = [clean_job_data(job) for job in jobs_data["jobs"]]
                
                # Apply search filter if search term is provided
                if search_term:
                    jobs = [
                        job for job in jobs
                        if search_term.lower() in str(job.get('title', '')).lower() or 
                           search_term.lower() in str(job.get('company', '')).lower() or
                           search_term.lower() in str(job.get('location', '')).lower()
                    ]
                
                # Apply remote filter if checked
                if show_remote_only:
                    remote_keywords = ['remote', 'work from home', 'wfh', 'virtual', 'telecommute']
                    jobs = [
                        job for job in jobs
                        if any(
                            keyword in str(job.get('title', '')).lower() or
                            keyword in str(job.get('description', '')).lower() or
                            keyword in str(job.get('job_type', '')).lower() or
                            keyword in str(job.get('location', '')).lower()
                            for keyword in remote_keywords
                        )
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
                                
                                # Add Generate CV button inside the expander
                                if st.button("Generate CV", key=f"gen_cv_{job.get('_id', '')}"):
                                    with st.spinner('Generating customized CV and Cover Letter...'):
                                        try:
                                            response = requests.post(
                                                f"{API_URL}/customize-documents",
                                                json={"job_description": job.get('description', '')}
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
                            
                            # Display CV and Cover Letter tabs if documents were generated
                            state_key = f"docs_{job.get('_id', '')}"
                            if state_key in st.session_state:
                                data = st.session_state[state_key]
                                
                                # Create tabs for CV and Cover Letter
                                cv_tab, cl_tab = st.tabs(["CV", "Cover Letter"])
                                
                                # Display CV in first tab
                                with cv_tab:
                                    display_pdf_viewer(
                                        data['cv_content'],
                                        "Customized CV"
                                    )
                                    st.download_button(
                                        "Download CV",
                                        data=base64.b64decode(data['cv_content']),
                                        file_name="customized_cv.pdf",
                                        mime="application/pdf",
                                        key=f"cv_download_{job.get('_id', '')}"
                                    )
                                
                                # Display Cover Letter in second tab
                                with cl_tab:
                                    display_pdf_viewer(
                                        data['cover_letter_content'],
                                        "Cover Letter"
                                    )
                                    st.download_button(
                                        "Download Cover Letter",
                                        data=base64.b64decode(data['cover_letter_content']),
                                        file_name="cover_letter.pdf",
                                        mime="application/pdf",
                                        key=f"cl_download_{job.get('_id', '')}"
                                    )
                        
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

view_saved_jobs()

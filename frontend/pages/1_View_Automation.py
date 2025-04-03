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

def download_pdf(pdf_bytes, filename, label):
    """Helper function to create a download link with proper filename"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{label}</a>'
    return href

def view_saved_jobs():
    # st.header("Saved Jobs")
    
    # Add clear jobs button in a container at the top
    # with st.container():
    #     col1, col2, col3 = st.columns([2, 1, 2])
    #     with col2:
    #         if st.button("Clear All Jobs", type="primary", use_container_width=True):
    #             try:
    #                 response = requests.delete(f"{API_URL}/api/jobs/clear")
    #                 if response.status_code == 200:
    #                     st.success("Successfully cleared all jobs!")
    #                     st.rerun()  # Rerun the app to refresh the jobs list
    #                 else:
    #                     st.error(f"Error clearing jobs: {response.text}")
    #             except Exception as e:
    #                 st.error(f"Error: {str(e)}")
    
    try:
        # Fetch all jobs from the database
        with st.spinner("Fetching saved jobs..."):
            response = requests.get(f"{API_URL}/api/jobs/recent")
        
        if response.status_code == 200:
            jobs_data = response.json()

            
            if jobs_data["total_jobs"] > 0:
                # Extract unique company names for the filter
                all_jobs = [clean_job_data(job) for job in jobs_data["jobs"]]
                company_names = sorted(list(set(job.get('company', 'N/A') for job in all_jobs if job.get('company'))))
                company_names.insert(0, "All Companies") # Add 'All Companies' option
                
                # Add company filter dropdown
                selected_company = st.selectbox(
                    "Filter by Company",
                    company_names,
                    key="company_filter"
                )

                # Filter jobs based on selected company
                if selected_company == "All Companies":
                    jobs = all_jobs
                else:
                    jobs = [job for job in all_jobs if job.get('company') == selected_company]

                # Display total count of filtered jobs
                st.markdown(f"<h4 style='font-size: 14px;'>Found {len(jobs)} Saved Jobs</h4>", unsafe_allow_html=True)
                
                # Display jobs in a clean format
                if not jobs:
                    st.info(f"No jobs found for {selected_company}.")
                else:
                    for job in jobs:
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"### {job.get('title', 'No Title')}")
                                st.markdown(f"**Company:** {job.get('company', 'N/A')}")
                                st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                                
                                # Add Generate CV button and download links
                                col1a, col1b, col1c = st.columns([1, 1, 1])
                                with col1a:
                                    if st.button("Generate CV", key=f"gen_cv_{job.get('_id', '')}"):
                                        with st.spinner('Generating customized CV and Cover Letter...'):
                                            try:
                                                # print(job)
                                                response = requests.post(
                                                    f"{API_URL}/customize-documents",
                                                    json={
                                                        "job_description": job.get('description', ''),
                                                        "id": job.get('id', '')
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
                                    with col1b:
                                        cv_bytes = base64.b64decode(data['cv_content'])
                                        st.markdown(
                                            download_pdf(cv_bytes, data.get('resume_filename', 'customized_cv.pdf'), "📄 Download CV"),
                                            unsafe_allow_html=True
                                        )
                                    with col1c:
                                        cl_bytes = base64.b64decode(data['cover_letter_content'])
                                        st.markdown(
                                            download_pdf(cl_bytes, data.get('cover_letter_filename', 'cover_letter.pdf'), "📝 Download Cover Letter"),
                                            unsafe_allow_html=True
                                        )
                                
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

view_saved_jobs()

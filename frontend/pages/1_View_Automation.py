import streamlit as st
import requests
from datetime import datetime
import math

API_URL = "http://localhost:8000"

st.title("View Automation")
st.write("This section is under development.") 

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

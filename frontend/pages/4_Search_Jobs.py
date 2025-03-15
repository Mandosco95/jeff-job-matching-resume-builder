import streamlit as st
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")


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


view_jobs()

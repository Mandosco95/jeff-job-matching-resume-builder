import streamlit as st

# Get query parameters
params = st._get_query_params()

# Check if the 'show_automate' parameter is set to 'true'
show_automate_param = params.get("show_automate")
if show_automate_param and show_automate_param[0] == "true":
    st.set_page_config(page_title="Automate Jobs", page_icon="🤖")
    st.title("🤖 Job Automation")
    st.write("This page is for automating job-related tasks.")
    
    # Add your automation logic here
    st.info("Automation features coming soon!")

else:
    st.error("Access denied. This page requires a specific query parameter to be viewed.")
    st.stop() 
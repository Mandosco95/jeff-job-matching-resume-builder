import streamlit as st
import requests
from dotenv import load_dotenv
import os
import base64

# Load environment variables
load_dotenv()

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")


st.set_page_config(
    page_title="Customizable CV & Cover Letter",
    page_icon=":envelope:",
    layout="wide",
    initial_sidebar_state="expanded",
)

def customize_documents():
    st.title("Customize your files based on the job")
    
    # Job description input
    job_description = st.text_area(
        "Enter The Job Description...",
        height=200,
        key="job_description"
    )
    
    # Create a form to prevent automatic rerun
    with st.form(key='customize_form'):
        submit_button = st.form_submit_button(label='Generate Documents')
        
        if submit_button:
            if not job_description:
                st.warning("Please enter a job description")
                return
                
            try:
                with st.spinner("Customizing your CV and Cover Letter..."):
                    response = requests.post(
                        f"{API_URL}/customize-documents",
                        json={
                            "job_description": job_description,
                        }
                    ).json()
                    
                    if response.get("success"):
                        st.success("Documents customized successfully!")
                        
                        # Store the PDFs in session state
                        st.session_state.resume_pdf = response["cv_content"]
                        st.session_state.cover_letter_pdf = response["cover_letter_content"]
                        
                        # Show preview and download buttons outside the form
                        st.session_state.show_downloads = True
                    else:
                        st.error("Failed to customize documents. Please try again.")
                        
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Display downloads and previews outside the form
    if st.session_state.get('show_downloads', False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Resume download and preview
            cv_bytes = base64.b64decode(st.session_state.resume_pdf)
            st.download_button(
                label="Download Customized CV",
                data=cv_bytes,
                file_name="customized_cv.pdf",
                mime="application/pdf",
                key="cv_download"
            )
            st.write("Preview of your customized CV:")
            st.write(f'<iframe src="data:application/pdf;base64,{st.session_state.resume_pdf}" width="100%" height="500px"></iframe>', unsafe_allow_html=True)
        
        with col2:
            # Cover letter download and preview
            cl_bytes = base64.b64decode(st.session_state.cover_letter_pdf)
            st.download_button(
                label="Download Cover Letter",
                data=cl_bytes,
                file_name="cover_letter.pdf",
                mime="application/pdf",
                key="cl_download"
            )
            st.write("Preview of your Cover Letter:")
            st.write(f'<iframe src="data:application/pdf;base64,{st.session_state.cover_letter_pdf}" width="100%" height="500px"></iframe>', unsafe_allow_html=True)

if __name__ == "__main__":
    customize_documents() 
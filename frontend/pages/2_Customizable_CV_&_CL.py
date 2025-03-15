import streamlit as st
import requests
from api_client import APIClient

st.set_page_config(
    page_title="Customizable CV & Cover Letter",
    page_icon=":envelope:",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.session_state["user_id"] = "66e166666666666666666666"

def customize_documents():
    st.title("Customize your files based on the job")
    
    # Get user ID from session state
    if "user_id" not in st.session_state:
        st.error("Please complete your profile first")
        return
    
    # Job description input
    job_description = st.text_area(
        "Enter The Job Description...",
        height=200
    )
    
    # Submit button
    if st.button("Submit"):
        if not job_description:
            st.warning("Please enter a job description")
            return
            
        try:
            api_client = APIClient()
            
            with st.spinner("Customizing your CV and Cover Letter..."):
                # Call API to generate customized documents
                response = api_client.customize_documents(
                    job_description=job_description,
                    user_id=st.session_state.user_id
                )
                
                if response.get("success"):
                    st.success("Documents customized successfully!")
                    
                    # Download buttons for generated documents
                    if "cv_content" in response:
                        st.download_button(
                            label="Download the new customized CV",
                            data=response["cv_content"],
                            file_name="customized_cv.pdf",
                            mime="application/pdf"
                        )
                    
                    if "cover_letter_content" in response:
                        st.download_button(
                            label="Download the new customized Cover letter",
                            data=response["cover_letter_content"],
                            file_name="customized_cover_letter.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.error("Failed to customize documents. Please try again.")
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    customize_documents() 
import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Main Streamlit application
def main():
    st.title("My Streamlit Application")
    
    # Sidebar menu
    st.sidebar.title("Menu")
    menu_option = st.sidebar.radio(
        "",
        ["PersonalInfo", "ViewAutomation", "Customizable CV & CL", "AskAI"]
    )
    
    # Main content based on menu selection
    if menu_option == "PersonalInfo":
        st.header("Personal Information")
        st.subheader("Give The AI all it needs to know about you")
        
        # Direct CV upload without extra click
        st.markdown("### Add your CV")
        uploaded_file = st.file_uploader("", 
                                       type=["pdf", "docx", "txt"],
                                       label_visibility="collapsed")
        
        if uploaded_file is not None:
            # Display success message and file info
            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            
            # Store the uploaded file in session state
            st.session_state.cv_file = uploaded_file
        
        # Text area for additional information
        additional_info = st.text_area(
            "Just randomly type what you think is not included in the CV that the AI should know about you, include anything.",
            height=200
        )
        
        # Submit button
        if st.button("Submit", use_container_width=False):
            if additional_info:
                # Check if CV was uploaded
                if uploaded_file is not None:
                    # Send to backend API
                    with st.spinner("Processing your CV..."):
                        try:
                            # Prepare the files and data for the API request
                            files = {
                                'cv_file': (uploaded_file.name, uploaded_file.getvalue(), f'application/{uploaded_file.type}')
                            }
                            data = {
                                'additional_info': additional_info
                            }
                            
                            # Make the API request
                            response = requests.post(f"{API_URL}/api/cv", files=files, data=data)
                            
                            # Check if request was successful
                            if response.status_code == 200:
                                result = response.json()
                                st.success("Information and CV submitted successfully!")
                                
                                # Display a summary of the processed data
                                with st.expander("View processed information"):
                                    st.write(f"**File:** {result['filename']}")
                                    st.write("**Extracted Text Preview:**")
                                    # Show first 500 characters of extracted text
                                    preview = result['extracted_text'][:500] + "..." if len(result['extracted_text']) > 500 else result['extracted_text']
                                    st.text_area("", preview, height=150, disabled=True)
                                    st.write("**Additional Information:**")
                                    st.write(result['additional_info'])
                            else:
                                st.error(f"Error: {response.status_code} - {response.text}")
                        except Exception as e:
                            st.error(f"Error connecting to the backend: {str(e)}")
                else:
                    st.warning("Please upload your CV before submitting.")
            else:
                st.warning("Please provide some additional information.")
    
    elif menu_option == "ViewAutomation":
        st.header("View Automation")
        st.write("This section is under development.")
        
    elif menu_option == "Customizable CV & CL":
        st.header("Customizable CV & Cover Letter")
        st.write("This section is under development.")
        
    elif menu_option == "AskAI":
        st.header("Ask AI")
        st.write("This section is under development.")

if __name__ == "__main__":
    main() 
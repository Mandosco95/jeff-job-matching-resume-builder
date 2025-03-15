import streamlit as st
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("Ask AI")

# Initialize session state for storing chat history and rerun flag
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

# Display chat history
for q, a in st.session_state['chat_history']:
    st.write(f"**You:** {q}")
    st.write(f"**AI:** {a}")

# Input for user question
question = st.text_input("Ask a question:")

# Button to submit the question
if st.button("Send") and not st.session_state['rerun']:
    if question:
        # Make a request to the backend API
        response = requests.post(
            f"{API_URL}/api/chat",
            json={"question": question}
        )
        
        # Get the response text
        if response.status_code == 200:
            answer = response.json().get("answer", "No answer available.")
        else:
            answer = "Error: Unable to get a response from the server."

        # Update chat history
        st.session_state['chat_history'].append((question, answer))
        
        # Set rerun flag to True
        st.session_state['rerun'] = True
        
        # Force a rerun to update the UI
        st.experimental_rerun()

# Reset rerun flag after rerun
st.session_state['rerun'] = False 
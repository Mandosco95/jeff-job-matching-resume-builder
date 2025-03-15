import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("Ask AI")
st.write("This section is under development.") 
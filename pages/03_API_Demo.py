import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px
from datetime import datetime

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from api_client import APIClient

st.title("API Integration Demo")

# Initialize API client
api_url = st.sidebar.text_input("API URL", value="http://localhost:8000")
api_client = APIClient(base_url=api_url)

st.sidebar.info("""
This page demonstrates how to integrate an external API with your Streamlit app.
Make sure the API server is running at the specified URL.

To start the API server:
cd api
pip install -r requirements.txt
python main.py
""")

# Create tabs for different API functionalities
tab1, tab2 = st.tabs(["Data Retrieval", "Predictions"])

with tab1:
    st.header("Fetch Data from API")
    
    # Try to get categories from API
    try:
        categories = api_client.get_categories()
        category_options = ["All"] + categories
        selected_category = st.selectbox("Filter by category:", category_options)
        
        limit = st.slider("Number of data points:", min_value=5, max_value=100, value=20)
        
        if st.button("Fetch Data"):
            with st.spinner("Fetching data from API..."):
                # Get data from API
                category_param = None if selected_category == "All" else selected_category
                response = api_client.get_data(category=category_param, limit=limit)
                
                # Display results
                st.success(f"Successfully retrieved {response['count']} data points")
                
                # Convert to DataFrame for display
                df = pd.DataFrame(response["data"])
                st.dataframe(df)
                
                # Create a visualization
                if not df.empty:
                    # Convert date strings to datetime
                    df['date'] = pd.to_datetime(df['date'])
                    
                    # Create a line chart grouped by category
                    fig = px.line(df, x='date', y='value', color='category', 
                                 title='Data from API by Category')
                    st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        st.info("Make sure the API server is running and accessible at the specified URL.")

with tab2:
    st.header("Make Predictions")
    
    try:
        # Get categories for the dropdown
        categories = api_client.get_categories()
        
        col1, col2 = st.columns(2)
        
        with col1:
            input_value = st.number_input("Input value:", min_value=0.0, max_value=1000.0, value=50.0)
        
        with col2:
            selected_category = st.selectbox("Select category:", categories)
        
        if st.button("Get Prediction"):
            with st.spinner("Calculating prediction..."):
                # Call the prediction API
                prediction = api_client.predict(input_value=input_value, category=selected_category)
                
                # Display results
                st.success("Prediction received!")
                
                # Create columns for the results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Predicted Value", f"{prediction['predicted_value']:.2f}")
                
                with col2:
                    st.metric("Confidence", f"{prediction['confidence']*100:.2f}%")
                
                st.info(prediction['message'])
                
                # Add some explanation
                st.write("""
                ### How this works
                
                This demonstration shows how your Streamlit app can:
                1. Send data to an external API
                2. Process the response
                3. Display the results in a user-friendly way
                
                In a real application, the API might be running a machine learning model,
                accessing a database, or performing other complex operations.
                """)
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        st.info("Make sure the API server is running and accessible at the specified URL.")
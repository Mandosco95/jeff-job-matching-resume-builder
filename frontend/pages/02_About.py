import streamlit as st

st.title("About This Application")

st.write("""
## Project Overview

This Streamlit application serves as a template for data visualization and analysis projects.
It demonstrates how to create a multi-page Streamlit application with various interactive features.

## Features

- **Data Exploration**: Visualize and analyze sample datasets
- **Interactive Elements**: Demonstrate Streamlit's widget capabilities
- **Multi-page Structure**: Organize content across multiple pages

## Technologies Used

- **Streamlit**: For the web application framework
- **Pandas**: For data manipulation
- **Matplotlib/Plotly**: For data visualization

## Getting Started

Check out the [README.md](https://github.com/yourusername/streamlit-app) file for installation and usage instructions.
""")

st.info("This is a template application. Customize it to fit your specific needs!")

# Contact form example
st.write("## Contact")

with st.form("contact_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    message = st.text_area("Message")
    
    submitted = st.form_submit_button("Submit")
    if submitted:
        st.success("Thanks for your message! This is a demo, so it wasn't actually sent anywhere.") 
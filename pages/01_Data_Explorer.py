import streamlit as st
import pandas as pd
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import load_sample_data, plot_time_series

st.title("Data Explorer")

# Load sample data
data = load_sample_data()

st.write("## Sample Dataset")
st.dataframe(data.head())

st.write("## Data Statistics")
st.write(data.describe())

st.write("## Time Series Visualization")
column = st.selectbox("Select column to visualize:", ["value_a", "value_b"])
fig = plot_time_series(data, column)
st.pyplot(fig)

st.write("## Filter by Category")
selected_category = st.multiselect(
    "Select categories:",
    options=data['category'].unique(),
    default=data['category'].unique()[0]
)

filtered_data = data[data['category'].isin(selected_category)]
st.dataframe(filtered_data) 
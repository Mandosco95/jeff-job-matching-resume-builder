import streamlit as st

# Main Streamlit application

def main():
    st.title("My Streamlit Application")
    
    st.write("""
    ## Welcome to my Streamlit app!
    
    This is a starter template for your Streamlit project.
    """)
    
    # Sidebar
    st.sidebar.header("Settings")
    option = st.sidebar.selectbox(
        "Choose a demo feature:",
        ["Data Visualization", "Interactive Widgets", "About"]
    )
    
    # Main content based on selection
    if option == "Data Visualization":
        st.header("Data Visualization Demo")
        st.write("Here you can add charts and data visualizations.")
        
        # Sample chart
        chart_data = {'x': [1, 2, 3, 4, 5], 'y': [10, 20, 15, 30, 25]}
        st.line_chart(chart_data)
        
    elif option == "Interactive Widgets":
        st.header("Interactive Widgets Demo")
        
        # Sample widgets
        name = st.text_input("Enter your name")
        if name:
            st.write(f"Hello, {name}!")
            
        age = st.slider("Select your age", 0, 100, 25)
        st.write(f"You selected: {age} years old")
        
        if st.button("Click me"):
            st.balloons()
            
    else:
        st.header("About This App")
        st.write("""
        This is a starter template for a Streamlit application.
        
        Streamlit is an open-source Python library that makes it easy to create
        and share beautiful, custom web apps for machine learning and data science.
        """)

if __name__ == "__main__":
    main() 
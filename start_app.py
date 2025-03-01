#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import argparse
import signal
import webbrowser
from threading import Thread

def start_api_server(api_dir="api", enable_reload=True):
    """Start the FastAPI server with optional hot reloading"""
    print("Starting API server...")
    os.chdir(api_dir)
    
    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("Installing API requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # Start the API server with reload flag if enabled
    reload_flag = ["--reload"] if enable_reload else []
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] + reload_flag
    )
    os.chdir("..")
    
    # Wait for API server to start
    print("Waiting for API server to start...")
    time.sleep(2)
    
    return api_process

def start_streamlit_app(enable_reload=True):
    """Start the Streamlit app with optional hot reloading"""
    print("Starting Streamlit app...")
    
    # Check if requirements are installed
    try:
        import streamlit
    except ImportError:
        print("Installing Streamlit requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # Start the Streamlit app with reload flag if enabled
    streamlit_cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    
    # Streamlit has hot reloading enabled by default, but we can add other flags if needed
    if enable_reload:
        os.environ["STREAMLIT_SERVER_RUN_ON_SAVE"] = "true"
    
    streamlit_process = subprocess.Popen(streamlit_cmd)
    
    # Wait for Streamlit to start
    print("Waiting for Streamlit app to start...")
    time.sleep(3)
    
    return streamlit_process

def open_browser(streamlit_port=8501, api_port=8000):
    """Open browser tabs for both applications"""
    streamlit_url = f"http://localhost:{streamlit_port}"
    api_url = f"http://localhost:{api_port}"
    api_docs_url = f"{api_url}/docs"
    
    print(f"Opening Streamlit app in browser: {streamlit_url}")
    webbrowser.open(streamlit_url)
    
    print(f"API documentation available at: {api_docs_url}")
    webbrowser.open(api_docs_url)

def main():
    parser = argparse.ArgumentParser(description="Start the Streamlit app and API server")
    parser.add_argument("--no-api", action="store_true", help="Don't start the API server")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--no-reload", action="store_true", help="Disable hot reloading")
    args = parser.parse_args()
    
    api_process = None
    streamlit_process = None
    
    # Determine if hot reloading should be enabled
    enable_reload = not args.no_reload
    
    try:
        # Start API server if requested
        if not args.no_api:
            api_process = start_api_server(enable_reload=enable_reload)
        
        # Start Streamlit app
        streamlit_process = start_streamlit_app(enable_reload=enable_reload)
        
        # Open browser if requested
        if not args.no_browser:
            # Start in a separate thread to avoid blocking
            Thread(target=lambda: open_browser()).start()
        
        print("\n✅ Application started successfully!")
        print("------------------------------------")
        print("📊 Streamlit app: http://localhost:8501")
        if not args.no_api:
            print("🚀 API server: http://localhost:8000")
            print("📚 API documentation: http://localhost:8000/docs")
        
        if enable_reload:
            print("\n🔄 Hot reloading is enabled - changes to your code will automatically reload the applications")
        
        print("\nPress Ctrl+C to stop all services\n")
        
        # Keep the script running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down services...")
    finally:
        # Clean up processes
        if api_process:
            print("Stopping API server...")
            api_process.terminate()
        
        if streamlit_process:
            print("Stopping Streamlit app...")
            streamlit_process.terminate()
        
        print("All services stopped.")

if __name__ == "__main__":
    main() 
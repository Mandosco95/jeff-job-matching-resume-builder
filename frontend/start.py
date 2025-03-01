#!/usr/bin/env python
import os
import subprocess

# Get the PORT environment variable, defaulting to 8501 if not set
port = os.environ.get('PORT', '8501')

# Print debug information
print(f"Starting Streamlit on port: {port}")

# Run Streamlit with the correct port
subprocess.run([
    'streamlit', 'run', 'app.py',
    '--server.port', port,
    '--server.address=0.0.0.0'
]) 
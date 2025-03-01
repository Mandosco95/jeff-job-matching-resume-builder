#!/usr/bin/env python
import os
import uvicorn

# Get the PORT environment variable from Railway, defaulting to 8000 if not set
port = int(os.environ.get('PORT', '8000'))

# Print debug information
print(f"Starting FastAPI server on port: {port}")

# Run the FastAPI application
uvicorn.run(
    "main:app", 
    host="0.0.0.0", 
    port=port
) 
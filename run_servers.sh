#!/bin/bash

# Run Backend
echo "Starting Backend Server..."
source backend/venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
deactivate

# Run Frontend
echo "Starting Frontend Server..."
source frontend/venv/bin/activate
streamlit run frontend/app.py &
FRONTEND_PID=$!
deactivate

# Wait for both processes to finish
wait $BACKEND_PID $FRONTEND_PID
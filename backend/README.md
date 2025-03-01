# Streamlit Demo API Backend

A simple FastAPI backend for demonstration with Streamlit.

## Features

- Sample data endpoint with filtering capabilities
- Prediction endpoint for demonstration
- Categories listing endpoint

## Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the server:
   ```
   python run.py
   ```

   Or use the Makefile:
   ```
   make run
   ```

## Development

For development, you can install the development dependencies:
```
pip install -r requirements-dev.txt
```

Run tests:
```
make test
```

Lint code:
```
make lint
```

Format code:
```
make format
```

## API Endpoints

- `GET /`: Welcome message
- `GET /api/data`: Get sample data with optional category filtering
- `POST /api/predict`: Make a prediction based on input value
- `GET /api/categories`: Get available categories

## API Documentation

Once the server is running, you can access the auto-generated API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 
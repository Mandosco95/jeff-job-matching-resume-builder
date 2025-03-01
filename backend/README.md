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

# Backend Deployment to Railway

This document provides instructions for deploying the FastAPI backend application to Railway.

## Prerequisites

1. A [Railway](https://railway.app/) account
2. [Railway CLI](https://docs.railway.app/develop/cli) installed (optional, but recommended)

## Deployment Steps

### Option 1: Deploy via Railway Dashboard

1. Log in to your Railway account
2. Create a new project
3. Select "Deploy from GitHub repo"
4. Connect your GitHub repository
5. Configure the following settings:
   - Root Directory: `backend`
   - Environment Variables:
     - `MONGODB_URL`: Your MongoDB connection string
     - Any other environment variables required by your application

### Option 2: Deploy via Railway CLI

1. Install Railway CLI:
   ```
   npm i -g @railway/cli
   ```

2. Login to Railway:
   ```
   railway login
   ```

3. Link to your project:
   ```
   railway link
   ```

4. Deploy the application:
   ```
   cd backend
   railway up
   ```

5. Set environment variables:
   ```
   railway variables set MONGODB_URL=your_mongodb_connection_string
   ```

## Environment Variables

- `MONGODB_URL`: MongoDB connection string
- `PORT`: Automatically set by Railway (do not set manually)

## Accessing Your Deployed Application

Once deployed, you can access your application at the URL provided by Railway in your project dashboard.

The API documentation will be available at `https://your-backend-url.railway.app/docs`.

## Connecting Frontend to Backend

After deploying both the frontend and backend, you'll need to update the frontend's `API_URL` environment variable to point to your deployed backend:

```
railway variables set API_URL=https://your-backend-url.railway.app
```

## Troubleshooting

- If you encounter any issues with the deployment, check the logs in the Railway dashboard.
- Ensure that your MongoDB database is accessible from Railway.
- Verify that all required environment variables are set correctly. 
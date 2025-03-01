# Frontend Deployment to Railway

This document provides instructions for deploying the Streamlit frontend application to Railway.

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
   - Root Directory: `frontend`
   - Environment Variables:
     - `API_URL`: URL of your backend API (e.g., `https://your-backend-url.railway.app`)

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
   cd frontend
   railway up
   ```

5. Set environment variables:
   ```
   railway variables set API_URL=https://your-backend-url.railway.app
   ```

## Environment Variables

- `API_URL`: URL of your backend API

## Accessing Your Deployed Application

Once deployed, you can access your application at the URL provided by Railway in your project dashboard.

## Troubleshooting

- If you encounter any issues with the deployment, check the logs in the Railway dashboard.
- Ensure that your backend API is also deployed and accessible.
- Verify that the `API_URL` environment variable is correctly set. 
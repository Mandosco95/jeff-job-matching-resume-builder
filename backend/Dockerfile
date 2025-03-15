FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install jobspy==0.29.0

COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "run.py"] 
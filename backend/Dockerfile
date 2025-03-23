FROM python:3.10-slim


# Install system dependencies including LaTeX
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure jobspy is installed
# RUN pip install jobspy==0.29.0

COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "run.py"] 
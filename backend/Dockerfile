# Use an official Python runtime with Debian (glibc) so binary wheels are available
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for some Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       git \
       curl \
       ca-certificates \
       libpq-dev \
       libffi-dev \
       libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip/setuptools/wheel before installing packages
RUN python -m pip install --upgrade pip setuptools wheel

# Copy only requirements first to leverage Docker cache

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies from the backend requirements file
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source into the image
COPY . /app

WORKDIR /app

# Expose port used by uvicorn
EXPOSE 8001

# Default command — run the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

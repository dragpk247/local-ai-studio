FROM python:3.12-slim

# Install necessary system dependencies (e.g. for building C-extensions or git access)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the requirements file into the container
COPY enterprise/requirements.txt .

# Install dependencies
RUN pip3 install -r requirements.txt

# Copy the core dashboard logic
COPY dashboard.py .

# Expose Streamlit port
EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Set entrypoint to run Streamlit in headless mode
ENTRYPOINT ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

# Use a base image with Python 3.9
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application code into the container
COPY chromadb/ .

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
        flask \
        chromadb[all] \
        openai

# Expose the port that the service will run on
EXPOSE 8001

# Set the environment variable for the OpenAI API key
# You can also set this at runtime using docker run -e OPENAI_API_KEY=your_api_key
ENV OPENAI_API_KEY=your-openai-api-key

# Start the Flask application
CMD ["python", "chroma_server.py"]

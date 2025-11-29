FROM python:3.11-slim

WORKDIR /app

# Install system deps (if any). Keep minimal for now.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 3001

CMD ["python", "-m", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "3001"]



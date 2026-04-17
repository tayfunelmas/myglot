FROM python:3.11-slim

WORKDIR /app

# Install deps first (layer cache)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy frontend
COPY frontend ./frontend

# Create mount points
RUN mkdir -p /app/data/audio /app/secrets

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

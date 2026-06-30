# ==========================================
# STAGE 1: Build Frontend (React)
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source code and build
COPY frontend/ .
RUN npm run build

# ==========================================
# STAGE 2: Build Backend & Serve
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (jika dibutuhkan)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements & install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh backend code
COPY backend/ .

# Copy build files dari Stage 1 (Frontend) ke folder static Backend
COPY --from=frontend-builder /app/frontend/dist /app/static

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

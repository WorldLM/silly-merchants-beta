FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p logs game_records

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD uvicorn main:app --host=0.0.0.0 --port=${PORT:-8000} 
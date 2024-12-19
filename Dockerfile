# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install alembic if not in requirements.txt
RUN pip install --no-cache-dir alembic pymysql

# Copy alembic configuration and migrations
COPY alembic.ini .
COPY alembic/ ./alembic/

# Copy application code
COPY app/ app/

# Default environment variables
ENV DB_HOST=mysql \
    DB_PORT=3306 \
    DB_NAME=chores-db \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Create an entrypoint script
# Copy entrypoint script first
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Run the application
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
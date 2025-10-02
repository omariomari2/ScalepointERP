FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-distutils \
    python3-dev \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install additional PostgreSQL dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    psycopg2-binary

# Copy the rest of the application
COPY . .

# Make sure our database fix script is included and executable
COPY cloud_db_fix.py /app/cloud_db_fix.py
RUN chmod +x /app/cloud_db_fix.py

# Create a non-root user and switch to it
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

# Make the entrypoint script executable
RUN chmod +x /app/docker-entrypoint.sh

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV SECRET_KEY="hard-to-guess-string"
# Database URL will be set in Cloud Run

# Create a volume for persistent data
VOLUME ["/app/instance"]

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8080

# Use the entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "wsgi:application"]

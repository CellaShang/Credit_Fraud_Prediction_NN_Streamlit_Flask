FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code, models, and logs directory
COPY . .

# Cloud Run requires listening on $PORT
ENV PORT=8080
EXPOSE 8080

# Use start.sh as entrypoint
CMD ["sh", "start.sh"]
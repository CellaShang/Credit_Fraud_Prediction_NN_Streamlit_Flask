FROM python:3.11-slim

WORKDIR /app

# Install TensorBoard
RUN pip install tensorboard

# Cloud Run injects PORT automatically
ENV PORT=${PORT:-8080}
EXPOSE $PORT

# Run TensorBoard using the PORT Cloud Run provides
CMD ["sh", "-c", "tensorboard --logdir gs://credit2025-tensorboard-logs/tensorboard --host 0.0.0.0 --port $PORT"]
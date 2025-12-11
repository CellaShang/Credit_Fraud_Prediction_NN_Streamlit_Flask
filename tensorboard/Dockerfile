FROM python:3.11-slim

WORKDIR /app

# Install TensorBoard
RUN pip install tensorboard

ENV PORT=8080
EXPOSE 8080
CMD ["tensorboard", "--logdir", "gs://credit2025-tensorboard-logs/tensorboard", "--host", "0.0.0.0", "--port", "8080"]

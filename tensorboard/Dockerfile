FROM python:3.11-slim

WORKDIR /app

# Install TensorBoard
RUN pip install tensorboard

# Cloud Run will inject PORT, default to 6006
ENV PORT=6006
EXPOSE 6006

# Run TensorBoard pointing at your GCS bucket
CMD ["tensorboard", "--logdir", "gs://credit2025-tensorboard-logs/tensorboard", "--host", "0.0.0.0", "--port", "6006"]

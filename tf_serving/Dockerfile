FROM tensorflow/serving:2.14.0

# Environment variables
ENV MODEL_NAME=fraud_model
ENV MODEL_BASE_PATH=gs://credit2025-models/fraud_model

# Cloud Run injects this
ENV PORT=${PORT:-8080}

EXPOSE $PORT

ENTRYPOINT ["sh", "-c", "\
    tensorflow_model_server \
    --rest_api_port=${PORT} \
    --model_name=${MODEL_NAME} \
    --model_base_path=${MODEL_BASE_PATH} \
"]

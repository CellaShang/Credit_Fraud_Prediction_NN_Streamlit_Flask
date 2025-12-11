FROM tensorflow/serving:2.14.0

# Model metadata
ENV MODEL_NAME=fraud_model
ENV MODEL_BASE_PATH=/models

# Copy locally saved_model into container
COPY saved_model /models/fraud_model

# Cloud Run port
ENV PORT=${PORT:-8080}
EXPOSE $PORT

# Wait until model exists, then start TF Serving
ENTRYPOINT ["sh", "-c", "\
  echo 'Waiting for model files...'; \
  while [ ! -f ${MODEL_BASE_PATH}/${MODEL_NAME}/1/saved_model.pb ]; do \
    sleep 2; \
  done; \
  echo 'Starting TensorFlow Serving...'; \
  tensorflow_model_server \
    --rest_api_port=${PORT} \
    --model_name=${MODEL_NAME} \
    --model_base_path=${MODEL_BASE_PATH}/${MODEL_NAME} \
"]

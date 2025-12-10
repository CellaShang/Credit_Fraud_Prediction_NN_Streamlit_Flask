# ------------------------------
# Help
# ------------------------------
help:
	@echo "Available targets:"
	@echo "  lint                  Run flake8 (non-blocking)"
	@echo "  format                Run black + isort (auto-fix, non-blocking)"
	@echo "  install-dev           Install dev requirements + pre-commit hooks"
	@echo "  build-<service>       Build Docker image for a service (flask, ui, serving, tensorboard)"
	@echo "  push-<service>        Push Docker image for a service"
	@echo "  deploy-<service>      Deploy a service to Cloud Run"
	@echo "  rollback-<service>    Rollback a service to previous revision"
	@echo "  pipeline-<service>    Full safe pipeline for a service"
	@echo "  pipeline-all          Run all service pipelines sequentially"

# ------------------------------
# Variables
# ------------------------------
PROJECT_ID=credit2025
REGION=us-central1

FLASK_IMAGE=gcr.io/$(PROJECT_ID)/fraud-api
UI_IMAGE=gcr.io/$(PROJECT_ID)/fraud-ui
SERVING_IMAGE=gcr.io/$(PROJECT_ID)/fraud-serving
TENSORBOARD_IMAGE=gcr.io/$(PROJECT_ID)/tensorboard

# ------------------------------
# Code Quality (Auto-fix + Non-blocking Lint)
# ------------------------------

format:
	@echo "Running Black auto-fix..."
	black . || true
	@echo "Running isort auto-fix..."
	isort . || true
	@echo "Formatting completed (errors ignored to continue pipeline)."

lint:
	@echo "Running flake8 (non-blocking)..."
	flake8 . || true
	@echo "Lint completed (errors ignored to continue pipeline)."

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# ------------------------------
# Docker Build
# ------------------------------
build-flask:
	docker build -t $(FLASK_IMAGE) flask/

build-ui:
	docker build -t $(UI_IMAGE) streamlit/

build-serving:
	docker build -t $(SERVING_IMAGE) tf_serving/

build-tensorboard:
	docker build -t $(TENSORBOARD_IMAGE) tensorboard/

build-all: build-flask build-ui build-serving build-tensorboard

# ------------------------------
# Docker Push
# ------------------------------
push-flask:
	docker push $(FLASK_IMAGE)

push-ui:
	docker push $(UI_IMAGE)

push-serving:
	docker push $(SERVING_IMAGE)

push-tensorboard:
	docker push $(TENSORBOARD_IMAGE)

push-all: push-flask push-ui push-serving push-tensorboard

# ------------------------------
# Deploy Cloud Run
# ------------------------------
deploy-flask:
	gcloud run deploy fraud-api \
		--image $(FLASK_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 8080 \
		--memory 1Gi

deploy-ui:
	gcloud run deploy fraud-ui \
		--image $(UI_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 8501 \
		--memory 1Gi

deploy-serving:
	gcloud run deploy fraud-serving \
		--image $(SERVING_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 8500 \
		--memory 2Gi

deploy-tensorboard:
	gcloud run deploy tensorboard \
		--image $(TENSORBOARD_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 6006 \
		--memory 1Gi

deploy-all: deploy-flask deploy-ui deploy-serving deploy-tensorboard

# ------------------------------
# Rollback
# ------------------------------
rollback-flask:
	@echo "Rolling back Flask..."
	gcloud run revisions list fraud-api --platform managed --region $(REGION)
	@echo "Use 'gcloud run services update-traffic fraud-api --to-revisions=<REVISION>:100' manually if needed"

rollback-ui:
	@echo "Rolling back UI..."
	gcloud run revisions list fraud-ui --platform managed --region $(REGION)
	@echo "Use 'gcloud run services update-traffic fraud-ui --to-revisions=<REVISION>:100' manually if needed"

rollback-serving:
	@echo "Rolling back TF Serving..."
	gcloud run revisions list fraud-serving --platform managed --region $(REGION)
	@echo "Use 'gcloud run services update-traffic fraud-serving --to-revisions=<REVISION>:100' manually if needed"

rollback-tensorboard:
	@echo "Rolling back Tensorboard..."
	gcloud run revisions list tensorboard --platform managed --region $(REGION)
	@echo "Use 'gcloud run services update-traffic tensorboard --to-revisions=<REVISION>:100' manually if needed"

# ------------------------------
# Full Safe Pipeline (per service)
# ------------------------------
pipeline-flask:
	$(MAKE) lint format
	$(MAKE) build-flask
	$(MAKE) push-flask
	-gcloud run deploy fraud-api \
		--image $(FLASK_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 8080 \
		--memory 1Gi || $(MAKE) rollback-flask

pipeline-ui:
	$(MAKE) lint format
	$(MAKE) build-ui
	$(MAKE) push-ui
	-gcloud run deploy fraud-ui \
		--image $(UI_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 8501 \
		--memory 1Gi || $(MAKE) rollback-ui

pipeline-serving:
	$(MAKE) lint format
	$(MAKE) build-serving
	$(MAKE) push-serving
	-gcloud run deploy fraud-serving \
		--image $(SERVING_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 8500 \
		--memory 2Gi || $(MAKE) rollback-serving

pipeline-tensorboard:
	$(MAKE) lint format
	$(MAKE) build-tensorboard
	$(MAKE) push-tensorboard
	-gcloud run deploy tensorboard \
		--image $(TENSORBOARD_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--port 6006 \
		--memory 1Gi || $(MAKE) rollback-tensorboard

pipeline-all: pipeline-flask pipeline-ui pipeline-serving pipeline-tensorboard

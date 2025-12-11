# ------------------------------
# Help
# ------------------------------
help:
	@echo "Available targets:"
	@echo "  lint                  Run flake8 (non-blocking)"
	@echo "  format                Run black + isort (non-blocking)"
	@echo "  install-dev           Install dev requirements + pre-commit hooks"
	@echo "  build-<service>       Build Docker image for a service (flask, ui, serving, tensorboard)"
	@echo "  push-<service>        Push Docker image for a service"
	@echo "  deploy-<service>      Deploy a service to Cloud Run"
	@echo "  rollback-<service>    Rollback a service manually"
	@echo "  pipeline-<service>    Full pipeline per service"

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
# Auth Checks
# ------------------------------
check-gcloud-auth:
	@echo "Checking gcloud authentication..."
	@gcloud auth list --filter=status:ACTIVE --format="value(account)" >/dev/null || (echo "No active gcloud account. Run 'gcloud auth login'" && exit 1)
	@echo "gcloud authentication OK."

check-docker-auth:
	@echo "Checking Docker access to GCR..."
	@docker info >/dev/null || (echo "Docker not running or not accessible" && exit 1)
	@gcloud auth configure-docker >/dev/null
	@echo "Docker authentication OK."

check-gcloud-project:
	@CURRENT_PROJECT=$$(gcloud config get-value project) ; \
	if [ "$$CURRENT_PROJECT" != "$(PROJECT_ID)" ]; then \
	  echo "Current gcloud project is $$CURRENT_PROJECT, expected $(PROJECT_ID). Aborting." ; exit 1 ; \
	else \
	  echo "Gcloud project verified: $$CURRENT_PROJECT" ; \
	fi

check-ui-secrets:
	@echo "Checking secrets for UI..."
	@gcloud secrets versions access latest --secret=gcs-service-account-key >/dev/null || (echo "UI secret not accessible. Aborting." && exit 1)
	@echo "UI secrets verified."

# ------------------------------
# Code Quality
# ------------------------------
format:
	@echo "Running Black auto-fix..."
	black . || true
	@echo "Running isort auto-fix..."
	isort . || true
	@echo "Formatting done (errors ignored)."

lint:
	@echo "Running flake8..."
	flake8 . || true
	@echo "Lint done (errors ignored)."

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

# ------------------------------
# Deploy Cloud Run
# ------------------------------
deploy-flask:
	gcloud run deploy fraud-api \
		--image $(FLASK_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 1Gi

deploy-ui:
	gcloud run deploy fraud-ui \
		--image $(UI_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 1Gi \
		--set-secrets "/secrets/gcs_service_account.json=gcs-service-account-key:latest"

deploy-serving:
	gcloud run deploy fraud-serving \
		--image $(SERVING_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 2Gi

deploy-tensorboard:
	gcloud run deploy tensorboard \
		--image $(TENSORBOARD_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 1Gi

# ------------------------------
# Rollback (manual, time/version-based)
# ------------------------------
rollback-flask:
	@echo "Listing revisions for Flask..."
	gcloud run revisions list fraud-api --platform managed --region $(REGION)
	@echo "Use: gcloud run services update-traffic fraud-api --to-revisions=<REVISION>:100"

rollback-ui:
	@echo "Listing revisions for UI..."
	gcloud run revisions list fraud-ui --platform managed --region $(REGION)
	@echo "Use: gcloud run services update-traffic fraud-ui --to-revisions=<REVISION>:100"

rollback-serving:
	@echo "Listing revisions for TF Serving..."
	gcloud run revisions list fraud-serving --platform managed --region $(REGION)
	@echo "Use: gcloud run services update-traffic fraud-serving --to-revisions=<REVISION>:100"

rollback-tensorboard:
	@echo "Listing revisions for TensorBoard..."
	gcloud run revisions list tensorboard --platform managed --region $(REGION)
	@echo "Use: gcloud run services update-traffic tensorboard --to-revisions=<REVISION>:100"

# ------------------------------
# Full Service Pipelines
# ------------------------------
pipeline-flask: check-gcloud-auth check-docker-auth check-gcloud-project
	$(MAKE) lint format
	$(MAKE) build-flask
	$(MAKE) push-flask
	-gcloud run deploy fraud-api \
		--image $(FLASK_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 1Gi || true

pipeline-ui: check-gcloud-auth check-docker-auth check-gcloud-project check-ui-secrets
	$(MAKE) lint format
	$(MAKE) build-ui
	$(MAKE) push-ui
	-gcloud run deploy fraud-ui \
		--image $(UI_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 1Gi \
		--set-secrets "/secrets/gcs_service_account.json=gcs-service-account-key:latest" || true

pipeline-serving: check-gcloud-auth check-docker-auth check-gcloud-project
	$(MAKE) lint format
	$(MAKE) build-serving
	$(MAKE) push-serving
	-gcloud run deploy fraud-serving \
		--image $(SERVING_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 2Gi || true

pipeline-tensorboard: check-gcloud-auth check-docker-auth check-gcloud-project
	$(MAKE) lint format
	$(MAKE) build-tensorboard
	$(MAKE) push-tensorboard
	-gcloud run deploy tensorboard \
		--image $(TENSORBOARD_IMAGE) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 1Gi || true


# ------------------------------
# Full Pipeline (All Services Sequentially)
# ------------------------------
pipeline-all: pipeline-flask pipeline-ui pipeline-serving pipeline-tensorboard
	@echo "All services pipeline completed."

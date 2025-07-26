.PHONY: install test lint run build push clean

# Variables
DOCKER_IMAGE ?= gamebot
DOCKER_TAG ?= latest

# Install dependencies
install:
	pip install -r requirements-dev.txt

# Run tests
TEST_PATH=./tests
test:
	pytest -v --cov=. --cov-report=term-missing $(TEST_PATH)

# Run linter
lint:
	flake8 .

# Run the application locally
run:
	uvicorn server:main --reload --host 0.0.0.0 --port 8000

# Build Docker image
build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run Docker container
docker-run: build
	docker run -p 8000:8000 \
	  -e OPENAI_API_KEY=$(OPENAI_API_KEY) \
	  -e VECTOR_STORE_ID=$(VECTOR_STORE_ID) \
	  -e ALLOWED_ORIGINS=* \
	  $(DOCKER_IMAGE):$(DOCKER_TAG)

# Run with docker-compose
docker-compose-up:
	docker-compose up --build

# Push Docker image to registry
push:
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)

# Clean up
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete
	find . -type f -name '*~' -delete

docker-clean:
	docker system prune -f

docker-clean-all: docker-clean
	docker rmi -f $(docker images -a -q) || true

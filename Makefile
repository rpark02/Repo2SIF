.PHONY: build build-simple

IMAGE_NAME := repo2docker-tool:latest

buildx: ## Build the Docker image using buildx
	docker buildx build --load -t $(IMAGE_NAME) --platform=linux/amd64 .

buildx: ## Build the Docker image using build
	DOCKER_BUILDKIT=0 docker build --load -t $(IMAGE_NAME) --platform=linux/amd64 .

build-simple: ## Build the Docker image using regular docker build (fallback if buildx has issues)
	DOCKER_BUILDKIT=0 docker build -t $(IMAGE_NAME) .

.PHONY: test-local test-github test-gitlab

test-local: build ## Test with a local repository (example)
	@echo "Example: ./repo2docker --input /path/to/repo --output ./out"
	@echo "Run: ./repo2docker --input <local_path> --output <output_dir> [--sif]"

test-github: build ## Test with a GitHub repository (example)
	@echo "Example: ./repo2docker --input https://github.com/user/repo --output ./out"
	@echo "Run: ./repo2docker --input <git_url> --output <output_dir> [--sif]"

test-gitlab: build ## Test with a GitLab repository (example)
	@echo "Example: ./repo2docker --input https://gitlab.com/user/repo --output ./out"
	@echo "Run: ./repo2docker --input <git_url> --output <output_dir> [--sif]"



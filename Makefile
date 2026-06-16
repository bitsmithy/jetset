.PHONY: run debug test lint fixtures deploy setup-pi start debug-start

# Local dev
run:   ## Run the emulator smoke test
	uv run python -m jetset

debug: ## Run with debug logging
	JETSET_DEBUG=1 uv run python -m jetset

test:  ## Run all tests
	uv run pytest -v

lint:  ## Lint and format check
	uv run ruff check src/

fixtures: ## Save live AeroAPI response as test fixture
	uv run python scripts/save_fixtures.py

# Pi Deployment
JETSET_USER ?= hao
JETSET_HOST ?= jetset.local
JETSET_PATH ?= /home/$(JETSET_USER)/jetset

deploy: ## rsync code to Pi
	rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '.git' \
		--exclude '*.pyc' --exclude 'wheels' \
		. $(JETSET_USER)@$(JETSET_HOST):$(JETSET_PATH)/

setup-pi: ## Setup Pi deps via SSH (clone, build, uv add)
	cat scripts/setup-pi.sh | ssh $(JETSET_USER)@$(JETSET_HOST) "bash -s"

start: ## Run on Pi via SSH (needs root for GPIO)
	ssh -t $(JETSET_USER)@$(JETSET_HOST) "cd $(JETSET_PATH) && sudo -E env PATH=\\$PATH uv run python -m jetset"

debug-start: ## Run on Pi via SSH with debug logging
	ssh -t $(JETSET_USER)@$(JETSET_HOST) "cd $(JETSET_PATH) && sudo -E env PATH=\\$PATH JETSET_DEBUG=1 uv run python -m jetset"

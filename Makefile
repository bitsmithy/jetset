.PHONY: run debug test lint fixtures deploy setup-pi run-pi debug-pi

# Local dev
run:   ## Run the emulator smoke test
	uv run python -m jetset

debug: ## Run with debug logging
	JETSET_DEBUG=1 uv run python -m jetset

test:  ## Run all tests
	uv run pytest -v

lint:  ## Lint and format check
	uv run ruff check src/

fixtures: ## Save a live AirLabs response as a test fixture
	uv run python scripts/save_fixtures.py

# Pi Deployment
JETSET_USER ?= pi
JETSET_HOST ?= jetset.local
JETSET_PATH ?= /home/$(JETSET_USER)/jetset

deploy: ## rsync to the Pi, run first-time setup if needed, restart the service
	rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '.git' \
		--exclude '*.pyc' --exclude 'wheels' \
		--exclude '.pytest_cache' --exclude '.ruff_cache' \
		. $(JETSET_USER)@$(JETSET_HOST):$(JETSET_PATH)/
	ssh -t $(JETSET_USER)@$(JETSET_HOST) \
		"cd $(JETSET_PATH) && \
		 { [ -f /etc/systemd/system/jetset.service ] || bash scripts/setup-pi.sh; } && \
		 sudo systemctl restart jetset"

setup-pi: ## Install deps and build rpi-rgb-led-matrix (run on the Pi)
	bash scripts/setup-pi.sh

run-pi: ## Run the app on the Pi (needs root for GPIO)
	sudo -E env PATH="$$PATH" uv run python -m jetset

debug-pi: ## Run the app on the Pi with debug logging
	sudo -E env PATH="$$PATH" JETSET_DEBUG=1 uv run python -m jetset

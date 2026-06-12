.PHONY: run test lint fixtures

run:   ## Run the emulator smoke test
	uv run python -m jetset

test:  ## Run all tests
	uv run pytest -v

lint:  ## Lint and format check
	uv run ruff check src/

fixtures: ## Save live AeroAPI response as test fixture
	uv run python scripts/save_fixtures.py

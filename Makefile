.PHONY: run test lint

run:   ## Run the emulator smoke test
	uv run python -m jetset

test:  ## Run all tests
	uv run pytest -v

lint:  ## Lint and format check
	uv run ruff check src/

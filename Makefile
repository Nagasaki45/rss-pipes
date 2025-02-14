unit-test:
	uv run python -m pytest

lint:
	uv run ruff format --check
	uv run ruff check

format:
	uv run ruff format
	uv run ruff check --fix

type-check:
	uv run mypy .
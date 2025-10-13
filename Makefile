SHELL := pwsh.exe
.PHONY: test typecheck ruff lint check

test:
	uv run pytest -q

typecheck:
	uv run mypy src

ruff:
	uv run ruff check .

lint: ruff typecheck

check: lint test

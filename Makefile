
.PHONY: test typecheck ruff lint check format clean test-cov deps complexity

# Install/sync dependencies (only if pyproject.toml changed)
uv.lock: pyproject.toml
	uv sync --group dev

# Run tests (quiet)
test: uv.lock
	uv run pytest -q

# Run tests with coverage report
test-cov: uv.lock
	@echo "Running tests with coverage..."
	uv run pytest tests/ --cov=src/mentat --cov-report=term-missing --cov-report=html:.htmlcov -v

# Type checking
typecheck:
	uv run mypy src

# Check code complexity with radon
complexity: uv.lock
	@echo "Analyzing code complexity..."
	@echo "=== Cyclomatic Complexity Overview ==="
	uv run radon cc src/ --average --show-complexity
	@echo ""
	@echo "=== Methods with B+ Complexity (if any) ==="
	uv run radon cc src/ --show-complexity --min=B || echo "✅ No methods with B+ complexity found!"
	@echo ""
	@echo "=== Complexity Legend ==="
	@echo "A (1-5): ✅ Excellent    C (11-20): ⚠️  Moderate"
	@echo "B (6-10): ✅ Good        D (21-30): 🔴 High"
	@echo "                         E (31+): 💀 Very High"

# Format code (ruff handles both formatting and import sorting)
format: uv.lock
	@echo "Formatting code with ruff..."
	uv run ruff format .
	@echo "Organizing imports with ruff..."
	uv run ruff check --fix .
	@echo "Code formatting completed!"

# Clean Python cache files and build artifacts
clean:
	@echo "Cleaning Python cache files..."
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage .htmlcov/ .pytest_cache/ .ruff_cache/ .mypy_cache/ dist/ build/
	@echo "Clean completed!"

lint: typecheck format

check: test lint


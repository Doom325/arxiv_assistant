.PHONY: test test-unit test-fast lint check

# Run all tests
test:
	python -m pytest tests/ -v --tb=short

# Run unit tests only (exclude tests requiring external services)
test-unit:
	python -m pytest tests/ -v --tb=short -k "not remote and not live and not mlx"

# Run unit tests, stop on first failure
test-fast:
	python -m pytest tests/ -v --tb=short -x -k "not remote and not live and not mlx"

# Syntax check critical files
lint:
	python -m py_compile models.py
	python -m py_compile config.py
	python -m py_compile database.py
	python -m py_compile main.py
	python -m py_compile production_worker.py
	python -m py_compile scheduler.py
	@echo "All critical files compile successfully."

# Verify imports work (quick sanity check)
check:
	python -c "from models import Paper, User, Base"
	python -c "from database import get_db"
	python -c "from config import settings"
	python -c "import main"
	@echo "All import checks passed."

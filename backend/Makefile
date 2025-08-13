.PHONY: test test-fast clean-testdb cov

# Activate virtual environment if it exists
VENV_ACTIVATE = source ../venv/bin/activate || true

test:
	$(VENV_ACTIVATE) && TESTING=true SECRET_KEY="test-secret-key-for-testing-only" USE_DEMO_CONTENT=false CONTENT_DATA_DIR="../data/real_content" pytest

test-fast:
	$(VENV_ACTIVATE) && TESTING=true SECRET_KEY="test-secret-key-for-testing-only" USE_DEMO_CONTENT=false CONTENT_DATA_DIR="../data/real_content" pytest -q -k "not slow"

clean-testdb:
	rm -f test.db

cov:
	$(VENV_ACTIVATE) && TESTING=true SECRET_KEY="test-secret-key-for-testing-only" USE_DEMO_CONTENT=false CONTENT_DATA_DIR="../data/real_content" pytest --cov=backend --cov-report=html --cov-report=term

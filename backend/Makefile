.PHONY: test test-fast clean-testdb cov auto-tag auto-tag-dry labels-smoke db-invariants

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

# Auto-tagging targets
auto-tag:
	$(VENV_ACTIVATE) && \
	PYTHONPATH=.. LABELS_ENABLED=true SECRET_KEY="auto-tag-secret-key" DATABASE_URL="sqlite+aiosqlite:///../test.db" python -m backend.scripts.auto_tag_labels

auto-tag-dry:
	$(VENV_ACTIVATE) && \
	PYTHONPATH=.. LABELS_ENABLED=true SECRET_KEY="auto-tag-secret-key" DATABASE_URL="sqlite+aiosqlite:///../test.db" python -m backend.scripts.auto_tag_labels --dry-run

labels-smoke:
	$(VENV_ACTIVATE) && \
	PYTHONPATH=.. LABELS_ENABLED=true SECRET_KEY="auto-tag-secret-key" DATABASE_URL="sqlite+aiosqlite:///../test.db" python -m backend.scripts.labels_smoke

db-invariants:
	$(VENV_ACTIVATE) && \
	PYTHONPATH=.. LABELS_ENABLED=true SECRET_KEY="db-invariants-secret-key" DATABASE_URL="sqlite+aiosqlite:///../test.db" python -m backend.scripts.check_db_invariants

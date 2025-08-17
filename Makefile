.PHONY: dev-deps offline-deps test test-docker build-test-image fix-old-directions

dev-deps:
	python3 -m pip install -r requirements-dev.txt

offline-deps:
	bash tools/install_offline.sh

test:
	pytest -q

build-test-image:
	docker build -f Dockerfile.test -t commons-tests .

test-docker: build-test-image
	docker run --rm commons-tests

fix-old-directions:
	@echo "🧹 Cleaning up old Level-A direction strings..."
	@cd backend && source ../venv/bin/activate && python scripts/cleanup_old_directions.py --dry-run
	@echo ""
	@if [ "$(FORCE)" = "1" ]; then \
		echo "🚀 Applying changes (FORCE=1)..."; \
		cd backend && source ../venv/bin/activate && python scripts/cleanup_old_directions.py --force; \
	else \
		echo "💡 To apply changes, run: make fix-old-directions FORCE=1"; \
	fi

seed-labels:
	@echo "🏷️ Seeding default labels..."
	@cd backend && source ../venv/bin/activate && python scripts/seed_labels.py

seed-stress: seed-labels
	@echo "🌱 Seeding stress test data..."
	@cd backend && source ../venv/bin/activate && python scripts/seed_stress_labels.py
	@cd backend && source ../venv/bin/activate && python scripts/seed_stress_polls.py
	@echo "✅ Stress seeding complete!"

wipe-dev:
	@echo "⚠️  Wiping development data (polls, labels, poll_labels)..."
	@if [ "$(FORCE)" = "1" ]; then \
		echo "🗑️  Truncating tables..."; \
		cd backend && source ../venv/bin/activate && python -c "import asyncio; from backend.database import get_db; asyncio.run((lambda: [db.execute('DELETE FROM poll_labels'), db.execute('DELETE FROM polls'), db.execute('DELETE FROM labels')])())"; \
	else \
		echo "💡 To actually wipe data, run: make wipe-dev FORCE=1"; \
	fi

labels-check-dupes:
	@echo "🔍 Checking for duplicate poll-label relationships..."
	@source .venv/bin/activate && python -m backend.scripts.find_dup_poll_labels

labels-fix:
	@echo "🔧 Running migration to remove duplicates and add unique constraint..."
	@source .venv/bin/activate && alembic upgrade head
	@echo "✅ Migration complete!"
	@echo "🔍 Verifying no duplicates remain..."
	@source .venv/bin/activate && python -m backend.scripts.find_dup_poll_labels

topics-ids:
	@echo "🔍 Getting raw topic data for slug=$(slug)..."
	@source .venv/bin/activate && curl -s "http://localhost:8000/api/dev/labels/$(slug)/raw" | python -m json.tool

perf-refresh:
	@echo "⚡ Refreshing performance metrics..."
	@python3 scripts/sim_override_load.py --requests 400
	@python3 backend/scripts/collect_override_latency.py --json-out reports/override_latency.json
	@echo "✅ Performance metrics refreshed!"

#!/bin/bash
set -e

DATE=$(date +"%Y-%m-%d")
RELEASE_TAG="${DATE}-stable"
NOTES_DIR="release_notes"
NOTES_FILE="${NOTES_DIR}/${DATE}-readiness.md"

mkdir -p "$NOTES_DIR"

echo "# Release Readiness Report – ${DATE}" > "$NOTES_FILE"
echo >> "$NOTES_FILE"

## 1. Git Status
echo "=== 1. Git Status Check ==="
git status docker-compose.prod.yml | tee -a "$NOTES_FILE"
echo >> "$NOTES_FILE"

## 2. Test Suite
echo "=== 2. Test Suite Results ==="
docker compose -f docker-compose.prod.yml exec web pytest --maxfail=1 --disable-warnings -q | tee -a "$NOTES_FILE" || true
echo >> "$NOTES_FILE"

## 3. Monitoring
echo "=== 3. Container Resource Usage ==="
docker stats --no-stream | tee -a "$NOTES_FILE"
echo >> "$NOTES_FILE"

## 4. Database Size & Growth
echo "=== 4. Database Backup Size ==="
ls -lh backups/prod-*/database_backup.sql | tee -a "$NOTES_FILE"
echo >> "$NOTES_FILE"

echo "=== 4b. Table Overview ==="
docker compose -f docker-compose.prod.yml exec db psql -U postgres -d the_commons -c "\dt+" | tee -a "$NOTES_FILE"
echo >> "$NOTES_FILE"

## 5. Security Review (manual)
echo "=== 5. Security Review Notes ===" | tee -a "$NOTES_FILE"
read -p "Review JWT/OAuth2 flows for expiry, refresh, and revocation – any changes needed? " SECURITY_NOTES
echo "$SECURITY_NOTES" >> "$NOTES_FILE"
echo >> "$NOTES_FILE"

## 6. User Access Plan (manual)
echo "=== 6. First User Onboarding Plan ===" | tee -a "$NOTES_FILE"
read -p "How will first real users be onboarded? " USER_PLAN
echo "$USER_PLAN" >> "$NOTES_FILE"
echo >> "$NOTES_FILE"

## 7. Frontend/UI Check
echo "=== 7. Frontend/UI Status ==="
FRONTEND=$(docker compose ps | grep -i front || true)
if [ -z "$FRONTEND" ]; then
  echo "No frontend container detected – API-only interaction" | tee -a "$NOTES_FILE"
else
  echo "$FRONTEND" | tee -a "$NOTES_FILE"
fi
echo >> "$NOTES_FILE"

## 8. Deployment Target (manual)
echo "=== 8. Deployment Target ===" | tee -a "$NOTES_FILE"
grep -i "ports:" docker-compose.prod.yml | tee -a "$NOTES_FILE"
read -p "Confirm final host/domain for production: " DEPLOY_TARGET
echo "Deployment Target: $DEPLOY_TARGET" >> "$NOTES_FILE"
echo >> "$NOTES_FILE"

echo "=== Release Readiness Checklist Complete ===" | tee -a "$NOTES_FILE"
echo "Full report saved to $NOTES_FILE"
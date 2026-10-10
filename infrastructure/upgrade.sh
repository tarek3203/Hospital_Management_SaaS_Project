#!/usr/bin/env bash
# Upgrade an installed CityCare HMS: back up, rebuild the app image, restart, migrate.
#   ./infrastructure/upgrade.sh
set -euo pipefail
cd "$(dirname "$0")/.."
COMPOSE=(docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env)
SITE=$(grep '^SITE_NAME=' infrastructure/.env | cut -d= -f2-)

echo "Backing up ${SITE} first..."
docker exec hms-backend-1 bench --site "$SITE" backup --with-files
git pull --ff-only
docker build -f infrastructure/Containerfile -t hms/app:v16 .
"${COMPOSE[@]}" up -d
docker exec hms-backend-1 bench --site "$SITE" migrate
docker exec hms-backend-1 bench --site "$SITE" clear-cache
"${COMPOSE[@]}" restart frontend
echo "Upgrade done. Backups are in sites/${SITE}/private/backups inside the sites volume."

#!/usr/bin/env bash
# Save the current demo site as the "clean" state that reset.sh restores.
# Run inside the backend container after loading demo data:
#   docker exec hms-backend-1 bash /home/frappe/demo/snapshot.sh
set -euo pipefail
cd /home/frappe/frappe-bench
SITE="${SITE_NAME:-hms.localhost}"
SNAP="/home/frappe/frappe-bench/sites/demo-snapshot"

rm -rf "$SNAP"
mkdir -p "$SNAP"
bench --site "$SITE" backup --with-files \
	--backup-path-db "$SNAP/db.sql.gz" \
	--backup-path-files "$SNAP/public.tar" \
	--backup-path-private-files "$SNAP/private.tar" \
	--backup-path-conf "$SNAP/site_config.json"
date -u +%FT%TZ > "$SNAP/taken_at"
echo "Snapshot saved to $SNAP"

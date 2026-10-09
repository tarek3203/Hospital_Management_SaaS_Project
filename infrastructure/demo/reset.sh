#!/usr/bin/env bash
# Restore the demo site to its snapshot, so visitor changes do not pile up.
# The demo-reset compose service runs this every RESET_INTERVAL_HOURS.
set -euo pipefail
cd /home/frappe/frappe-bench
SITE="${SITE_NAME:-hms.localhost}"
SNAP="/home/frappe/frappe-bench/sites/demo-snapshot"
SITE_DIR="/home/frappe/frappe-bench/sites/$SITE"

if [ ! -f "$SNAP/db.sql.gz" ]; then
	echo "No snapshot at $SNAP, run snapshot.sh first" >&2
	exit 1
fi

bench --site "$SITE" set-maintenance-mode on
# Never leave the demo stuck in maintenance mode if a step fails.
trap 'bench --site "$SITE" set-maintenance-mode off' EXIT

# Restoring the tars only adds files back; remove visitor uploads first.
rm -rf "$SITE_DIR/public/files" "$SITE_DIR/private/files"
mkdir -p "$SITE_DIR/public/files" "$SITE_DIR/private/files"

bench --site "$SITE" restore "$SNAP/db.sql.gz" \
	--with-public-files "$SNAP/public.tar" \
	--with-private-files "$SNAP/private.tar" \
	--db-root-password "$DB_ROOT_PASSWORD" \
	--force
bench --site "$SITE" set-config hms_demo_mode 1
# Sessions in the snapshot and in Redis belong to earlier visitors.
bench --site "$SITE" destroy-all-sessions
bench --site "$SITE" clear-cache
echo "$(date -u +%FT%TZ) demo reset done"

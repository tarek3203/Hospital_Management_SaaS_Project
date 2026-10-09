#!/usr/bin/env bash
# Restore the demo site to its snapshot, so visitor changes do not pile up.
# The demo-reset compose service runs this every RESET_INTERVAL_HOURS.
set -euo pipefail
cd /home/frappe/frappe-bench
SITE="${SITE_NAME:-hms.localhost}"
SNAP="/home/frappe/frappe-bench/sites/demo-snapshot"

if [ ! -f "$SNAP/db.sql.gz" ]; then
	echo "No snapshot at $SNAP, run snapshot.sh first" >&2
	exit 1
fi

bench --site "$SITE" set-maintenance-mode on
bench --site "$SITE" restore "$SNAP/db.sql.gz" \
	--with-public-files "$SNAP/public.tar" \
	--with-private-files "$SNAP/private.tar" \
	--db-root-password "$DB_ROOT_PASSWORD" \
	--force
bench --site "$SITE" set-config hms_demo_mode 1
bench --site "$SITE" set-maintenance-mode off
bench --site "$SITE" clear-cache
echo "$(date -u +%FT%TZ) demo reset done"

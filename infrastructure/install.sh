#!/usr/bin/env bash
# One-command install of CityCare HMS for a hospital (or a public demo).
#
#   ./infrastructure/install.sh --site hms.example.com [--port 80] [--demo]
#
# Builds the images (first run takes about 20 minutes), writes
# infrastructure/.env with strong random passwords, starts the stack and
# creates the site. --demo also loads the demo hospital, turns on demo mode
# (role login buttons) and the scheduled demo reset.
set -euo pipefail
cd "$(dirname "$0")/.."

SITE="hms.localhost"
PORT="8080"
DEMO=0
while [ $# -gt 0 ]; do
	case "$1" in
		--site) SITE="$2"; shift 2 ;;
		--port) PORT="$2"; shift 2 ;;
		--demo) DEMO=1; shift ;;
		*) echo "Unknown option $1" >&2; exit 1 ;;
	esac
done

command -v docker >/dev/null || { echo "Docker is required: https://docs.docker.com/engine/install/" >&2; exit 1; }
docker compose version >/dev/null || { echo "Docker Compose v2 is required" >&2; exit 1; }

COMPOSE=(docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env)

if [ ! -f infrastructure/.env ]; then
	secret() { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24; }
	cat > infrastructure/.env <<ENV
DB_ROOT_PASSWORD=$(secret)
ADMIN_PASSWORD=$(secret)
SITE_NAME=${SITE}
HTTP_PORT=${PORT}
ENV
	if [ "$DEMO" = 1 ]; then
		printf 'COMPOSE_PROFILES=demo\nRESET_INTERVAL_HOURS=6\n' >> infrastructure/.env
	fi
	chmod 600 infrastructure/.env
	echo "Wrote infrastructure/.env with new passwords (keep it private)."
else
	echo "Using existing infrastructure/.env"
fi

if ! docker image inspect hms/base:v16 >/dev/null 2>&1; then
	[ -d infrastructure/frappe_docker ] || git clone --depth 1 https://github.com/frappe/frappe_docker.git infrastructure/frappe_docker
	echo "Building the base image (Frappe, ERPNext, HRMS, Healthcare). This takes a while..."
	docker build --secret id=apps_json,src=infrastructure/apps.json --build-arg FRAPPE_BRANCH=version-16 \
		-t hms/base:v16 -f infrastructure/frappe_docker/images/layered/Containerfile infrastructure/frappe_docker
fi
echo "Building the CityCare HMS image..."
docker build -f infrastructure/Containerfile -t hms/app:v16 .

"${COMPOSE[@]}" up -d
echo "Waiting for the site to be created..."
until [ "$(docker inspect -f '{{.State.Status}}' hms-create-site-1 2>/dev/null)" = "exited" ]; do sleep 5; done
if [ "$(docker inspect -f '{{.State.ExitCode}}' hms-create-site-1)" != "0" ]; then
	echo "Site creation failed, see: docker logs hms-create-site-1" >&2
	exit 1
fi

# Daily database and file backups, kept for a week.
docker exec hms-backend-1 bench --site "$SITE" set-config backup_limit 7

if [ "$DEMO" = 1 ]; then
	echo "Loading the demo hospital (about 10 minutes)..."
	docker exec hms-backend-1 bench --site "$SITE" execute hospital_saas.demo.setup.run
	docker exec hms-backend-1 bench --site "$SITE" set-config hms_demo_mode 1
	docker exec hms-backend-1 bash /home/frappe/demo/snapshot.sh
fi

ADMIN_PASSWORD=$(grep '^ADMIN_PASSWORD=' infrastructure/.env | cut -d= -f2-)
cat <<DONE

CityCare HMS is running on http://${SITE}:${PORT}
  Administrator password: ${ADMIN_PASSWORD}
Log in, finish the setup wizard (hospital name, currency, fiscal year),
then create staff users and give each one a role profile.
DONE

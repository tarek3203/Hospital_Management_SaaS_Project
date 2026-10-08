# Local setup (Docker)

Frappe v16 + ERPNext + HRMS + Healthcare (Marley) + `hospital_saas`.

## First time

From the repo root:

1. Get the official image recipes (ignored by git):

   ```bash
   git clone --depth 1 https://github.com/frappe/frappe_docker.git infrastructure/frappe_docker
   ```

2. Build the base image with upstream apps (~20 min, cached afterwards):

   ```bash
   docker build --secret id=apps_json,src=infrastructure/apps.json --build-arg FRAPPE_BRANCH=version-16 -t hms/base:v16 -f infrastructure/frappe_docker/images/layered/Containerfile infrastructure/frappe_docker
   ```

3. Build our app image:

   ```bash
   docker build -f infrastructure/Containerfile -t hms/app:v16 .
   ```

4. Configure and start (creates the site on first run):

   ```bash
   cp infrastructure/.env.example infrastructure/.env
   ```

   ```bash
   docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env up -d
   ```

5. Load demo data once `hms-create-site-1` has exited:

   ```bash
   docker exec hms-backend-1 bench --site hms.localhost execute hospital_saas.demo.setup.run
   ```

Open http://localhost:8080 — logins are in `docs/DEMO_GUIDE.md`.

## Day to day

- `apps/hospital_saas` is bind-mounted; after Python changes restart the app
  containers: `docker compose -f infrastructure/compose.yaml restart backend queue-short queue-long scheduler`
- After DocType/hook changes: `docker exec hms-backend-1 bench --site hms.localhost migrate`
- Rebuild `hms/app:v16` when dependencies change or before shipping an image.

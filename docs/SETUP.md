# Setup Guide — Hospital Management SaaS (end to end)

This guide takes you from an empty machine to a running hospital system with
demo data, in about **30–40 minutes** (most of it is a one-time image build).

Stack: Frappe v16 + ERPNext + Frappe HR + Frappe Health, plus our custom app
`hospital_saas`, all running in Docker.

---

## 1. What you need

| Requirement | Notes |
| --- | --- |
| **Docker** | Windows/Mac: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows: WSL 2 backend). Linux: Docker Engine + Compose plugin. |
| **Git** | Any recent version. |
| **RAM** | 8 GB minimum, 16 GB recommended. Give Docker Desktop at least 6 GB. |
| **Disk** | ~20 GB free. |
| **Internet** | Needed for the first build (downloads Frappe and apps from GitHub). |
| **Free port** | `8080` (change `HTTP_PORT` in `.env` if it is taken). |

Check Docker is working:

```bash
docker --version
```

```bash
docker compose version
```

> **Windows users:** run all commands in **Git Bash** (comes with Git), not
> CMD. Keep line endings Unix-style so shell scripts work inside containers:
>
> ```bash
> git config --global core.autocrlf input
> ```

---

## 2. Get the code

```bash
git clone https://github.com/KompileX/Hospital_Management_SaaS_Project.git
```

```bash
cd Hospital_Management_SaaS_Project
```

If you were given a branch (for example `feature/client-demo`), switch to it:

```bash
git switch feature/client-demo
```

The repo layout:

```
apps/hospital_saas/    our Frappe app (branding, demo data)
infrastructure/        Docker build + compose files
docs/                  this guide and the demo walkthrough
```

---

## 3. Get the official Frappe Docker recipes

These are not stored in our repo; clone them into `infrastructure/`:

```bash
git clone --depth 1 https://github.com/frappe/frappe_docker.git infrastructure/frappe_docker
```

---

## 4. Build the images (one time, ~20 min)

**4a. Base image** — Frappe + ERPNext + HR + Healthcare (the long step):

```bash
docker build --secret id=apps_json,src=infrastructure/apps.json --build-arg FRAPPE_BRANCH=version-16 -t hms/base:v16 -f infrastructure/frappe_docker/images/layered/Containerfile infrastructure/frappe_docker
```

**4b. App image** — adds our `hospital_saas` app on top (~2 min):

```bash
docker build -f infrastructure/Containerfile -t hms/app:v16 .
```

Check both images exist:

```bash
docker images hms/*
```

---

## 5. Configure

Create your local settings file from the template:

```bash
cp infrastructure/.env.example infrastructure/.env
```

Open `infrastructure/.env` and adjust if needed:

| Variable | Default | Meaning |
| --- | --- | --- |
| `DB_ROOT_PASSWORD` | `admin` | MariaDB root password |
| `ADMIN_PASSWORD` | `admin` | Password for the `Administrator` user |
| `SITE_NAME` | `hms.localhost` | Frappe site name |
| `HTTP_PORT` | `8080` | Port the app is served on |

> Never commit `infrastructure/.env`. Use strong passwords on any machine
> reachable by others.

---

## 6. Start the system

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env up -d
```

On the first start, a one-off `create-site` container creates the site and
installs all apps. This takes **3–6 minutes**. Follow it with:

```bash
docker logs -f hms-create-site-1
```

Wait until you see `Current Site set to hms.localhost`, then press `Ctrl+C`.

Check everything is running:

```bash
docker compose -f infrastructure/compose.yaml ps
```

`configurator` and `create-site` show **Exited (0)** — that is expected. All
others should be **running**.

---

## 7. Load the demo data (~3 min)

```bash
docker exec hms-backend-1 bench --site hms.localhost execute hospital_saas.demo.setup.run
```

It prints each step and ends with `Demo data ready.` This creates the
hospital, branches, doctors, beds, patients, appointments, lab results,
invoices, pharmacy stock, staff and demo logins.

> Skip this step if you want an empty system for real data.

---

## 8. Open it

Go to **http://localhost:8080** (or your `HTTP_PORT`).

All demo users share the password **`Demo@2026`**:

| Email | Use it for |
| --- | --- |
| `admin.demo@citycare.test` | Hospital admin — full access (start here) |
| `reception@citycare.test` | Front desk — patients, appointments, billing |
| `doctor@citycare.test` | Doctor — consultations, prescriptions |
| `nurse@citycare.test` | Nurse — vitals, inpatients |
| `lab@citycare.test` | Lab — test results |
| `accounts@citycare.test` | Accounts — invoices, payments |

System super user: `Administrator` / your `ADMIN_PASSWORD`.

For a guided client walkthrough see [DEMO_GUIDE.md](DEMO_GUIDE.md).

---

## 9. Everyday commands

Stop (data is kept):

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env stop
```

Start again:

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env start
```

See backend logs:

```bash
docker logs -f hms-backend-1
```

Open a Frappe console (Python shell on the site):

```bash
docker exec -it hms-backend-1 bench --site hms.localhost console
```

Back up the database and files:

```bash
docker exec hms-backend-1 bench --site hms.localhost backup --with-files
```

Backups are saved inside the container at
`sites/hms.localhost/private/backups/`.

---

## 10. Working on the code

`apps/hospital_saas` is mounted live into the containers.

- **Python changes** → restart the app containers:

  ```bash
  docker compose -f infrastructure/compose.yaml restart backend queue-short queue-long scheduler
  ```

- **DocType / hooks / patches changes** → also run a migrate:

  ```bash
  docker exec hms-backend-1 bench --site hms.localhost migrate
  ```

- **New Python dependencies or before sharing an image** → rebuild step 4b and
  run `up -d` again.

---

## 11. Reset everything (start fresh)

This **deletes all data** (database, files, site):

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env down -v
```

Then repeat steps 6 and 7.

---

## 12. Troubleshooting

| Symptom | Fix |
| --- | --- |
| Containers keep restarting with `exec /usr/local/bin/entrypoint.sh: no such file or directory` | Windows line endings. Set `git config --global core.autocrlf input`, delete `infrastructure/frappe_docker`, clone it again, then rebuild step 4b. |
| `create-site` failed / site half-created | `docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env down -v`, then step 6 again. |
| `Site hms.localhost already exists, skipping creation` | Normal on restarts — the site is already there. |
| `port is already allocated` on 8080 | Change `HTTP_PORT` in `infrastructure/.env`, then run step 6 again. |
| Page shows `404` or wrong site | Make sure `SITE_NAME` in `.env` matches the site you created (`hms.localhost`). |
| "Not permitted" for a user | That role lacks permission for the screen. Log in as `admin.demo@citycare.test`, or add the role in **User → Roles**. |
| Base build fails while downloading | Network hiccup — re-run the step 4a command; finished layers are cached. |
| Very slow / out of memory | Give Docker Desktop more RAM (Settings → Resources), close other containers. |
| Demo data step fails midway | Fix the cause and re-run step 7; finished steps are skipped. For a clean slate use section 11. |

# Installing CityCare HMS for a hospital

CityCare HMS is installed once per hospital: one server, one site, one
database. Branches are set up inside that site.

## Server

- Ubuntu 22.04/24.04 (or any Linux with Docker), 4 vCPU, 8 GB RAM, 60 GB disk
- Docker Engine with the Compose plugin
- A domain name pointing at the server (for HTTPS, put Caddy, Nginx or a
  Cloudflare tunnel in front of the HTTP port)

## Install

```bash
git clone <repo> citycare-hms && cd citycare-hms
./infrastructure/install.sh --site hms.hospital-domain.com --port 8080
```

The script:

1. writes `infrastructure/.env` with long random database and Administrator
   passwords (kept private, never committed),
2. builds the images (about 20 minutes the first time),
3. starts the stack and creates the site with ERPNext, HRMS, Healthcare and
   CityCare HMS,
4. keeps a week of daily backups.

Then open the site, log in as Administrator with the printed password and
finish the setup wizard (hospital name, currency, fiscal year). After that:

1. **Setup**: branches, departments, doctors (Healthcare Practitioner with
   schedules), wards and beds (Healthcare Service Unit tree), lab and
   radiology test templates, medicines, price lists.
2. **Staff**: create a user for each staff member and give them one role
   profile: Super Admin, Admin, Doctor, Pharmacist, Pathologist, Radiologist,
   Accountant, Receptionist or Nurse. They land on `/hms` after login.
3. **Patients**: patients get portal access when their record has an email
   and "Invite as user" is ticked.

Demo data and demo mode are never loaded on a hospital install.

## Public demo

```bash
./infrastructure/install.sh --site demo.example.com --demo
```

Loads the demo hospital, shows one-click role logins on the login page,
locks the demo accounts and resets the data every 6 hours. See
[DEMO_GUIDE.md](DEMO_GUIDE.md).

## Upgrade

```bash
./infrastructure/upgrade.sh
```

Backs up the site, pulls the latest code, rebuilds the app image and runs
migrations.

## Backups and restore

Daily backups are written to `sites/<site>/private/backups` in the `sites`
volume. To take one now:

```bash
docker exec hms-backend-1 bench --site <site> backup --with-files
```

To restore:

```bash
docker exec hms-backend-1 bench --site <site> restore <db.sql.gz> --with-public-files <public.tar> --with-private-files <private.tar> --db-root-password <from .env>
```

Copy backups off the server regularly (S3, Google Drive or another machine).

## Security notes

- Only the web port is published; MariaDB and Redis stay inside the Docker
  network.
- There are no default passwords: the stack refuses to start without
  `DB_ROOT_PASSWORD` and `ADMIN_PASSWORD` in `.env`.
- Turn on two-factor login for admin users in System Settings.
- Use HTTPS in front of the HTTP port before going live.

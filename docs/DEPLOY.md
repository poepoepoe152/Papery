# Papery — Pilot Deployment Guide

This guide takes Papery from local development to a real, HTTPS-served pilot on
a single server. It targets a company using **digital PDF** documents (the
supported-and-tested path).

## What you need

- A small VPS (2 vCPU / 4 GB RAM is plenty for a pilot) running Linux with
  **Docker** and the **Docker Compose plugin**.
- A **domain name** (e.g. `papery.yourcompany.com`) with an `A` record pointing
  at the server's public IP.
- Ports **80** and **443** open to the internet.

## 1. Get the code onto the server

```bash
git clone <your-repo-url> /opt/papery
cd /opt/papery
```

## 2. Create the `.env` file (secrets)

Generate strong secrets — never reuse the development defaults.

```bash
cat > .env <<EOF
PUBLIC_DOMAIN=papery.yourcompany.com
PUBLIC_URL=https://papery.yourcompany.com
JWT_SECRET=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -base64 24)
SUPER_ADMIN_EMAIL=you@yourcompany.com
SUPER_ADMIN_PASSWORD=$(openssl rand -base64 18)
EOF
chmod 600 .env
cat .env   # copy the SUPER_ADMIN_PASSWORD somewhere safe, then you can clear it from history
```

(Optional) add SMTP settings so password-reset and invite emails are delivered.
Without SMTP the app still works — reset links are written to the backend logs.

```bash
cat >> .env <<EOF
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=no-reply@yourcompany.com
EOF
```

## 3. Launch with automatic HTTPS

```bash
docker compose -f docker-compose.tls.yml up --build -d
```

Caddy automatically obtains and renews a Let's Encrypt certificate for
`PUBLIC_DOMAIN`. Give it a minute on first boot, then open
**https://papery.yourcompany.com**.

The backend creates its tables and seeds subscription plans on first start.

> Prefer nginx or already have TLS terminated upstream? Use
> `docker-compose.prod.yml` (plain HTTP on port 80) behind your own load
> balancer / certificate instead.

## 4. First-run setup

1. Log in as the platform super-admin (`SUPER_ADMIN_EMAIL` /
   `SUPER_ADMIN_PASSWORD`) → **Admin Panel**.
2. **Generate a license key** for the pilot company (pick a plan).
3. Send the key to the company's admin. They **Sign up**, **activate** with the
   key, invite their team, and start verifying documents.

## 5. Backups (do this before real data goes in)

`scripts/backup.sh` dumps the database to `./backups` and prunes old files.
Run it against the compose Postgres service and schedule it with cron:

```bash
# test it once
COMPOSE_DB_SVC=db BACKUP_DIR=/opt/papery/backups ./scripts/backup.sh

# daily at 02:30
( crontab -l 2>/dev/null; \
  echo "30 2 * * * cd /opt/papery && COMPOSE_DB_SVC=db BACKUP_DIR=/opt/papery/backups ./scripts/backup.sh >> /var/log/papery-backup.log 2>&1" \
) | crontab -
```

Restore when needed (stop the backend first):

```bash
COMPOSE_DB_SVC=db ./scripts/restore.sh backups/papery-YYYYMMDD-HHMMSS.sql.gz
```

Copy backups off the server periodically (another host or object storage) so a
server loss doesn't take the backups with it.

## 6. Updating

```bash
cd /opt/papery
git pull
docker compose -f docker-compose.tls.yml up --build -d
```

Schema changes are applied automatically on start (create-if-missing). Uploaded
files persist in the `papery_uploads` volume; the database in `papery_pgdata`.

## 7. Operating notes

- **Logs:** `docker compose -f docker-compose.tls.yml logs -f backend`
- **Reset a user's password manually** (no SMTP): trigger *Forgot password* in
  the UI, then copy the reset link from the backend logs and send it to them.
- **Monitor disk:** uploaded documents and backups grow over time; keep an eye
  on free space and prune old backups (the script keeps 14 days by default).

## Scope reminder

This pilot setup is a solid single-server deployment. For scale/HA later, the
architecture (`docs/ARCHITECTURE.md`) covers the moves: managed Postgres with
replicas, S3 for files, a Celery/Redis job queue, and horizontal workers.

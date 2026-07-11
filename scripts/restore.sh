#!/usr/bin/env bash
# Restore a Papery database backup produced by scripts/backup.sh.
#
#   ./scripts/restore.sh backups/papery-20260101-023000.sql.gz
#
# WARNING: this overwrites the target database. Stop the backend first.
# Env: PGHOST, PGPORT, PGUSER, PGDATABASE, PGPASSWORD (or COMPOSE_DB_SVC).
set -euo pipefail

FILE="${1:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  echo "usage: $0 <backup-file.sql.gz>" >&2
  exit 1
fi

PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-papery}"
PGDATABASE="${PGDATABASE:-papery}"

echo "[restore] restoring $FILE into $PGDATABASE"
read -r -p "This OVERWRITES $PGDATABASE. Type 'yes' to continue: " confirm
[ "$confirm" = "yes" ] || { echo "aborted"; exit 1; }

if [ -n "${COMPOSE_DB_SVC:-}" ]; then
  gunzip -c "$FILE" | docker compose exec -T "$COMPOSE_DB_SVC" psql -U "$PGUSER" "$PGDATABASE"
else
  gunzip -c "$FILE" | PGPASSWORD="${PGPASSWORD:-}" psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PGDATABASE"
fi

echo "[restore] done."

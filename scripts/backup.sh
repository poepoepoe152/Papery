#!/usr/bin/env bash
# Papery database backup — dumps PostgreSQL to a compressed file and prunes old
# backups. Designed to run from cron on the host running docker compose.
#
#   ./scripts/backup.sh
#
# Configure via environment (defaults suit docker-compose.prod.yml):
#   PGHOST, PGPORT, PGUSER, PGDATABASE, PGPASSWORD  (standard libpq vars)
#   BACKUP_DIR       where dumps are written           (default ./backups)
#   RETENTION_DAYS   delete dumps older than this many  (default 14)
#   COMPOSE_DB_SVC   if set, dump runs inside this compose service via docker
#
# Cron example (daily at 02:30, log to a file):
#   30 2 * * * cd /opt/papery && ./scripts/backup.sh >> /var/log/papery-backup.log 2>&1
set -euo pipefail

PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-papery}"
PGDATABASE="${PGDATABASE:-papery}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$BACKUP_DIR/papery-$STAMP.sql.gz"

echo "[backup] $(date -Is) dumping $PGDATABASE -> $OUT"

if [ -n "${COMPOSE_DB_SVC:-}" ]; then
  # Dump from inside the compose Postgres container.
  docker compose exec -T "$COMPOSE_DB_SVC" \
    pg_dump -U "$PGUSER" "$PGDATABASE" | gzip > "$OUT"
else
  PGPASSWORD="${PGPASSWORD:-}" pg_dump \
    -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" "$PGDATABASE" | gzip > "$OUT"
fi

SIZE="$(du -h "$OUT" | cut -f1)"
echo "[backup] wrote $OUT ($SIZE)"

# Prune old backups.
find "$BACKUP_DIR" -name 'papery-*.sql.gz' -type f -mtime +"$RETENTION_DAYS" -print -delete \
  | sed 's/^/[backup] pruned /' || true

echo "[backup] done. Keeping backups newer than ${RETENTION_DAYS} days."

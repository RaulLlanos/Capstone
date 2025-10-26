#!/usr/bin/env sh
set -e

# Variables aceptadas:
#   Opción A: DATABASE_URL (postgresql://user:pass@host:port/db?params)
#   Opción B: POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#
# Config:
: "${BACKUP_PATH:=/backups}"
: "${BACKUP_KEEP:=7}"
: "${BACKUP_INTERVAL_SEC:=86400}"

mkdir -p "$BACKUP_PATH"

do_backup () {
  TS=$(date +"%Y%m%d-%H%M%S")
  FILE="${BACKUP_PATH}/dump-${TS}.sql.gz"
  echo "[backup] creando ${FILE}"

  if [ -n "$DATABASE_URL" ]; then
    # Con URL completa
    pg_dump "$DATABASE_URL" | gzip > "$FILE"
  else
    # Con variables sueltas
    export PGPASSWORD="$POSTGRES_PASSWORD"
    pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$FILE"
  fi

  # Mantener solo los últimos BACKUP_KEEP archivos
  ls -1t "${BACKUP_PATH}"/dump-*.sql.gz 2>/dev/null | tail -n +$((BACKUP_KEEP+1)) | xargs -r rm -f
}

if [ "$ONESHOT" = "1" ]; then
  do_backup
  exit 0
fi

while true; do
  do_backup
  sleep "$BACKUP_INTERVAL_SEC"
done

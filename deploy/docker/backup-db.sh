#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
if [ -n "${1:-}" ]; then
  OUT="$1"
elif [ -d /var/backups ]; then
  mkdir -p /var/backups/gestia
  OUT="/var/backups/gestia/gestia-${STAMP}.sql.gz"
else
  mkdir -p "${ROOT}/backups"
  OUT="${ROOT}/backups/gestia-${STAMP}.sql.gz"
fi
mkdir -p "$(dirname "${OUT}")"

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec -T db pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" | gzip > "${OUT}"

echo "${OUT}"

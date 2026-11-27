#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DATA_DIR="${ROOT}/deploy/data"
DUMP="${DATA_DIR}/shop.json"
MEDIA_TAR="${DATA_DIR}/media.tar.gz"
PYTHON="${ROOT}/.venv/bin/python3"
if [ ! -x "${PYTHON}" ]; then
  PYTHON="python3"
fi

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

https_on() {
  case "${USE_HTTPS:-false}" in
    true|True|TRUE|1|yes|YES) return 0 ;;
    *) return 1 ;;
  esac
}

compose() {
  if https_on; then
    docker compose \
      -f docker-compose.yml \
      -f docker-compose.prod.yml \
      -f docker-compose.ssl.yml \
      "$@"
  else
    docker compose \
      -f docker-compose.yml \
      -f docker-compose.prod.yml \
      "$@"
  fi
}

health_ok() {
  local body
  if https_on; then
    body="$(curl -sfk https://127.0.0.1/healthz/ 2>/dev/null || true)"
  else
    body="$(curl -sf http://127.0.0.1/healthz/ 2>/dev/null || true)"
  fi
  printf '%s\n' "${body}" | grep -q ok
}

# Вітрина лише: catalog + content. Без auth/session/order/axes і без демо-admin.
export_data() {
  mkdir -p "${DATA_DIR}"
  "${PYTHON}" manage.py dumpdata catalog content \
    --natural-foreign --natural-primary --indent 2 -o "${DUMP}"
  if [ -d media ] && [ -n "$(find media -type f -print -quit 2>/dev/null)" ]; then
    tar -czf "${MEDIA_TAR}" -C media .
  elif [ -d demo/media ]; then
    tar -czf "${MEDIA_TAR}" -C demo/media .
  else
    echo "no media to pack" >&2
    exit 1
  fi
  echo "${DUMP}"
  echo "${MEDIA_TAR}"
}

load_data() {
  if [ ! -f "${DUMP}" ]; then
    echo "missing ${DUMP} — run export first" >&2
    exit 1
  fi
  health_ok
  compose cp "${DUMP}" backend:/tmp/shop.json
  compose exec -T backend python manage.py loaddata /tmp/shop.json
  if [ -f "${MEDIA_TAR}" ]; then
    compose cp "${MEDIA_TAR}" backend:/tmp/media.tar.gz
    compose exec -T backend sh -c 'mkdir -p /app/media && tar -xzf /tmp/media.tar.gz -C /app/media'
  fi
  echo "loaded catalog/content. run createsuperuser separately."
}

case "${1:-}" in
  export) export_data ;;
  load) load_data ;;
  *)
    echo "usage: $0 export|load" >&2
    exit 1
    ;;
esac

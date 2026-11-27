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

free_host_ports() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl stop nginx 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    systemctl stop gunicorn 2>/dev/null || true
    systemctl disable gunicorn 2>/dev/null || true
  fi
  if ! command -v ss >/dev/null 2>&1; then
    return 0
  fi
  for port in 80 443; do
    ss -tlnp "sport = :${port}" 2>/dev/null | while read -r line; do
      echo "$line" | grep -q docker-proxy && continue
      pid="$(echo "$line" | sed -n 's/.*pid=\([0-9][0-9]*\).*/\1/p' | head -1)"
      [ -n "${pid}" ] || continue
      comm="$(ps -p "${pid}" -o comm= 2>/dev/null || true)"
      case "${comm}" in
        docker-proxy) continue ;;
        nginx|nginx:*|gunicorn*)
          echo "free :${port} host process ${comm} pid ${pid}"
          kill "${pid}" 2>/dev/null || true
          ;;
      esac
    done
  done
}

wait_healthz() {
  local i body
  for i in $(seq 1 90); do
    if https_on; then
      body="$(curl -sfk https://127.0.0.1/healthz/ 2>/dev/null || true)"
    else
      body="$(curl -sf http://127.0.0.1/healthz/ 2>/dev/null || true)"
    fi
    if echo "${body}" | grep -q ok; then
      echo "healthz OK"
      return 0
    fi
    sleep 2
  done
  echo "healthz failed" >&2
  compose logs --tail=40 backend nginx
  return 1
}

inventory() {
  local out svc line
  out="$(compose ps --format '{{.Service}} {{.Status}}' 2>/dev/null || compose ps)"
  echo "${out}"
  for svc in nginx backend db; do
    line="$(printf '%s\n' "${out}" | awk -v s="${svc}" '$1 == s {print; found=1} END {exit !found}')" || true
    if ! printf '%s\n' "${line}" | grep -qi Up; then
      echo "MISSING or not Up: ${svc}" >&2
      return 1
    fi
  done
}

if https_on && [ -z "${DOMAIN:-}" ]; then
  echo "DOMAIN is required when USE_HTTPS=true" >&2
  exit 1
fi

free_host_ports
compose up -d --build
wait_healthz
inventory

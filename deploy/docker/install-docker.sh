#!/bin/bash
set -euo pipefail

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "Docker already installed"
  docker --version
  docker compose version
  exit 0
fi

curl -fsSL https://get.docker.com | sh
if command -v systemctl >/dev/null 2>&1; then
  systemctl enable --now docker
fi
docker --version
docker compose version

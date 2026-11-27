#!/bin/sh
set -e
echo "Waiting for postgres..."
while ! nc -z db 5432; do sleep 0.1; done
echo "PostgreSQL started"
if [ -d /app/demo/media ]; then
  mkdir -p /app/media
  cp -an /app/demo/media/. /app/media/ || true
fi
python manage.py compilemessages -l uk || true
python manage.py compilemessages -l en || true
python manage.py compilemessages -l fr || true
exec "$@"

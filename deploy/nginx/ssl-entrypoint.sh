#!/bin/sh
set -e
if [ -z "${DOMAIN}" ]; then
  echo "DOMAIN is required for TLS nginx config" >&2
  exit 1
fi
if [ ! -f /nginx-ssl.template ]; then
  echo "/nginx-ssl.template is missing" >&2
  exit 1
fi
envsubst '${DOMAIN}' < /nginx-ssl.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"

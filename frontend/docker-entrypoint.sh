#!/bin/sh
set -e
echo "window.__env__ = { SENTRY_DSN: \"${SENTRY_FRONTEND_DSN}\" };" \
  > /usr/share/nginx/html/env-config.js
exec nginx -g 'daemon off;'

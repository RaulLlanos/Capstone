#!/usr/bin/env sh
set -e

# (opcional) collectstatic si usas archivos estáticos
# python manage.py collectstatic --noinput || true

python manage.py migrate --noinput
exec "$@"

#!/bin/sh
# Runs every time the container starts in production.

# Stop at the first failing command, so a broken migration never goes live
set -e

# Gather static files for whitenoise
python manage.py collectstatic --noinput

# Bring the database schema up to date
python manage.py migrate --noinput

# Create or refresh the staff groups and their permissions
python manage.py setup_roles

# Create the admin from DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD.
# It fails when the admin already exists, which is fine on every start after the first
python manage.py createsuperuser --noinput || true

# Start the server; Render gives the port in $PORT
exec gunicorn Ecommerce.wsgi:application --bind 0.0.0.0:${PORT:-8000}
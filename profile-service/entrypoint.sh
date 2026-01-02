#!/bin/sh
echo "Waiting for PostgreSQL to be fully ready..."

until pg_isready -h "$PROFILE_DB_HOST" -p "$PROFILE_DB_PORT" -U "$PROFILE_DB_USER"; do
  echo "PostgreSQL is still starting..."
  sleep 1
done

echo "PostgreSQL is fully ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting Supervisor (Django + Consumer)..."
exec supervisord -c /app/supervisord.conf

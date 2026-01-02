#!/bin/sh
echo "Waiting for PostgreSQL..."

while ! nc -z "$AUTH_DB_HOST" "$AUTH_DB_PORT"; do
  echo "Database not ready yet..."
  sleep 0.5
done

echo "PostgreSQL is ready!"
python manage.py migrate --noinput
echo "Starting Auth Service..."
python manage.py runserver 0.0.0.0:8000

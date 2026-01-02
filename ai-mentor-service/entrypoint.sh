#!/bin/sh
echo "Waiting for PostgreSQL..."

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  echo "Database not ready yet..."
  sleep 0.5
done

echo "PostgreSQL is ready!"

echo "Creating migrations..."
python manage.py makemigrations mentor --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting AI Mentor Service..."
python manage.py runserver 0.0.0.0:8006
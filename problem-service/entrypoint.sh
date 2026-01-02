echo "Waiting for PostgreSQL..."

while ! nc -z "$PROBLEM_DB_HOST" "$PROBLEM_DB_PORT"; do
  echo "Database not ready... waiting..."
  sleep 1
done

echo "Database connected!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting Problem Service..."
python manage.py runserver 0.0.0.0:8004

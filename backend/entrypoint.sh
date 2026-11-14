#!/bin/sh
set -eu

echo "Esperando a que la base de datos esté lista..."

RETRIES=20

until python -c "import pymysql, os; pymysql.connect(
    host=os.environ.get('DB_HOST', 'db'),
    user=os.environ.get('DB_USER', 'licomart_user'),
    password=os.environ.get('DB_PASSWORD', 'licomart_password'),
    database=os.environ.get('DB_NAME', 'licomart_db')
)" >/dev/null 2>&1
do
  RETRIES=$((RETRIES-1))
  if [ "$RETRIES" -le 0 ]; then
    echo "No se pudo conectar a la base de datos, abortando."
    exit 1
  fi
  echo "Base de datos no lista aún, reintentando..."
  sleep 3
done

echo "Base de datos lista, corriendo migraciones..."
python manage.py migrate --noinput

echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput 2>/dev/null || true

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo ""
  echo "Cargando datos de demostración..."
  python manage.py seed_completo
fi

echo "Levantando servidor..."
gunicorn licomart.wsgi:application --bind 0.0.0.0:8000 --workers 3

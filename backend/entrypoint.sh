#!/bin/sh
set -eu

echo "Esperando a que la base de datos esté lista..."

# Intentar conectar varias veces
RETRIES=20

until python -c "import MySQLdb, os; MySQLdb.connect(
    host=os.environ.get('DB_HOST', 'db'),
    user=os.environ.get('DB_USER', 'licomart_user'),
    passwd=os.environ.get('DB_PASSWORD', 'licomart_password'),
    db=os.environ.get('DB_NAME', 'licomart_db')
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

echo "Levantando servidor Django..."
python manage.py runserver 0.0.0.0:8000

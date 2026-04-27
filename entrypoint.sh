#!/bin/bash
set -e

echo "Esperando a MySQL..."
until python -c "
import pymysql, os, sys
try:
    pymysql.connect(
        host=os.getenv('DB_HOST','db'),
        port=int(os.getenv('DB_PORT',3306)),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME')
    )
    sys.exit(0)
except Exception as e:
    sys.exit(1)
"; do
    echo "MySQL no está listo, reintentando..."
    sleep 2
done

echo "MySQL listo. Aplicando migraciones..."
python manage.py migrate --fake-initial

echo "Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:8000

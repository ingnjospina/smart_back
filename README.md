# Gestion_Backend


1. Intalar python 3.12.7
1. Crear ambiente   
    - python -m venv venv
    - .\venv\Scripts\activate
1. crear archivo .env EJ:
    - DB_USER=root
    - DB_NAME=nameDB
    - DB_PASSWORD=passwordDB
    - DB_HOST=localhost
    - DB_PORT=3306
1. Instalar dependencias
    - pip install -r requirements.txt
1. Generar migración de DB
    - python manage.py makemigrations
    - python manage.py migrate
1. Iniciar server
    - python manage.py runserver   

#!/bin/sh

echo "Running database migrations..."
./manage.py migrate

echo "Starting gunicorn..."
gunicorn --bind 0.0.0.0:8000 --workers 3 parlhist.wsgi:application

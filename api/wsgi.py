# wsgi.py
# WSGI factory pattern - https://stackoverflow.com/questions/56476687/deploy-a-flask-app-with-gunicorn-exploreflask-tuto
from app import create_app

app = create_app()
"""
WSGI Configuration
==================
WSGI (Web Server Gateway Interface) is the standard protocol Python web apps
use to communicate with web servers (like Gunicorn or uWSGI) in production.

In development, `python manage.py runserver` handles this for you.
In production, you'd use: gunicorn config.wsgi:application
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

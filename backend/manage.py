#!/usr/bin/env python
"""
manage.py — Django's Command-Line Utility
==========================================
This is your main entry point for interacting with Django on the command line.

Common commands you'll use:
  python manage.py runserver        → Start the development server
  python manage.py makemigrations   → Detect model changes and create migration files
  python manage.py migrate          → Apply migrations to the database
  python manage.py createsuperuser  → Create an admin user
  python manage.py shell            → Open an interactive Python shell with Django loaded
"""
import os
import sys


def main():
    # Tell Django which settings file to use.
    # os.environ.setdefault only sets it if not already set,
    # so you can override it from the command line.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it's installed and your "
            "virtual environment is activated."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UNIQUE_Dashboard.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # 👇 Check for create_superuser trigger
    if 'create_superuser_once' in sys.argv:
        import django
        django.setup()
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'HOSTER@gmail.com', 'HOSTER@123')
            print("✅ Superuser created.")
        else:
            print("ℹ️ Superuser already exists.")
    else:
        execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

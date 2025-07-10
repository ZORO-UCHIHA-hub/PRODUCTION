#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UNIQUE_Dashboard.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django."
        ) from exc

    # Run management command first
    execute_from_command_line(sys.argv)

    # 🔐 Auto-create superuser (only runs on Railway deployment)
    try:
        import django
        django.setup()
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='HOSTER@gmail.com',
                password='HOSTER@123'
            )
            print("✅ Superuser 'admin' created.")
        else:
            print("ℹ️ Superuser already exists.")
    except Exception as e:
        print("⚠️ Error creating superuser:", str(e))

if __name__ == '__main__':
    main()

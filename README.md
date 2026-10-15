# Employee Directory

A Django application for employee registration, profile display, employee login, and HR-managed employee directory access.

## Features

- Employee signup with generated, unique employee IDs
- Passwords stored as Django password hashes
- Optional profile photo upload (JPG, JPEG, PNG, or WEBP; up to 5 MB)
- Employee profile page
- HR directory access controlled by an administrator
- Search, department filtering, pagination, and CSV export for authorized HR users
- Django Admin for managing employee records and granting HR access

## Requirements

- Python 3.11+
- Django 5.2.6 (see `requirements.txt`)

## Local setup

From the project directory, create and activate a virtual environment, then install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Set a new local Django secret and start the development server:

```powershell
$env:DJANGO_SECRET_KEY = (python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/body/` to sign up. The employee profile is at `http://127.0.0.1:8000/body/homepage/`, and the login page is at `http://127.0.0.1:8000/body/login/`.

## Granting HR access

1. Sign in to Django Admin at `http://127.0.0.1:8000/admin/` with a superuser.
2. Open **Body signups**, select the employee record, enable **Is HR access**, then save.
3. That employee can log in at `/body/login/`; HR-enabled users are directed to `/body/employees/`.

## Network development

For temporary testing on a trusted local network, set `DJANGO_ALLOWED_HOSTS` to include this computer's LAN IP and run:

```powershell
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,192.168.1.10"
python manage.py runserver 0.0.0.0:8000
```

Replace `192.168.1.10` with the computer's current LAN IP. Django's built-in server is for development only, not production hosting.

## Security notes

- The local SQLite database, uploaded employee photos, and virtual environments are excluded from Git. They contain local employee data and must not be published.
- Set a unique `DJANGO_SECRET_KEY` in the environment. The settings fallback is for local development only.
- Before deploying publicly, set `DJANGO_DEBUG=false`, configure `DJANGO_ALLOWED_HOSTS`, use a production-ready web server, and review Django's deployment checklist.
- Employee records include sensitive personal information. Restrict HR access and follow applicable privacy requirements.

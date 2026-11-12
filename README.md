# Digitech Avenue CRM — Backend

Django REST Framework API for Digitech Avenue CRM.

## Local setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py create_production_users \
  --admin-password 'YOUR_ADMIN_PASSWORD' \
  --staff-password 'YOUR_STAFF_PASSWORD'
python manage.py runserver
```

API: http://127.0.0.1:8000/api/

## Railway

Crash fix included: `gunicorn`, Whitenoise, Postgres URL support, and pending migrations.

Set these variables in Railway:

| Variable | Example |
|----------|---------|
| `SECRET_KEY` | long random string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.railway.app,your-service.up.railway.app` |
| `CORS_ALLOWED_ORIGINS` | `https://your-frontend-domain` |
| `DATABASE_URL` | auto from Railway Postgres |

Recommended: add a **PostgreSQL** plugin to the service.

After deploy, create users from Railway console:

```bash
python manage.py create_production_users \
  --admin-password 'Wq5a7E4DJlVJu#pB' \
  --staff-password '&A&zgOLNkKiR3djK'
```

## Notes

- JWT auth via `/api/auth/login/`
- Role-based permissions (Owner vs Project Manager)
- Frontend is in a separate repository

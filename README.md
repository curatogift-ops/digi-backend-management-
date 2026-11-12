# Digitech Avenue CRM — Backend

Django REST Framework API for Digitech Avenue CRM.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_crm
python manage.py runserver
```

API: http://127.0.0.1:8000/api/  
Admin: http://127.0.0.1:8000/admin/

## Demo logins

| Role | Username | Password |
|------|----------|----------|
| Owner | `owner` | `Owner@123` |
| Project Manager | `pm` | `PM@12345` |
| Developer | `dev` | `Dev@12345` |

## Notes

- JWT auth via `/api/auth/login/`
- Role-based permissions (Owner vs Project Manager)
- Frontend is in a separate repository

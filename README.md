# Flowboard — Phase 1 MVP

A Django project-management app with account registration/login, profiles, projects, membership foundation, Kanban boards, task assignment fields, comments API, dashboard metrics, and searchable projects/tasks API.

## Requirements
- Python 3.10+
- VS Code or another editor

## macOS / Linux
```bash
cd project_management
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000/. Register a normal user, create a project, and open its board. Admin is at `/admin/`.

## Windows
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations core
python manage.py migrate
python manage.py runserver
```

## Phase 1 functionality
- Secure Django password hashing and session authentication.
- User profile update.
- Project create/list/detail and project membership model.
- Board defaults: To Do, In Progress, In Review, Completed.
- Create tasks, assign a user ID through the API, set priority/due date, and drag tasks between columns.
- Dashboard counts and upcoming tasks are read from SQLite.
- DRF APIs for projects, columns, tasks, comments and dashboard, with authenticated project-scoped querysets.
- Responsive HTML/CSS layout.

## API overview
Session-authenticated endpoints:
- `/api/projects/` (GET, POST, detail PATCH/DELETE)
- `/api/projects/{id}/members/` (GET, POST with `user_id`)
- `/api/tasks/` (GET, POST, detail PATCH/DELETE; query parameters `project`, `search`, `status`, `priority`, `assigned_to`)
- `/api/tasks/{id}/move/` (PATCH with `column_id`, optional `position`)
- `/api/columns/` (GET, POST, PATCH, DELETE)
- `/api/comments/` (GET, POST, PATCH, DELETE)
- `/api/dashboard/` (GET)

For browser API requests, authenticate through the website first and send the CSRF cookie/token for unsafe methods. DRF browsable API is available.

## Notes
- SQLite is configured for local development. Configure PostgreSQL before production.
- Email-based password reset, invitations, advanced role administration, task detail modal, comments UI, file uploads, and advanced phase 2/3 features are not included in this Phase 1 starter.
- Set a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, secure cookies, HTTPS, and production static/media storage before deployment.


## Phase 2 and Phase 3 extension scaffold

This revision adds data models for notifications, checklist items, task attachments, activity logs, project templates, recurring task rules, task dependencies, and time entries. It also adds notification, calendar/deadline list, analytics summary, activity, CSV export, and checklist actions. The calendar is currently a deadline-sorted list rather than a visual month grid.

### Setup on macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env  # only if .env does not already exist
python manage.py check
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python manage.py runserver
```

Open http://127.0.0.1:8000/. Media uploads require Pillow. Back up `db.sqlite3` and your project before applying schema changes.

### Implementation status and limitations

This is an incremental student-project extension, not a production-ready application. Notification records have a page but are not yet automatically generated for every event; upload and time-entry workflows, recurring-task scheduler, template-to-project workflow, full Gantt UI, live WebSocket collaboration, and comprehensive automated tests still require implementation. Task dependency cycle validation is included in the model, but should be covered by tests before relying on it. Review permissions, upload limits, deployment secrets, HTTPS, and database configuration before deployment.

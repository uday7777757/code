# Student Management App

A simple Flask + MySQL web app for managing student records with role-based access.

## Features
- Login/logout authentication
- Role-based permissions:
  - `admin`: add, edit, delete students
  - `viewer`: read-only access
- Student list with search
- MySQL-backed persistence
- Dockerized setup with `docker-compose`

## Tech Stack
- Python 3.11
- Flask
- MySQL 8.4
- Gunicorn
- Docker Compose

## Project Structure
- `app.py` - Flask application and routes
- `templates/` - HTML templates
- `static/` - CSS and static assets
- `init.sql` - database initialization script
- `Dockerfile` - web image build
- `docker-compose.yml` - local multi-container setup

## Run with Docker Compose (recommended)
```bash
docker compose up --build
```

The app will be available at:
- `http://localhost:8000`

MySQL will be exposed at:
- `localhost:3307` (maps to container `3306`)

## Default Login Credentials
- Admin
  - Username: `admin`
  - Password: `admin123`
- Viewer
  - Username: `viewer`
  - Password: `viewer123`

## Run Locally (without Docker)
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. Start a MySQL instance and create the `student_db` database.
3. Run `init.sql` against your MySQL database.
4. Set environment variables as needed:
```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=student
export DB_PASSWORD=student123
export DB_NAME=student_db
export SECRET_KEY=change-this
```
5. Start the app:
```bash
python app.py
```

## Environment Variables
- `DB_HOST` (default: `db`)
- `DB_PORT` (default: `3306`)
- `DB_USER` (default: `student`)
- `DB_PASSWORD` (default: `student123`)
- `DB_NAME` (default: `student_db`)
- `DB_RETRIES` (default: `15`)
- `DB_RETRY_DELAY` (default: `3`)
- `DB_POOL_SIZE` (default: `5`)
- `SECRET_KEY`
- `ADMIN_USERNAME` (default: `admin`)
- `ADMIN_PASSWORD` (default: `admin123`)
- `VIEWER_USERNAME` (default: `viewer`)
- `VIEWER_PASSWORD` (default: `viewer123`)
- `FLASK_DEBUG` (default: `false`)


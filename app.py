import os
import time
from functools import wraps
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
from mysql.connector import pooling

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-in-production")

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "student")
DB_PASSWORD = os.getenv("DB_PASSWORD", "student123")
DB_NAME = os.getenv("DB_NAME", "student_db")
DB_RETRIES = int(os.getenv("DB_RETRIES", "15"))
DB_RETRY_DELAY = int(os.getenv("DB_RETRY_DELAY", "3"))
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
VIEWER_USERNAME = os.getenv("VIEWER_USERNAME", "viewer")
VIEWER_PASSWORD = os.getenv("VIEWER_PASSWORD", "viewer123")

USERS = {
    ADMIN_USERNAME: {"password": ADMIN_PASSWORD, "role": "admin"},
    VIEWER_USERNAME: {"password": VIEWER_PASSWORD, "role": "viewer"},
}

# Wait for DB pool
db_pool = None
for _ in range(DB_RETRIES):
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="student_pool",
            pool_size=DB_POOL_SIZE,
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        # Validate one connection immediately.
        test_conn = db_pool.get_connection()
        test_conn.close()
        break
    except mysql.connector.Error:
        time.sleep(DB_RETRY_DELAY)

if db_pool is None:
    raise RuntimeError("Could not connect to MySQL after configured retries.")


def get_db_connection():
    return db_pool.get_connection()


def is_safe_next_url(next_url):
    if not next_url:
        return False
    parsed = urlparse(next_url)
    return parsed.netloc == "" and parsed.path.startswith("/")


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("username"):
            next_url = request.full_path.rstrip("?")
            return redirect(url_for("login", next=next_url))
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return redirect(url_for("index"))
        return view_func(*args, **kwargs)

    return wrapper

@app.after_request
def disable_cache_for_dynamic_pages(response):
    if not request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.context_processor
def inject_auth_context():
    return {
        "is_authenticated": bool(session.get("username")),
        "is_admin": session.get("role") == "admin",
        "current_user": session.get("username"),
        "current_role": session.get("role"),
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    next_url = request.args.get("next", "/")
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = USERS.get(username)
        if user and user["password"] == password:
            session["username"] = username
            session["role"] = user["role"]
            requested_next = request.form.get("next", "/")
            if is_safe_next_url(requested_next):
                return redirect(requested_next)
            return redirect("/")
        error = "Invalid username or password."
    return render_template("login.html", error=error, next_url=next_url)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def render_students_page():
    raw_search = request.args.get("search", "")
    search = " ".join(raw_search.split())
    where_clauses = []
    params = []

    if search:
        for token in search.split():
            like_value = f"%{token}%"
            where_clauses.append("(full_name LIKE %s OR course LIKE %s OR email LIKE %s)")
            params.extend([like_value, like_value, like_value])
        if search.isdigit():
            where_clauses.append("id = %s")
            params.append(int(search))

    query = "SELECT * FROM students"
    if where_clauses:
        query += " WHERE " + " OR ".join(where_clauses)
    query += " ORDER BY id DESC"

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, tuple(params))
        students = cursor.fetchall()
        filtered_total = len(students)

        cursor.execute("SELECT COUNT(*) FROM students")
        total = cursor.fetchone()[0]
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "index.html",
        students=students,
        total=total,
        filtered_total=filtered_total,
        search=search,
    )

@app.route("/")
@login_required
def index():
    return render_students_page()

@app.route("/search")
@login_required
def search():
    query = request.args.get("search", "").strip()
    return redirect(url_for("index", search=query))

@app.route("/add", methods=["POST"])
@login_required
@admin_required
def add_student():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO students (full_name, email, course) VALUES (%s,%s,%s)",
            (
                request.form["full_name"],
                request.form["email"],
                request.form["course"],
            ),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect("/")

@app.route("/delete/<int:id>")
@login_required
@admin_required
def delete_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM students WHERE id=%s", (id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_student(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        try:
            cursor.execute(
                "UPDATE students SET full_name=%s, email=%s, course=%s WHERE id=%s",
                (
                    request.form["full_name"],
                    request.form["email"],
                    request.form["course"],
                    id,
                ),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        return redirect("/")

    try:
        cursor.execute("SELECT * FROM students WHERE id=%s", (id,))
        student = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return render_template("edit_student.html", student=student)



if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")

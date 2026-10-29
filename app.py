"""Student Management System - a small Flask + SQLite web app."""
import csv
import io
import os
import secrets
import sqlite3
from datetime import datetime

from flask import (Flask, Response, abort, flash, g, redirect,
                   render_template, request, session, url_for)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

COURSES = [
    "Computer Science", "Information Technology", "Electronics",
    "Mechanical", "Civil", "Electrical", "Business Administration",
]
YEARS = [1, 2, 3, 4]
STATUSES = ["Active", "Graduated", "On leave"]
GENDERS = ["Female", "Male", "Other"]


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        DATABASE=os.path.join(BASE_DIR, "students.db"),
    )
    if test_config:
        app.config.update(test_config)

    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()

    register_routes(app)
    return app


# ---------- database ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app_db())
        g.db.row_factory = sqlite3.Row
    return g.db


def current_app_db():
    from flask import current_app
    return current_app.config["DATABASE"]


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            gender TEXT,
            dob TEXT,
            course TEXT NOT NULL,
            year INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            address TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    db.commit()


# ---------- helpers ----------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def validate(form, student_id=None):
    data = {k: form.get(k, "").strip() for k in
            ("roll_no", "name", "email", "phone", "gender", "dob",
             "course", "year", "status", "address")}
    errors = []
    if not data["roll_no"]:
        errors.append("Roll number is required.")
    if not data["name"]:
        errors.append("Name is required.")
    if "@" not in data["email"] or "." not in data["email"].split("@")[-1]:
        errors.append("Enter a valid email address.")
    if data["phone"] and not data["phone"].replace("+", "").replace(" ", "").isdigit():
        errors.append("Phone number can only contain digits, spaces and +.")
    if data["course"] not in COURSES:
        errors.append("Choose a course from the list.")
    if not data["year"].isdigit() or int(data["year"]) not in YEARS:
        errors.append("Choose a year between 1 and 4.")
    if data["status"] not in STATUSES:
        errors.append("Choose a valid status.")
    if data["dob"]:
        try:
            datetime.strptime(data["dob"], "%Y-%m-%d")
        except ValueError:
            errors.append("Date of birth must look like 2005-08-21.")
    if data["roll_no"]:
        row = get_db().execute(
            "SELECT id FROM students WHERE roll_no = ?", (data["roll_no"],)
        ).fetchone()
        if row and row["id"] != student_id:
            errors.append(f"Roll number {data['roll_no']} already belongs to another student.")
    return data, errors


def query_students(q="", course="", year="", status=""):
    sql, params = "SELECT * FROM students WHERE 1=1", []
    if q:
        sql += " AND (name LIKE ? OR roll_no LIKE ? OR email LIKE ?)"
        params += [f"%{q}%"] * 3
    if course:
        sql += " AND course = ?"
        params.append(course)
    if year.isdigit():
        sql += " AND year = ?"
        params.append(int(year))
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY name COLLATE NOCASE"
    return get_db().execute(sql, params).fetchall()


# ---------- routes ----------
def register_routes(app):
    app.jinja_env.globals.update(
        csrf_token=csrf_token, COURSES=COURSES, YEARS=YEARS,
        STATUSES=STATUSES, GENDERS=GENDERS,
    )

    @app.before_request
    def check_csrf():
        if request.method == "POST":
            sent, expected = request.form.get("_csrf"), session.get("_csrf")
            if not sent or not expected or not secrets.compare_digest(sent, expected):
                abort(400, "Invalid or missing form token. Reload the page and try again.")

    @app.route("/")
    def dashboard():
        db = get_db()
        total = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        active = db.execute("SELECT COUNT(*) FROM students WHERE status='Active'").fetchone()[0]
        by_course = db.execute(
            "SELECT course, COUNT(*) AS n FROM students GROUP BY course ORDER BY n DESC"
        ).fetchall()
        by_year = {r["year"]: r["n"] for r in db.execute(
            "SELECT year, COUNT(*) AS n FROM students GROUP BY year")}
        recent = db.execute(
            "SELECT * FROM students ORDER BY id DESC LIMIT 5").fetchall()
        return render_template(
            "dashboard.html", total=total, active=active, by_course=by_course,
            by_year=by_year, recent=recent,
            top=max((r["n"] for r in by_course), default=1),
        )

    @app.route("/students")
    def students():
        f = {k: request.args.get(k, "").strip() for k in ("q", "course", "year", "status")}
        rows = query_students(**f)
        return render_template("students.html", students=rows, f=f)

    @app.route("/students/new", methods=["GET", "POST"])
    def add_student():
        if request.method == "POST":
            data, errors = validate(request.form)
            if not errors:
                db = get_db()
                db.execute(
                    """INSERT INTO students (roll_no, name, email, phone, gender, dob,
                       course, year, status, address, created_at)
                       VALUES (:roll_no, :name, :email, :phone, :gender, :dob,
                       :course, :year, :status, :address, :created_at)""",
                    {**data, "year": int(data["year"]),
                     "created_at": datetime.now().isoformat(timespec="seconds")},
                )
                db.commit()
                flash(f"Added {data['name']}.", "ok")
                return redirect(url_for("students"))
            for e in errors:
                flash(e, "error")
            return render_template("student_form.html", s=data, mode="add"), 400
        return render_template("student_form.html", s={"status": "Active", "year": "1"}, mode="add")

    @app.route("/students/<int:sid>/edit", methods=["GET", "POST"])
    def edit_student(sid):
        db = get_db()
        row = db.execute("SELECT * FROM students WHERE id = ?", (sid,)).fetchone()
        if row is None:
            abort(404)
        if request.method == "POST":
            data, errors = validate(request.form, student_id=sid)
            if not errors:
                db.execute(
                    """UPDATE students SET roll_no=:roll_no, name=:name, email=:email,
                       phone=:phone, gender=:gender, dob=:dob, course=:course,
                       year=:year, status=:status, address=:address WHERE id=:id""",
                    {**data, "year": int(data["year"]), "id": sid},
                )
                db.commit()
                flash(f"Saved changes to {data['name']}.", "ok")
                return redirect(url_for("students"))
            for e in errors:
                flash(e, "error")
            return render_template("student_form.html", s={**data, "id": sid}, mode="edit"), 400
        return render_template("student_form.html", s=dict(row), mode="edit")

    @app.route("/students/<int:sid>/delete", methods=["POST"])
    def delete_student(sid):
        db = get_db()
        row = db.execute("SELECT name FROM students WHERE id = ?", (sid,)).fetchone()
        if row is None:
            abort(404)
        db.execute("DELETE FROM students WHERE id = ?", (sid,))
        db.commit()
        flash(f"Deleted {row['name']}.", "ok")
        return redirect(url_for("students"))

    @app.route("/students/export.csv")
    def export_csv():
        f = {k: request.args.get(k, "").strip() for k in ("q", "course", "year", "status")}
        rows = query_students(**f)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Roll no", "Name", "Email", "Phone", "Gender", "DOB",
                    "Course", "Year", "Status", "Address"])
        for r in rows:
            w.writerow([r["roll_no"], r["name"], r["email"], r["phone"], r["gender"],
                        r["dob"], r["course"], r["year"], r["status"], r["address"]])
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=students.csv"})

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404,
                               msg="That page or student doesn't exist."), 404

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400, msg=e.description), 400


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

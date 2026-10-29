# Student Management System

A small web app for keeping student records, built with **Python (Flask)** and **SQLite**.
No database server or extra setup needed: the database file is created on first run.

## Features

- Dashboard with totals, students per course and per year, and recently added students
- Add, edit and delete students (roll number, contact details, course, year, status)
- Search by name, roll number or email, and filter by course, year and status
- Export the full list, or just the filtered list, as CSV
- Form validation (valid email, unique roll number, valid year and status)
- CSRF protection on every form, and a confirmation prompt before deleting
- Responsive layout that works on phones
- Automated tests

## Project structure

```
student-management-system/
├── app.py            # Flask app: routes, validation, database code
├── seed.py           # Optional: adds sample students
├── requirements.txt
├── templates/        # HTML pages (Jinja2)
├── static/           # style.css, app.js
└── tests/            # unit tests
```

## Run it

You need Python 3.9 or newer.

```bash
# 1. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) load sample data
python seed.py

# 4. Start the app
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Run the tests

```bash
python -m unittest discover -s tests -v
```

## Configuration

| Setting | How to change | Default |
|---|---|---|
| Secret key | `SECRET_KEY` environment variable | `dev-change-me` (change this before deploying) |
| Debug mode | `FLASK_DEBUG=1` | off |

## Upload to GitHub

```bash
cd student-management-system
git init
git add .
git commit -m "Initial commit: student management system"
git branch -M main
git remote add origin https://github.com/<your-username>/student-management-system.git
git push -u origin main
```

Or create an empty repository on github.com and use **Add file → Upload files** to drag in the contents of this folder.

## Ideas to extend it

- Login for admins and teachers
- Attendance and marks tables linked to each student
- Pagination for large lists
- Switch SQLite to MySQL or PostgreSQL

## License

MIT

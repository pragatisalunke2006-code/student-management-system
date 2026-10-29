"""Fill the database with sample students: python seed.py"""
from datetime import datetime
from app import app, get_db

SAMPLE = [
    ("CS21001", "Aarohi Patil", "aarohi@example.com", "9876500001", "Female", "2004-03-14", "Computer Science", 3, "Active"),
    ("CS21002", "Rohan Deshmukh", "rohan@example.com", "9876500002", "Male", "2004-07-02", "Computer Science", 3, "Active"),
    ("IT22010", "Sneha Kulkarni", "sneha@example.com", "9876500003", "Female", "2005-01-25", "Information Technology", 2, "Active"),
    ("EC23005", "Aditya Joshi", "aditya@example.com", "9876500004", "Male", "2006-05-30", "Electronics", 1, "Active"),
    ("ME20007", "Priya Nair", "priya@example.com", "9876500005", "Female", "2003-11-09", "Mechanical", 4, "Graduated"),
    ("CV22014", "Kabir Shaikh", "kabir@example.com", "9876500006", "Male", "2005-09-18", "Civil", 2, "On leave"),
]

with app.app_context():
    db = get_db()
    for s in SAMPLE:
        db.execute(
            """INSERT OR IGNORE INTO students (roll_no,name,email,phone,gender,dob,course,year,status,address,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (*s, "Pune, Maharashtra", datetime.now().isoformat(timespec="seconds")))
    db.commit()
    print("Sample students added.")

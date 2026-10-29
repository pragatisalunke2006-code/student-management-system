import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app  # noqa: E402

STUDENT = {
    "roll_no": "CS001", "name": "Test Student", "email": "t@example.com",
    "phone": "9999999999", "gender": "Female", "dob": "2005-01-01",
    "course": "Computer Science", "year": "2", "status": "Active", "address": "Pune",
}


class StudentAppTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app({"DATABASE": self.path, "TESTING": True})
        self.client = self.app.test_client()

    def tearDown(self):
        os.remove(self.path)

    def token(self, url="/students/new"):
        html = self.client.get(url).get_data(as_text=True)
        return re.search(r'name="_csrf" value="([^"]+)"', html).group(1)

    def add(self, **over):
        data = {**STUDENT, **over, "_csrf": self.token()}
        return self.client.post("/students/new", data=data, follow_redirects=True)

    def test_dashboard_loads(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_add_and_list(self):
        r = self.add()
        self.assertIn(b"Added Test Student", r.data)
        self.assertIn(b"CS001", self.client.get("/students").data)

    def test_duplicate_roll_rejected(self):
        self.add()
        r = self.add(email="other@example.com")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"already belongs", r.data)

    def test_invalid_email_rejected(self):
        self.assertEqual(self.add(email="nope").status_code, 400)

    def test_edit_and_delete(self):
        self.add()
        t = self.token("/students/1/edit")
        r = self.client.post("/students/1/edit", data={**STUDENT, "name": "Renamed", "_csrf": t},
                             follow_redirects=True)
        self.assertIn(b"Renamed", r.data)
        r = self.client.post("/students/1/delete", data={"_csrf": t}, follow_redirects=True)
        self.assertIn(b"Deleted Renamed", r.data)

    def test_search_filter(self):
        self.add()
        self.assertIn(b"CS001", self.client.get("/students?q=Test").data)
        self.assertNotIn(b"CS001", self.client.get("/students?q=zzz").data)

    def test_csv_export(self):
        self.add()
        r = self.client.get("/students/export.csv")
        self.assertEqual(r.mimetype, "text/csv")
        self.assertIn(b"Test Student", r.data)

    def test_csrf_blocks_post(self):
        self.assertEqual(self.client.post("/students/new", data=STUDENT).status_code, 400)


if __name__ == "__main__":
    unittest.main()

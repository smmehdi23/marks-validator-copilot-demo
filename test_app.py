import json
import unittest
import urllib.error
import urllib.request


def api_request(path: str, method: str = "GET", payload: dict | None = None):
    url = f"http://127.0.0.1:8000{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=3) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


class TestMarksValidator(unittest.TestCase):
    def test_valid_student_mark(self):
        status, body = api_request(
            "/api/records",
            method="POST",
            payload={"student": "Sara", "score": 88},
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["student"], "Sara")
        self.assertEqual(body["grade"], "A")

    def test_whitespace_trimmed_in_student_name(self):
        status, body = api_request(
            "/api/records",
            method="POST",
            payload={"student": "  Bilal  ", "score": 72},
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["student"], "Bilal")
        self.assertEqual(body["grade"], "B")

    def test_empty_student_name_returns_400(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            api_request(
                "/api/records",
                method="POST",
                payload={"student": "   ", "score": 75},
            )
        self.assertEqual(ctx.exception.code, 400)

    def test_out_of_range_score_returns_400(self):
        for score in (-1, 140):
            with self.subTest(score=score):
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    api_request(
                        "/api/records",
                        method="POST",
                        payload={"student": "Zain", "score": score},
                    )
                self.assertEqual(ctx.exception.code, 400)

    def test_invalid_json_returns_400(self):
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/records",
            data=b"{",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=3)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)

import json
import math
from http.server import BaseHTTPRequestHandler, HTTPServer

RECORDS = []

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Student Marks &amp; Grade Validator</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; background: #f5f7fa; color: #1e293b; }
    .card { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); margin-bottom: 20px; }
    h1 { margin-top: 0; font-size: 22px; }
    label { display: block; margin-top: 12px; font-weight: 600; font-size: 14px; }
    input { width: 100%; padding: 9px 10px; margin-top: 6px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
    button { margin-top: 16px; padding: 10px 18px; background: #2563eb; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; }
    button:hover { background: #1d4ed8; }
    .msg { margin-top: 12px; padding: 10px; border-radius: 6px; font-size: 14px; display: none; }
    .err { background: #fee2e2; color: #991b1b; display: block; }
    .ok { background: #dcfce7; color: #166534; display: block; }
    ul { list-style: none; padding: 0; margin: 0; }
    li { padding: 10px 12px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; }
    li:last-child { border-bottom: none; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Marks &amp; Grade Validator</h1>
    <form id="markForm">
      <label for="student">Student Name</label>
      <input id="student" name="student" type="text" placeholder="e.g. Ali Raza" required />

      <label for="score">Score (0 - 100)</label>
      <input id="score" name="score" type="number" step="any" placeholder="e.g. 85" required />

      <button type="submit">Validate &amp; Save</button>
    </form>
    <div id="feedback" class="msg"></div>
  </div>

  <div class="card">
    <h2>Evaluated Records</h2>
    <ul id="recordsList"></ul>
  </div>

  <script>
    const form = document.getElementById("markForm");
    const feedback = document.getElementById("feedback");
    const list = document.getElementById("recordsList");

    async function loadRecords() {
      const res = await fetch("/api/records");
      const data = await res.json();
      list.innerHTML = "";
      for (const r of data.records) {
        const li = document.createElement("li");
        li.innerHTML = `<span><strong>${r.student}</strong> — Score: ${r.score}</span><span>Grade: <strong>${r.grade}</strong></span>`;
        list.appendChild(li);
      }
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      feedback.className = "msg";
      const student = document.getElementById("student").value;
      const score = Number(document.getElementById("score").value);

      const res = await fetch("/api/records", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student, score })
      });
      const data = await res.json();
      if (!res.ok) {
        feedback.textContent = data.error || "Invalid input";
        feedback.className = "msg err";
        return;
      }
      feedback.textContent = `Saved ${data.student} with Grade ${data.grade}`;
      feedback.className = "msg ok";
      form.reset();
      loadRecords();
    });

    loadRecords();
  </script>
</body>
</html>
"""


def validate_mark(student: str, score: float) -> dict:
    if not isinstance(student, str):
        raise ValueError("Student name must be a string")
    student = student.strip()
    if not student:
        raise ValueError("Student name cannot be empty")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise ValueError("Score must be a number")
    if not math.isfinite(score) or not 0 <= score <= 100:
        raise ValueError("Score must be between 0 and 100")

    if score >= 80:
        grade = "A"
    elif score >= 60:
        grade = "B"
    elif score >= 50:
        grade = "C"
    else:
        grade = "F"

    entry = {
        "id": len(RECORDS) + 1,
        "student": student,
        "score": score,
        "grade": grade,
    }
    RECORDS.append(entry)
    return entry


class AppHandler(BaseHTTPRequestHandler):
    def _send_html(self, status_code: int, html: str):
        body = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._send_html(200, HTML_PAGE)
        elif self.path == "/api/records":
            self._send_json(200, {"records": RECORDS})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/records":
            self._send_json(404, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)
        try:
            data = json.loads(raw_body.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Request body must be a JSON object")
            record = validate_mark(data.get("student"), data.get("score"))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            self._send_json(400, {"error": str(error)})
            return

        self._send_json(201, record)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), AppHandler)
    print("Marks Validator UI running at http://127.0.0.1:8000")
    server.serve_forever()

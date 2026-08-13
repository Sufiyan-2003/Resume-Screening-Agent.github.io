from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]

def test_health():
    assert client.get("/api/health").json() == {"status":"ok"}

def test_analyze_ten_resumes(monkeypatch):
    monkeypatch.setattr("backend.api.routes.semantic_scores", lambda jd, texts: [70.0]*len(texts))
    jd = (ROOT / "data/sample_jd/python_backend_jd.txt").read_text()
    handles = [("resumes", (p.name, p.read_bytes(), "text/plain")) for p in (ROOT / "data/sample_resumes").glob("*.txt")]
    response = client.post("/api/analyze", data={"job_description":jd}, files=handles)
    assert response.status_code == 200, response.text
    assert response.json()["total_candidates"] == 10

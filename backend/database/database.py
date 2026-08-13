import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "resume_screening.db"

def connection():
    con = sqlite3.connect(DB_PATH); con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE IF NOT EXISTS screening_runs (id INTEGER PRIMARY KEY, job_title TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, total_candidates INTEGER, jd_json TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS candidates (id INTEGER PRIMARY KEY, run_id INTEGER, payload TEXT)")
    return con

def save_run(jd: dict, candidates: list[dict]) -> int:
    con = connection(); cur = con.execute("INSERT INTO screening_runs (job_title,total_candidates,jd_json) VALUES (?,?,?)", (jd["job_title"], len(candidates), json.dumps(jd))); run_id = cur.lastrowid
    for c in candidates:
        con.execute("INSERT INTO candidates (run_id,payload) VALUES (?,?)", (run_id, json.dumps(c)))
    con.commit(); con.close(); return run_id

def get_run(run_id: int) -> dict | None:
    con = connection(); run = con.execute("SELECT * FROM screening_runs WHERE id=?", (run_id,)).fetchone()
    if not run: con.close(); return None
    candidates = [json.loads(r["payload"]) | {"id": r["id"]} for r in con.execute("SELECT * FROM candidates WHERE run_id=?", (run_id,))]
    con.close(); return {"id": run["id"], "job_title": run["job_title"], "created_at": run["created_at"], "total_candidates": run["total_candidates"], "jd": json.loads(run["jd_json"]), "candidates": candidates}

def list_runs() -> list[dict]:
    con = connection(); rows = con.execute("SELECT id,job_title,created_at,total_candidates FROM screening_runs ORDER BY id DESC").fetchall(); con.close(); return [dict(r) for r in rows]

def get_candidate(candidate_id: int) -> dict | None:
    con = connection(); row = con.execute("SELECT payload FROM candidates WHERE id=?", (candidate_id,)).fetchone(); con.close()
    return json.loads(row["payload"]) | {"id": candidate_id} if row else None

def reset():
    con = connection(); con.execute("DELETE FROM candidates"); con.execute("DELETE FROM screening_runs"); con.commit(); con.close()

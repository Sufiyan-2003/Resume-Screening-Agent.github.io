import csv
import io
import json

FIELDS = ["rank", "name", "email", "score", "semantic_score", "skills_score", "experience_score", "education_score", "preferred_skills_score", "recommendation", "matched_skills", "missing_skills"]

def csv_export(candidates: list[dict]) -> str:
    stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=FIELDS); writer.writeheader()
    for c in candidates:
        row = {k: c.get(k, "") for k in FIELDS}; row["matched_skills"] = "; ".join(c["matched_skills"]); row["missing_skills"] = "; ".join(c["missing_skills"]); writer.writerow(row)
    return stream.getvalue()

def json_export(run: dict) -> str:
    return json.dumps(run, indent=2)

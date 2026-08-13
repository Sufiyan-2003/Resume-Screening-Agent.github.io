import json
import os
from urllib.request import Request, urlopen


def _template(candidate: dict, jd: dict) -> str:
    matched = ", ".join(candidate["matched_skills"]) or "no required skills"
    missing = ", ".join(candidate["missing_skills"]) or "no required skills"
    exp = f"{candidate['experience_years']} years" if candidate["experience_years"] is not None else "experience was not explicitly found"
    return (f"{candidate['recommendation']}. The candidate matches {len(candidate['matched_skills'])} of "
            f"{len(jd['required_skills'])} required skills ({matched}). Their stated experience is {exp}. "
            f"Missing required skills: {missing}. This explanation is based only on extracted resume evidence.")


def explain(candidate: dict, jd: dict) -> str:
    """Use Groq only for wording; deterministic data remains the source of truth."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return _template(candidate, jd)
    facts = {k: candidate.get(k) for k in ("score", "recommendation", "matched_skills", "missing_skills", "experience_years", "semantic_score", "skills_score", "experience_score", "education_score", "preferred_skills_score")}
    prompt = ("Explain this resume screening decision in two concise sentences. Use ONLY these facts; "
              "do not recalculate any score or invent qualifications. State unavailable evidence as not found. "
              f"Job title: {jd['job_title']}. Facts: {json.dumps(facts)}")
    payload = json.dumps({"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}).encode()
    try:
        request = Request("https://api.groq.com/openai/v1/chat/completions", data=payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=8) as response:
            content = json.loads(response.read())["choices"][0]["message"]["content"].strip()
        return content or _template(candidate, jd)
    except Exception:
        return _template(candidate, jd)

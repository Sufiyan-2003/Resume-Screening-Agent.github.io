import re
from .skill_extractor import extract_skills


def parse_jd(text: str) -> dict:
    skills = extract_skills(text)
    lower = text.lower()
    preferred_markers = ("preferred", "nice to have", "bonus", "plus:")
    preferred = []
    for line in re.split(r"[\n.;]", text):
        if any(marker in line.lower() for marker in preferred_markers):
            preferred.extend(extract_skills(line))
    preferred = sorted(set(preferred), key=str.lower)
    required = [s for s in skills if s not in preferred]
    exp = re.search(r"(?:minimum|at least|required|with)?\s*(\d+)\+?\s*(?:years?|yrs?)", lower)
    education = next((x for x in ["PhD", "Master's", "Bachelor's", "B.Tech", "B.E."] if x.lower() in lower), None)
    title_match = re.search(r"(?:job title|position|role)\s*[:\-]\s*([^\n.]+)", text, re.I)
    if not title_match:
        title_match = re.search(r"\b(?:Senior |Junior |Lead )?(?:Python |Backend |Software |Machine Learning |Data )?(?:Engineer|Developer|Scientist|Analyst)\b", text, re.I)
    return {"job_title": title_match.group(1).strip() if title_match and title_match.lastindex else (title_match.group(0) if title_match else "Untitled role"), "required_skills": required, "preferred_skills": preferred, "required_experience": int(exp.group(1)) if exp else None, "education": education, "responsibilities": text[:1000]}

import re


def extract_years(text: str) -> int | None:
    matches = re.findall(r"(?:over|more than)?\s*(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience", text, re.I)
    return max(map(int, matches)) if matches else None


def experience_score(candidate_years: int | None, required_years: int | None) -> float:
    if not required_years:
        return 100.0
    if candidate_years is None:
        return 50.0
    return round(min(100, 100 * candidate_years / required_years), 2)


def education_score(text: str, requirement: str | None) -> float:
    if not requirement:
        return 100.0
    levels = {"bachelor's": 1, "b.tech": 1, "b.e.": 1, "master's": 2, "phd": 3}
    req = next((v for k, v in levels.items() if k in requirement.lower()), 1)
    got = max((v for k, v in levels.items() if k in text.lower()), default=0)
    return 100.0 if got >= req else (50.0 if got else 30.0)


def score_candidate(semantic: float, candidate_skills: list[str], jd: dict, resume_text: str) -> dict:
    required, preferred = jd["required_skills"], jd["preferred_skills"]
    matched = sorted(set(candidate_skills) & set(required), key=str.lower)
    missing = sorted(set(required) - set(candidate_skills), key=str.lower)
    skills = 100 * len(matched) / len(required) if required else 100.0
    pref = 100 * len(set(candidate_skills) & set(preferred)) / len(preferred) if preferred else 100.0
    years = extract_years(resume_text)
    exp = experience_score(years, jd["required_experience"])
    edu = education_score(resume_text, jd["education"])
    final = round(semantic*.40 + skills*.30 + exp*.15 + edu*.10 + pref*.05, 2)
    return {"score": final, "semantic_score": semantic, "skills_score": round(skills, 2), "experience_score": exp, "education_score": edu, "preferred_skills_score": round(pref, 2), "matched_skills": matched, "missing_skills": missing, "additional_skills": sorted(set(candidate_skills)-set(required)-set(preferred)), "experience_years": years}

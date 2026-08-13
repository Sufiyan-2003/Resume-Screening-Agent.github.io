import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
with open(ROOT / "data" / "skills.json", encoding="utf-8") as f:
    SKILLS = json.load(f)

ALIASES = {"rest": "REST API", "restful api": "REST API", "rest api": "REST API", "mongo": "MongoDB", "node": "Node.js", "github": "GitHub", "scikit learn": "scikit-learn"}
ALL_SKILLS = [s for values in SKILLS.values() for s in values]


def normalize_skill(skill: str) -> str:
    raw = re.sub(r"\s+", " ", skill.strip().lower())
    return ALIASES.get(raw, next((s for s in ALL_SKILLS if s.lower() == raw), skill.strip()))


def extract_skills(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        variants = [skill.lower()] + [a for a, canonical in ALIASES.items() if canonical.lower() == skill.lower()]
        if any(re.search(r"(?<!\w)" + re.escape(v) + r"(?!\w)", lower) for v in variants):
            found.append(skill)
    return sorted(set(found), key=str.lower)

import re
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from ..services.resume_parser import parse_upload
from ..services.jd_parser import parse_jd
from ..services.skill_extractor import extract_skills
from ..services.embeddings import semantic_scores
from ..services.scoring import score_candidate
from ..services.ranking import rank
from ..services.llm_reasoner import explain
from ..services.export_service import csv_export, json_export
from ..database import database

router = APIRouter(prefix="/api")

def identity(text: str, fallback: str) -> dict:
    """
    Extract candidate identity from resume text.

    Priority:
    1. Explicit name fields
    2. A likely person's name from the resume header
    3. Email-derived name
    4. Generic fallback
    """

    # ---------------------------------------------------------
    # Extract email
    # ---------------------------------------------------------
    email_match = re.search(
        r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        text
    )

    email = email_match.group(0) if email_match else None

    # ---------------------------------------------------------
    # Extract phone
    # ---------------------------------------------------------
    phone_match = re.search(
        r"(?:\+?\d[\d\s().-]{8,}\d)",
        text
    )

    phone = phone_match.group(0) if phone_match else None

    # ---------------------------------------------------------
    # Clean resume lines
    # ---------------------------------------------------------
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # ---------------------------------------------------------
    # 1. Look for explicit name fields
    #
    # Examples:
    # Name: Priya Rao
    # Full Name: Priya Rao
    # Candidate Name: Priya Rao
    # ---------------------------------------------------------
    name_patterns = [
        r"^(?:full\s+name|candidate\s+name|name)\s*[:\-]\s*(.+)$"
    ]

    for line in lines[:20]:
        for pattern in name_patterns:
            match = re.match(pattern, line, re.IGNORECASE)

            if match:
                possible_name = match.group(1).strip()

                if _is_valid_name(possible_name):
                    return {
                        "name": possible_name[:80],
                        "email": email,
                        "phone": phone,
                    }

    # ---------------------------------------------------------
    # 2. Look for a likely name in the resume header
    # ---------------------------------------------------------
    for line in lines[:12]:

        possible_name = re.sub(
            r"[^A-Za-z .'-]",
            "",
            line
        ).strip()

        if _is_valid_name(possible_name):
            return {
                "name": possible_name[:80],
                "email": email,
                "phone": phone,
            }

    # ---------------------------------------------------------
    # 3. Email fallback
    #
    # priya.rao@example.com
    #        ↓
    # priya.rao
    #        ↓
    # Priya Rao
    # ---------------------------------------------------------
    if email:
        email_username = email.split("@")[0]

        email_username = re.sub(
            r"[._\-]+",
            " ",
            email_username
        )

        email_username = re.sub(
            r"\d+",
            "",
            email_username
        )

        email_username = re.sub(
            r"\s+",
            " ",
            email_username
        ).strip()

        if email_username:
            name_from_email = email_username.title()

            if _is_valid_name(name_from_email):
                return {
                    "name": name_from_email[:80],
                    "email": email,
                    "phone": phone,
                }

    # ---------------------------------------------------------
    # 4. Final fallback
    # ---------------------------------------------------------
    return {
        "name": fallback,
        "email": email,
        "phone": phone,
    }


def _is_valid_name(value: str) -> bool:
    """
    Check whether a string looks like a person's name.
    """

    if not value:
        return False

    value = value.strip()

    # Reasonable name length
    if len(value) < 3 or len(value) > 80:
        return False

    lower = value.lower()

    # Common resume headings that must not become names
    invalid_values = {
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "professional summary",
        "summary",
        "objective",
        "experience",
        "work experience",
        "education",
        "skills",
        "technical skills",
        "projects",
        "certifications",
        "contact",
        "contact information",
        "references",
        "junior ai engineer",
        "ai engineer",
        "software engineer",
        "python backend engineer",
    }

    if lower in invalid_values:
        return False

    # Never treat an email as a name
    if "@" in value:
        return False

    # Never treat URLs as names
    if "http://" in lower or "https://" in lower or "www." in lower:
        return False

    # Reject lines containing too many numbers
    if sum(char.isdigit() for char in value) > 2:
        return False

    words = value.split()

    # Most normal names contain 2–5 words
    if len(words) < 2 or len(words) > 5:
        return False

    # Every word should contain at least one letter
    if not all(re.search(r"[A-Za-z]", word) for word in words):
        return False

    return True

@router.get("/health")
def health(): return {"status": "ok"}

@router.post("/analyze")
async def analyze(job_description: str = Form(""), jd_file: UploadFile | None = File(None), resumes: list[UploadFile] = File(...)):
    if jd_file:
        job_description = await parse_upload(jd_file)
    if not job_description.strip(): raise HTTPException(400, "A job description is required.")
    if not resumes: raise HTTPException(400, "Upload at least one resume.")
    if len(resumes) > 50: raise HTTPException(400, "A maximum of 50 resumes can be analyzed per run.")
    jd = parse_jd(job_description)
    texts = [await parse_upload(f) for f in resumes]
    semantics = semantic_scores(job_description, texts)
    candidates = []
    for i, (file, text, semantic) in enumerate(zip(resumes, texts, semantics), 1):
        candidate = identity(text, f"Candidate {i}") | score_candidate(semantic, extract_skills(text), jd, text)
        candidate["raw_text"] = text
        candidates.append(candidate)
    candidates = rank(candidates)
    for c in candidates: c["reasoning"] = explain(c, jd)
    run_id = database.save_run(jd, candidates)
    run = database.get_run(run_id)
    return run

@router.get("/results")
def results(): return database.list_runs()
@router.get("/results/{run_id}")
def result(run_id: int):
    run = database.get_run(run_id)
    if not run: raise HTTPException(404, "Screening run not found.")
    return run
@router.get("/candidate/{candidate_id}")
def candidate(candidate_id: int):
    value = database.get_candidate(candidate_id)
    if not value: raise HTTPException(404, "Candidate not found.")
    return value
@router.get("/export/{run_id}/csv")
def export_csv(run_id: int):
    run = database.get_run(run_id)
    if not run: raise HTTPException(404, "Screening run not found.")
    return Response(csv_export(run["candidates"]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=screening-{run_id}.csv"})
@router.get("/export/{run_id}/json")
def export_json(run_id: int):
    run = database.get_run(run_id)
    if not run: raise HTTPException(404, "Screening run not found.")
    return Response(json_export(run), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=screening-{run_id}.json"})
@router.post("/reset")
def reset(): database.reset(); return {"status": "reset"}

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
    email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    phone = re.search(r"(?:\+?\d[\d\s().-]{8,}\d)", text)
    first = next((line.strip() for line in text.splitlines() if len(line.strip()) > 2 and not re.search(r"@|\d{3}", line)), fallback)
    return {"name": re.sub(r"[^A-Za-z .'-]", "", first).strip()[:80] or fallback, "email": email.group(0) if email else None, "phone": phone.group(0) if phone else None}

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

from backend.services.skill_extractor import extract_skills, normalize_skill
from backend.services.scoring import score_candidate
from backend.services.ranking import rank

def test_skill_normalization_and_extraction():
    assert normalize_skill("mongo") == "MongoDB"
    assert set(extract_skills("PYTHON, RESTful API and Mongo")) >= {"Python", "REST API", "MongoDB"}

def test_transparent_scoring_and_ranking():
    jd = {"required_skills":["Python","FastAPI"],"preferred_skills":[],"required_experience":2,"education":"Bachelor's"}
    high = score_candidate(90,["Python","FastAPI"],jd,"3 years experience. Bachelor's degree")
    low = score_candidate(30,["Python"],jd,"1 year experience")
    assert high["score"] > low["score"]
    assert rank([low,high])[0]["score"] == high["score"]

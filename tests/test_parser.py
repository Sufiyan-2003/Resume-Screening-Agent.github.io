from pathlib import Path
from backend.services.resume_parser import parse_path

def test_txt_extraction():
    path = Path(__file__).resolve().parents[1] / "data/sample_resumes/01_avery_shah.txt"
    assert "Avery Shah" in parse_path(path)

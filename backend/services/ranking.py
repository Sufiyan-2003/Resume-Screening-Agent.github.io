def recommendation(score: float) -> str:
    if score >= 80: return "Strong Match"
    if score >= 65: return "Good Match"
    if score >= 45: return "Moderate Match"
    return "Low Match"


def rank(candidates: list[dict]) -> list[dict]:
    ordered = sorted(candidates, key=lambda c: c["score"], reverse=True)
    for i, candidate in enumerate(ordered, 1):
        candidate["rank"] = i
        candidate["recommendation"] = recommendation(candidate["score"])
    return ordered

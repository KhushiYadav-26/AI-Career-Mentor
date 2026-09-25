from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def rank(items: list[dict], career: str, skills: list[str], kind: str) -> list[dict]:
    if not items: return []
    query = " ".join([career, *skills])
    texts = [" ".join(map(str, [item.get("career", ""), item.get("skill", ""), item.get("description", ""), *item.get("skills", [])])) for item in items]
    matrix = TfidfVectorizer(stop_words="english").fit_transform([query, *texts])
    scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    result = []
    wanted = {s.lower() for s in skills}
    for item, score in zip(items, scores):
        item = dict(item)
        item_skills = item.get("skills", [item.get("skill", "")])
        overlap = [s for s in item_skills if s.lower() in wanted]
        item["score"] = float(score) + .12 * len(overlap) + (.25 if item.get("career") == career else 0)
        item["why"] = "Builds " + ", ".join(overlap or item_skills[:2]) + "."
        result.append(item)
    return sorted(result, key=lambda x: x["score"], reverse=True)

import re
from .helpers import all_skills
from .nlp_utils import extract_known_skills

SECTIONS = {"Contact":r"(?:email|phone|linkedin|@)","Summary":r"(?:summary|profile|objective)","Education":r"(?:education|university|college|bachelor|master)","Skills":r"(?:skills|technical skills)","Projects":r"(?:projects|portfolio)","Experience":r"(?:experience|employment|internship)","Certifications":r"(?:certifications?|certificates?)"}

def analyze_resume(text: str, career: dict):
    lowered = text.lower()
    required = all_skills(career)
    matched = extract_known_skills(lowered, required)
    missing = [skill for skill in required if skill not in matched]
    sections = [name for name, pattern in SECTIONS.items() if re.search(pattern, lowered)]
    skill_score = len(matched) / max(1, len(required)) * 50
    keyword_score = min(20, len(set(re.findall(r"\b[a-z]{4,}\b", lowered)) & {s.lower() for s in required}) * 4)
    section_score = len(sections) / len(SECTIONS) * 15
    quality_score = 15 if len(text.split()) >= 120 else min(15, len(text.split()) / 120 * 15)
    score = round(skill_score + keyword_score + section_score + quality_score)
    suggestions = [f"Add {skill} to your skills or project experience." for skill in missing[:4]]
    if "Projects" not in sections: suggestions.append("Add a projects section with measurable outcomes.")
    return {"score":score,"matched":matched,"missing":missing,"sections":sections,"suggestions":suggestions}

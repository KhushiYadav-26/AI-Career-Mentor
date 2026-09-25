"""Small, dependency-light NLP helpers used across the application."""
import re

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z.+#-]*", clean_text(text))

def extract_known_skills(text: str, skills: list[str]) -> list[str]:
    """Find complete known skills, preserving multi-word names such as Machine Learning."""
    cleaned = clean_text(text)
    return [skill for skill in skills if re.search(r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)", cleaned)]

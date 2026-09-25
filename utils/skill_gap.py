from .helpers import all_skills

def analyze(career: dict, current: list[str]) -> dict:
    required = all_skills(career)
    normalized = {skill.lower(): skill for skill in current}
    matched = [skill for skill in required if skill.lower() in normalized]
    missing = [skill for skill in required if skill.lower() not in normalized]
    required_lower = {skill.lower() for skill in required}
    extra = [skill for skill in current if skill.lower() not in required_lower]
    readiness = round((len(matched) / len(required) * 100) if required else 0)
    levels = {level:[skill for skill in missing if skill in skills] for level, skills in career.get("skills", {}).items()}
    return {"required":required,"matched":matched,"missing":missing,"extra":extra,"readiness":readiness,"levels":levels}

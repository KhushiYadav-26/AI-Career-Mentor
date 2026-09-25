from __future__ import annotations
import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

@st.cache_data
def load_json(name: str):
    path = ROOT / "data" / name
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(f"Could not read {name}: {error.msg}") from error

def all_skills(career: dict) -> list[str]:
    return [skill for skills in career.get("skills", {}).values() for skill in skills]

def skill_level(career: dict, skill: str) -> str:
    for level, skills in career.get("skills", {}).items():
        if skill.lower() == skill.lower().strip() and skill in skills:
            return level
    return "Additional"

def normalize_skill(value: str, aliases: dict) -> str:
    cleaned = value.strip().lower().replace("_", " ")
    return aliases.get(cleaned, next((v for v in aliases.values() if v.lower() == cleaned), value.strip()))

def initialize_state():
    defaults = {"page":"Dashboard", "career_id":None, "current_skills":[], "name":"", "goal":"", "skill_status":{}, "ats":None, "chat":[], "authenticated":False, "user_id":None, "auth_provider":None, "avatar_path":None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

"""Small SQLite-backed authentication and profile store for local development."""
from __future__ import annotations
import hashlib, hmac, json, os, secrets, sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "career_mentor.db"

def connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
        password_hash TEXT, provider TEXT NOT NULL DEFAULT 'local', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    db.execute("""CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY, state_json TEXT NOT NULL DEFAULT '{}', updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id))""")
    return db

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex()
    return f"{salt}${digest}"

def verify_password(password: str, stored: str | None) -> bool:
    if not stored or "$" not in stored: return False
    salt, digest = stored.split("$", 1)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex()
    return hmac.compare_digest(actual, digest)

def register(email: str, name: str, password: str):
    email = email.strip().lower()
    if not email or "@" not in email: raise ValueError("Enter a valid email address.")
    if len(password) < 8: raise ValueError("Use a password with at least 8 characters.")
    try:
        db = connection(); cur = db.execute("INSERT INTO users(email,name,password_hash,provider) VALUES (?,?,?,?)", (email, name.strip() or email.split("@")[0], hash_password(password), "local")); db.commit()
        return dict(db.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone())
    except sqlite3.IntegrityError as error: raise ValueError("An account already exists for this email.") from error

def login(email: str, password: str):
    db = connection(); row = db.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    return dict(row) if row and verify_password(password, row["password_hash"]) else None

def find_user(email: str):
    row = connection().execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    return dict(row) if row else None

def google_user(email: str, name: str):
    db = connection(); row = db.execute("SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
    if row: return dict(row)
    cur = db.execute("INSERT INTO users(email,name,provider) VALUES (?,?,?)", (email.lower(), name or email.split("@")[0], "google")); db.commit()
    return dict(db.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone())

def load_profile(user_id: int) -> dict:
    row = connection().execute("SELECT state_json FROM profiles WHERE user_id=?", (user_id,)).fetchone()
    try: return json.loads(row["state_json"]) if row else {}
    except json.JSONDecodeError: return {}

def save_profile(user_id: int, state: dict):
    db = connection(); db.execute("INSERT INTO profiles(user_id,state_json,updated_at) VALUES (?,?,CURRENT_TIMESTAMP) ON CONFLICT(user_id) DO UPDATE SET state_json=excluded.state_json, updated_at=CURRENT_TIMESTAMP", (user_id, json.dumps(state))); db.commit()

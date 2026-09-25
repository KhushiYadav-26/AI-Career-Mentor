# AI Career Mentor using NLP & ML

A Streamlit career-guidance application for a college mini-project. It provides career exploration, skill-gap analysis, BFS/DFS/A* learning paths, a personalized roadmap, explainable course and project recommendations, an ATS-style resume review, a knowledge-based chat mentor, profile settings, and PDF reports.

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Notes

- Career, project, course, and skill-alias data live under `data/` and can be expanded without editing application code.
- Resume analysis supports PDF, DOCX, and TXT. The score is an educational estimate, not a commercial ATS decision.
- The mentor works without an external API; no key is needed.
- Session data is intentionally temporary. A database can be added later if persistent profiles are needed.

## Accounts and remembered sign-in

Local accounts and each user's learning details are stored in `data/career_mentor.db` (SQLite). Passwords are salted and PBKDF2-hashed; passwords are never stored in plain text. The **Remember me** checkbox stores an encrypted device cookie with the account identifier, not the password. Before production, set `CAREER_MENTOR_COOKIE_SECRET` to a long private value.

The current interface uses secure local account sign-in only. Google sign-in has been removed from the visible product flow.

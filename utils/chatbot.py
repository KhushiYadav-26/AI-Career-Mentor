def reply(question, career, gap, ats):
    q = question.lower()
    if not career: return "Choose a target career first, then I can tailor guidance to you."
    if "skill gap" in q or "ready" in q: return f"Your current readiness for {career['name']} is {gap['readiness']}%. Focus next on {', '.join(gap['missing'][:3]) or 'building projects'} ."
    if "project" in q: return f"Start with: {', '.join(career.get('projects', [])[:2])}. Pick one that uses your next missing skill."
    if "course" in q: return f"Look for a beginner course covering {gap['missing'][0] if gap['missing'] else 'your selected specialization'} and apply it in a small project."
    if "resume" in q: return (f"Your ATS-style estimated score is {ats['score']}/100. " if ats else "Upload a resume for a personalized score. ") + "Include role-relevant skills, projects, and measurable outcomes."
    return f"For {career['name']}, learn in this order: {' → '.join(career['learning_path'][:5])}. Your next useful step is {gap['missing'][0] if gap['missing'] else 'a portfolio project'}."

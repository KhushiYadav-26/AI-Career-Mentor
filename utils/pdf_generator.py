from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def create_report(name, career, current, gap, paths, projects, courses, ats):
    output = BytesIO(); doc = SimpleDocTemplate(output, pagesize=A4); styles = getSampleStyleSheet(); story = []
    def section(title, body):
        story.extend([Paragraph(title, styles['Heading2']), Paragraph(body or 'Not analyzed yet', styles['BodyText']), Spacer(1, 10)])
    story.append(Paragraph('AI Career Mentor — Career Guidance Report', styles['Title']))
    section('Student information', f'Name: {name or "Student"}<br/>Target career: {career["name"]}')
    section('Current skills', ', '.join(current)); section('Skill gap', f'Readiness: {gap["readiness"]}%<br/>Matched: {", ".join(gap["matched"])}<br/>Missing: {", ".join(gap["missing"])}')
    section('Learning roadmap', ' → '.join(career['learning_path']))
    for algo, path in paths.items(): section(f'{algo} analysis', ' → '.join(path) if path else 'No path generated')
    section('Recommended projects', '<br/>'.join(p['title'] for p in projects[:4])); section('Recommended courses', '<br/>'.join(c['name'] for c in courses[:4]))
    section('ATS-style estimated score', f"{ats['score']}/100" if ats else 'No resume analyzed')
    doc.build(story); return output.getvalue()

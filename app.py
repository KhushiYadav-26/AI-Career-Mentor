from pathlib import Path
import base64
import os
import textwrap
import streamlit as st
from utils.helpers import load_json, initialize_state, all_skills, normalize_skill
from utils.skill_gap import analyze
from utils.algorithms import build_graph, bfs, dfs, astar
from utils.recommendations import rank
from utils.resume_parser import extract_text
from utils.ats_analyzer import analyze_resume
from utils.chatbot import reply
from utils.pdf_generator import create_report
from utils.auth import register, login, find_user, load_profile, save_profile
try:
    from streamlit_cookies_manager import EncryptedCookieManager
except ImportError:
    EncryptedCookieManager = None

st.set_page_config(page_title="CareerMentor", page_icon="🎯", layout="wide")
def render_html(content): st.html(textwrap.dedent(content).strip())
ROOT = Path(__file__).resolve().parent
def asset_path(name): return ROOT / name
def has_asset(name):
    try: return asset_path(name).exists()
    except Exception: return False
def image_data_url(name):
    path = asset_path(name)
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


UNSPLASH = {
    "study":    "1760351561007-526f5353cc76",  # two students studying with a laptop
    "mountain": "1754762646500-d741ed975cd1",  # hiker reaching a mountain summit
    "code":     "1555066931-4365d14bab8c",     # MacBook with code on screen
    "data":     "1460925895917-afdab827c52f",  # laptop with charts/statistics
    "security": "1768839720936-87ce3adf2d08",  # padlock on a keyboard
    "design":   "1586717799252-bd134ad00e26",  # MacBook + design/wireframe setup
}
def unsplash_url(key, w=700, q=68):
    return f"https://images.unsplash.com/photo-{UNSPLASH[key]}?auto=format&fit=crop&w={w}&q={q}"
_FALLBACK_SVG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='500'%3E%3Crect width='800' height='500' fill='%239564DD'/%3E%3C/svg%3E"
def img_tag(url, alt="", style=""):
    """<img> that quietly swaps to a solid-color placeholder if the hot-linked photo ever fails to load."""
    safe_alt = alt.replace("'", "")
    return (f"<img src='{url}' alt='{safe_alt}' loading='lazy' style='{style}' "
            f"onerror=\"this.onerror=null;this.src='{_FALLBACK_SVG}';\" />")


CATEGORY_VISUALS = [
    ("security", {"icon": "fa-solid fa-shield-halved", "color": "#0D9488", "image": "security"}),
    ("cyber",    {"icon": "fa-solid fa-shield-halved", "color": "#0D9488", "image": "security"}),
    ("network",  {"icon": "fa-solid fa-diagram-project", "color": "#0891B2", "image": "security"}),
    ("design",   {"icon": "fa-solid fa-pen-nib", "color": "#DB2777", "image": "design"}),
    ("ui",       {"icon": "fa-solid fa-pen-nib", "color": "#DB2777", "image": "design"}),
    ("ux",       {"icon": "fa-solid fa-swatchbook", "color": "#DB2777", "image": "design"}),
    ("mobile",   {"icon": "fa-solid fa-mobile-screen", "color": "#EA580C", "image": "design"}),
    ("data",     {"icon": "fa-solid fa-chart-line", "color": "#16A34A", "image": "data"}),
    ("analytic", {"icon": "fa-solid fa-chart-pie", "color": "#16A34A", "image": "data"}),
    ("database", {"icon": "fa-solid fa-database", "color": "#059669", "image": "data"}),
    ("sql",      {"icon": "fa-solid fa-database", "color": "#059669", "image": "data"}),
    ("machine learning", {"icon": "fa-solid fa-brain", "color": "#7C3AED", "image": "data"}),
    ("ml",       {"icon": "fa-solid fa-brain", "color": "#7C3AED", "image": "data"}),
    ("ai",       {"icon": "fa-solid fa-robot", "color": "#7C3AED", "image": "code"}),
    ("cloud",    {"icon": "fa-solid fa-cloud", "color": "#0284C7", "image": "code"}),
    ("devops",   {"icon": "fa-solid fa-gears", "color": "#B45309", "image": "code"}),
    ("python",   {"icon": "fa-brands fa-python", "color": "#2563EB", "image": "code"}),
    ("javascript", {"icon": "fa-brands fa-js", "color": "#CA8A04", "image": "code"}),
    ("react",    {"icon": "fa-brands fa-react", "color": "#0EA5E9", "image": "code"}),
    ("node",     {"icon": "fa-brands fa-node-js", "color": "#16A34A", "image": "code"}),
    ("web",      {"icon": "fa-solid fa-globe", "color": "#4C6FFF", "image": "code"}),
    ("full stack", {"icon": "fa-solid fa-code", "color": "#4C6FFF", "image": "code"}),
    ("backend",  {"icon": "fa-solid fa-server", "color": "#334155", "image": "code"}),
    ("frontend", {"icon": "fa-solid fa-code", "color": "#4C6FFF", "image": "code"}),
    ("technology", {"icon": "fa-solid fa-microchip", "color": "#4C6FFF", "image": "code"}),
    ("marketing", {"icon": "fa-solid fa-bullhorn", "color": "#DC2626", "image": "study"}),
    ("product",  {"icon": "fa-solid fa-lightbulb", "color": "#CA8A04", "image": "study"}),
    ("business", {"icon": "fa-solid fa-briefcase", "color": "#334155", "image": "study"}),
    ("healthcare", {"icon": "fa-solid fa-heart-pulse", "color": "#DC2626", "image": "study"}),
]
def get_visual(label):
    key = (label or "").lower()
    for needle, visual in CATEGORY_VISUALS:
        if needle in key: return visual
    return {"icon": "fa-solid fa-graduation-cap", "color": "#5B4DE6", "image": "study"}
def reco_card(title_text, meta, description, why, badge=None, price=None):
    visual = get_visual(meta or title_text)
    badge_html = f"<span class='reco-badge'>{badge}</span>" if badge else ""
    price_html = f"<span class='reco-price'>{price}</span>" if price else ""
    photo = img_tag(unsplash_url(visual["image"], w=460, q=60), title_text,
                     "position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.5")
    render_html(f"""
    <div class='reco-card'>
      <div class='reco-cover' style='background:{visual["color"]}'>{photo}{price_html}{badge_html}<i class='{visual["icon"]}' style='position:relative;z-index:2'></i></div>
      <div class='reco-body'>
        <span class='reco-meta'>{meta}</span>
        <h4>{title_text}</h4>
        <p class='reco-desc'>{description}</p>
        <div class='reco-why'>💡 {why}</div>
      </div>
    </div>""")
def hero_art():
    render_html("""
    <div class='hero-art'>
      <i class='fa-solid fa-route'></i>
      <span>🎯 Learn</span>
      <span>📈 Grow</span>
      <span>🚀 Achieve</span>
    </div>""")
def photo_card(photo_key, height=230, radius=18, caption=None):
    photo = img_tag(unsplash_url(photo_key, w=760, q=70), photo_key, "width:100%;height:100%;object-fit:cover;display:block")
    caption_html = f"<div class='photo-card-caption'>{caption}</div>" if caption else ""
    render_html(f"<div class='photo-card' style='border-radius:{radius}px;height:{height}px'>{photo}{caption_html}</div>")
def mini_mountain_card(quote="\u201cProgress, not perfection.\u201d", note="Every step counts."):
    """Small, Figma-style summit card — intentionally compact, not a full-width banner."""
    photo = img_tag(unsplash_url("mountain", w=420, q=62), "Mountain summit", "position:absolute;inset:0;width:100%;height:100%;object-fit:cover")
    render_html(f"""
    <div class='mini-mountain-card'>{photo}
      <div class='mini-mountain-overlay'><i class='fa-solid fa-flag'></i><p>{quote}<br/><small>{note}</small></p></div>
    </div>""")
def section_hero(icon, heading, subtitle):
    render_html(f"""
    <div class='section-hero'>
      <span class='section-hero-icon'><i class='fa-solid {icon}'></i></span>
      <div><h3>{heading}</h3><p>{subtitle}</p></div>
    </div>""")
def fallback_avatar(name, size_class=""):
    letter = (name or "S")[0].upper()
    render_html(f"<div class='fallback-avatar {size_class}'>{letter}</div>")
def progress_ring(percent, label, color="#5B4DE6", size=104):
    """CSS conic-gradient donut — a lightweight 'graph' for a single percentage."""
    percent = max(0, min(100, round(percent)))
    render_html(f"""
    <div class='ring-wrap'>
      <div class='ring' style='width:{size}px;height:{size}px;background:conic-gradient({color} {percent * 3.6}deg, #EDEBFB 0deg)'>
        <div class='ring-hole' style='width:{size - 22}px;height:{size - 22}px'>{percent}%</div>
      </div>
      <span class='ring-label'>{label}</span>
    </div>""")
def pie_chart(labels, values, colors, title=""):
    """Small donut/pie chart via matplotlib — falls back to a plain caption if unavailable."""
    values = [max(0, v) for v in values]
    if sum(values) == 0:
        st.caption("Not enough data yet for a chart.")
        return
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        keep = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
        labels, values, colors = zip(*keep)
        fig, ax = plt.subplots(figsize=(3.1, 3.1))
        wedges, _texts, autotexts = ax.pie(
            values, labels=labels, colors=colors, startangle=90,
            autopct=lambda p: f"{p:.0f}%" if p > 3 else "",
            wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
            textprops={"fontsize": 8.5, "color": "#3E0F8D"},
        )
        for t in autotexts: t.set_color("white"); t.set_fontsize(8.5); t.set_fontweight("bold")
        if title: ax.set_title(title, fontsize=10.5, fontweight="bold", color="#3E0F8D")
        ax.set_aspect("equal"); fig.patch.set_alpha(0)
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)
    except Exception:
        for l, v in zip(labels, values):
            st.caption(f"● {l}: {v}")


ALGO_COLORS = {"BFS": "#4C6FFF", "DFS": "#9564DD", "A*": "#16A34A"}
def graph_edges_from(graph, nodes):
    edges, seen = [], set()
    try:
        items = graph.items() if hasattr(graph, "items") else []
        for node, neighbors in items:
            for nb in (neighbors or []):
                key = tuple(sorted((str(node), str(nb))))
                if key not in seen:
                    seen.add(key); edges.append((node, nb))
    except Exception:
        pass
    if not edges:
        edges = [(nodes[i], nodes[i + 1]) for i in range(len(nodes) - 1)]
    return edges
def draw_algo_graph(nodes, edges, path, color, reveal=None, width=740, height=250):
    import html as _html
    if not nodes: return ""
    path = path or []
    reveal = len(path) if reveal is None else max(0, min(reveal, len(path)))
    visible = path[:reveal]
    cols = max(1, min(len(nodes), 6)); rows = -(-len(nodes) // cols)
    xgap, ygap = width / (cols + 1), height / (rows + 1)
    pos = {}
    for i, node in enumerate(nodes):
        r, c = divmod(i, cols)
        c = c if r % 2 == 0 else (cols - 1 - c)
        pos[node] = (xgap * (c + 1), ygap * (r + 1))
    path_edges = {tuple(sorted((str(visible[i]), str(visible[i + 1])))) for i in range(len(visible) - 1)}
    path_set = {str(p) for p in visible}
    current_node = str(visible[-1]) if visible else None
    svg = [f"<svg viewBox='0 0 {width} {height}' width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg' style='width:100%;height:auto;display:block'>"]
    for a, b in edges:
        if a not in pos or b not in pos: continue
        x1, y1 = pos[a]; x2, y2 = pos[b]
        on_path = tuple(sorted((str(a), str(b)))) in path_edges
        svg.append(f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' "
                   f"stroke='{color if on_path else '#D8DCEF'}' stroke-width='{4 if on_path else 1.6}' stroke-linecap='round'/>")
    for i, node in enumerate(nodes):
        x, y = pos[node]
        on_path = str(node) in path_set
        is_current = str(node) == current_node
        order = visible.index(node) + 1 if node in visible else None
        r = 24 if is_current else (22 if on_path else 16)
        node_class = "graph-node-current" if is_current else ""
        svg.append(f"<circle class='{node_class}' cx='{x:.1f}' cy='{y:.1f}' r='{r}' fill='{color if on_path else '#EDEBFB'}' stroke='white' stroke-width='2'/>")
        if order:
            svg.append(f"<text x='{x:.1f}' y='{y+4:.1f}' font-size='12' font-weight='700' text-anchor='middle' fill='white'>{order}</text>")
        label = _html.escape(str(node))[:14]
        svg.append(f"<text x='{x:.1f}' y='{y+r+15:.1f}' font-size='10.5' text-anchor='middle' fill='#3E0F8D' font-weight='600'>{label}</text>")
    svg.append("</svg>")
    return "".join(svg)

def draw_snake_backdrop(step_count, row_height=140):
    """A winding dark-purple 'road' drawn as an absolute-positioned SVG behind the
    roadmap's step pins, so the vertical list of steps reads as a snaking path."""
    if step_count <= 0:
        return ""
    height = step_count * row_height
    left_x, right_x = 9, 91
    xs = [left_x if i % 2 == 0 else right_x for i in range(step_count)]
    ys = [row_height * (i + 0.5) for i in range(step_count)]
    d = f"M {xs[0]:.1f} {ys[0]:.1f} "
    for i in range(1, step_count):
        x0, y0, x1, y1 = xs[i - 1], ys[i - 1], xs[i], ys[i]
        my = (y0 + y1) / 2
        d += f"C {x0:.1f} {my:.1f}, {x1:.1f} {my:.1f}, {x1:.1f} {y1:.1f} "
    return f"""<div class='snake-road-bg'><svg viewBox='0 0 100 {height}' width='100' height='{height}' preserveAspectRatio='none' xmlns='http://www.w3.org/2000/svg' style='width:100%;height:100%;display:block'>
      <path d='{d}' fill='none' stroke='#1E0F4D' stroke-width='6.5' stroke-linecap='round' opacity='.92'/>
      <path d='{d}' fill='none' stroke='#fff' stroke-width='1.6' stroke-dasharray='1.6 8' stroke-linecap='round' opacity='.95'/>
    </svg></div>"""

def algo_output_list(path, reveal=None):
    """Numbered read-out of the traversal order. Steps beyond `reveal` show dimmed,
    so the list advances in lockstep with the Next-step graph animation."""
    if not path:
        return "<p class='algo-output-empty'>No forward path exists between these two skills.</p>"
    reveal = len(path) if reveal is None else reveal
    items = "".join(
        f"<li class='{'active' if i <= reveal else 'pending'}'><span class='algo-step-no'>{i}</span>{step}</li>"
        for i, step in enumerate(path, 1)
    )
    return f"<ol class='algo-output-list'>{items}</ol>"

css = Path(__file__).parent / "css" / "style.css"
if css.exists(): st.markdown(f"<style>{css.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
initialize_state()

if EncryptedCookieManager is None:
    st.error("Login support needs one dependency. Run: python -m pip install -r requirements.txt")
    st.stop()
cookies = EncryptedCookieManager(prefix="career_mentor/", password=os.getenv("CAREER_MENTOR_COOKIE_SECRET", "set-a-private-cookie-secret-before-production"))
if not cookies.ready(): st.stop()

def load_user(user):
    st.session_state.authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.auth_provider = user.get("provider", "local")
    st.session_state.page = "Dashboard"
    st.session_state.pop("nav_radio", None)
    st.session_state.pop("global_search", None)
    profile = load_profile(user["id"]) or {}
    for key in ("name", "goal", "career_id", "current_skills", "skill_status", "ats", "avatar_path"):
        if key in profile and profile[key] is not None:
            st.session_state[key] = profile[key]
    st.session_state.name = st.session_state.name or user.get("name", "Student")

def go(page):
    st.session_state.page = page
    st.rerun()

def choose(c):
    st.session_state.career_id = c["id"]
    st.session_state.current_skills = []
    st.session_state.skill_status = {}
    st.success(f"{c['name']} is now your target career.")
    go("Skill Gap Analysis")

def show_login():
    render_html("""<div class='auth-top-space'></div>""")
    outer = st.container(border=True)
    with outer:
        illustration, form_column = st.columns([1.02, 1.12], gap="large")
        with illustration:
            if has_asset("login.png"):
                login_img = f"<img src='{image_data_url('login.png')}' alt='Student learning at a laptop' style='width:100%;height:100%;object-fit:cover;display:block'/>"
            else:
                login_img = img_tag(unsplash_url("study", w=700, q=70), "Student learning at a laptop", "width:100%;height:100%;object-fit:cover;display:block")
            artwork = f"<div class='login-image-frame'>{login_img}<p class='auth-mantra'>Learn with focus.<br/>Grow with confidence.<br/>Build your future.</p></div>"
            render_html(f"""
            <section class='auth-illustration'>
              <div class='auth-brand'><span class='brand-mark'>✦</span><span><b>AI Career Mentor</b><small>Your Future&nbsp; • &nbsp;Our Guidance</small></span></div>
              {artwork}
            </section>""")
        with form_column:
            render_html("""<div class='auth-form-heading'><span class='eyebrow'>YOUR CAREER SPACE</span><h1>Welcome back<span>!</span></h1><p>Log in to continue your personalized career journey with AI.</p></div>""")
            sign_in, create = st.tabs(["Log in", "Create account"])
        with form_column:
            with sign_in:
                with st.form("login_form"):
                    email = st.text_input("Email address", key="login_email", placeholder="you@example.com")
                    password = st.text_input("Password", type="password", key="login_password")
                    remember = st.checkbox("Remember me on this device")
                    submitted = st.form_submit_button("Sign in  →", type="primary", use_container_width=True)
                if submitted:
                    email = (email or "").strip().lower()
                    password = password or ""
                    try:
                        user = login(email, password)
                        if not user:
                            st.error("No matching account found. Create the account first or check your email and password.")
                        else:
                            load_user(user)
                            cookies["remembered_email"] = user["email"] if remember else ""
                            cookies.save()
                            st.rerun()
                    except Exception as error:
                        st.error(f"Login error: {error}")
            with create:
                with st.form("register_form"):
                    name = st.text_input("Your name", placeholder="Your name")
                    email = st.text_input("Email address", key="register_email", placeholder="you@example.com")
                    password = st.text_input("Password", type="password", key="register_password", help="Use at least 8 characters.")
                    confirm_password = st.text_input("Confirm password", type="password", key="confirm_password")
                    agreed = st.checkbox("I agree to the Terms of Service and Privacy Policy")
                    submitted = st.form_submit_button("Create account  →", type="primary", use_container_width=True)
                if submitted:
                    try:
                        if password != confirm_password: raise ValueError("Your passwords do not match.")
                        if not agreed: raise ValueError("Please agree to the Terms and Privacy Policy.")
                        user = register(email, name, password); load_user(user); st.rerun()
                    except ValueError as error: st.error(str(error))
                st.caption("Already have an account? Select **Log in** above.")

# Restore a deliberately remembered local account.
if not st.session_state.authenticated and cookies.get("remembered_email"):
    remembered = find_user(cookies["remembered_email"])
    if remembered: load_user(remembered)
if not st.session_state.authenticated:
    show_login()
    st.stop()
careers, projects, courses = load_json("careers.json"), load_json("projects.json"), load_json("courses.json")
skill_data = load_json("skills.json") or {"aliases": {}}
career = next((c for c in careers if c["id"] == st.session_state.career_id), None)
gap = analyze(career, st.session_state.current_skills) if career else None

PAGES = ["Dashboard", "Career Explorer", "Skill Gap Analysis", "Career Roadmap", "Project Recommendations", "Course Recommendations", "Resume ATS Analyzer", "AI Career Chatbot", "Profile", "Settings"]
PAGE_ICONS = {"Dashboard": "🏠", "Career Explorer": "🧭", "Skill Gap Analysis": "📊", "Career Roadmap": "🧬", "Project Recommendations": "💻", "Course Recommendations": "🎓", "Resume ATS Analyzer": "📄", "AI Career Chatbot": "🤖", "Profile": "👤", "Settings": "⚙️"}
with st.sidebar:
    render_html("""<div class='sidebar-brand'><span class='sidebar-orb'><i class='fa-solid fa-sparkles'></i></span><div><b>AI Career Mentor</b><small>Your Future&nbsp; • &nbsp;Our Guidance</small></div></div>""")
    page = st.radio("Navigate", PAGES, index=PAGES.index(st.session_state.page) if st.session_state.page in PAGES else 0,
                     format_func=lambda p: f"{PAGE_ICONS.get(p, '✦')}  {p}", label_visibility="collapsed", key="nav_radio")
    st.session_state.page = page
    if career: st.caption(f"Target: {career['name']}")
    st.divider()
    st.caption(f"Signed in as {st.session_state.name}")
    if st.button("Sign out", use_container_width=True):
        cookies["remembered_email"] = ""
        cookies.save()
        if st.session_state.get("auth_provider") == "google" and hasattr(st, "logout"):
            st.logout()
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.auth_provider = None
        st.session_state.name = ""
        st.session_state.goal = ""
        st.session_state.career_id = None
        st.session_state.current_skills = []
        st.session_state.skill_status = {}
        st.session_state.ats = None
        st.session_state.chat = []
        st.session_state.avatar_path = None
        st.session_state.page = "Dashboard"
        st.session_state.pop("nav_radio", None)
        st.session_state.pop("global_search", None)
        st.rerun()


search_col, profile_col = st.columns([5, 2])
with search_col:
    query = st.text_input("Search", placeholder="Search careers, skills, courses...", label_visibility="collapsed", key="global_search")
    query = (query or "").strip().lower()
    if query:
        matched_careers = [c for c in careers if query in c['name'].lower() or query in c['description'].lower() or any(query in s.lower() for s in all_skills(c))]
        matched_courses = [c for c in courses if query in c['name'].lower() or query in c.get('platform', '').lower()]
        matched_projects = [p for p in projects if query in p['title'].lower() or any(query in s.lower() for s in p.get('skills', []))]
        total_hits = len(matched_careers) + len(matched_courses) + len(matched_projects)
        with st.container(border=True):
            if total_hits == 0:
                st.caption(f"🔍 No matches for “{query}”. Try a different keyword.")
            else:
                st.caption(f"🔍 {total_hits} result{'s' if total_hits != 1 else ''} for “{query}”")
                result_cols = st.columns(3)
                for c in matched_careers[:4]:
                    with result_cols[0]:
                        if st.button(f"🧭 {c['name']}", key=f"search_career_{c['id']}", use_container_width=True, help="Career path"):
                            choose(c)
                for c in matched_courses[:4]:
                    with result_cols[1]:
                        if st.button(f"🎓 {c['name']}", key=f"search_course_{c['name']}", use_container_width=True, help="Course"):
                            go("Course Recommendations")
                for p in matched_projects[:4]:
                    with result_cols[2]:
                        if st.button(f"💻 {p['title']}", key=f"search_project_{p['title']}", use_container_width=True, help="Project"):
                            go("Project Recommendations")
with profile_col:
    avatar_photo = st.session_state.avatar_path
    if avatar_photo and Path(avatar_photo).exists():
        try:
            b64_avatar = base64.b64encode(Path(avatar_photo).read_bytes()).decode("ascii")
            avatar_html = f"<span class='profile-avatar' style='background-image:url(data:image/png;base64,{b64_avatar})'></span>"
        except Exception:
            avatar_html = f"<span class='profile-avatar'>{(st.session_state.name or 'S')[0].upper()}</span>"
    else:
        avatar_html = f"<span class='profile-avatar'>{(st.session_state.name or 'S')[0].upper()}</span>"
    render_html(f"""<div class='top-profile'><span class='notification'><i class='fa-regular fa-bell'></i><b></b></span>{avatar_html}<span><strong>{st.session_state.name or 'Student'}</strong><small>Career learner</small></span></div>""")

def title(name, subtitle):
    icon = {"Dashboard":"fa-house", "Career Explorer":"fa-compass", "Skill Gap Analysis":"fa-chart-line", "Career Roadmap":"fa-map", "Project Recommendations":"fa-code", "Course Recommendations":"fa-graduation-cap", "Resume ATS Analyzer":"fa-file-lines", "AI Career Chatbot":"fa-robot", "Profile":"fa-user", "Settings":"fa-gear"}.get(name, "fa-sparkles")
    render_html(f"<div class='page-heading'><span><i class='fa-solid {icon}'></i></span><div><h1>{name}</h1><p>{subtitle}</p></div></div>")
def tech_badges(items):
    icons = {"Python":"fa-python", "React":"fa-react", "Node.js":"fa-node-js", "Git":"fa-git-alt", "Docker":"fa-docker", "GitHub":"fa-github", "JavaScript":"fa-js", "HTML":"fa-html5", "CSS":"fa-css3-alt", "Jupyter":"fa-python", "MongoDB":"fa-leaf"}
    markup = "".join(f"<span class='tech-badge'><i class='fa-brands {icons.get(item, 'fa-code')}'></i>{item}</span>" for item in items)
    render_html(f"<div class='tech-badges'>{markup}</div>")
def require_career():
    if not career:
        st.info("Choose a target career to unlock personalized guidance.")
        if st.button("Choose Your Career →"): go("Career Explorer")
        return True
    return False

if page == "Dashboard":
    title("Dashboard", "Your learning space, recommendations, and next milestone.")
    if not career:
        hero_copy, hero_image = st.columns([1.05, 1])
        with hero_copy: render_html("""<section class='career-hero'><div><span class='hero-chip'><i class='fa-solid fa-sparkles'></i> AI-powered career guidance</span><h2>Your career journey<br/>starts here.</h2><p>Explore career paths, discover your skills, and build the future you want with AI.</p></div></section>""")
        with hero_image:
            if has_asset("banner.png"): st.image(asset_path("banner.png"), use_container_width=True)
            else: photo_card("study", height=240, caption="Learn • Grow • Achieve")
        if st.button("Choose Your Career →", type="primary"): go("Career Explorer")
    else:
        completed = sum(v == "Completed" for v in st.session_state.skill_status.values())
        ring_col, m1, m2, m3 = st.columns([1.1, 1, 1, 1])
        with ring_col: progress_ring(gap['readiness'], "Career readiness", color="#3E0F8D")
        m1.metric("Target career", career['name']); m2.metric("Missing skills", len(gap['missing'])); m3.metric("Roadmap progress", f"{completed}/{len(all_skills(career))}")
        hero_copy, hero_image = st.columns([1.05, 1])
        with hero_copy: render_html("""<section class='career-hero compact'><div><span class='hero-chip'><i class='fa-solid fa-sparkles'></i> PERSONALIZED PATH</span><h2>Your career journey<br/>starts here.</h2><p>Keep building small skills today for bigger opportunities tomorrow.</p></div></section>""")
        with hero_image:
            if has_asset("banner.png"): st.image(asset_path("banner.png"), use_container_width=True)
            else: photo_card("study", height=200, caption="Small steps today, big dreams tomorrow")
        st.markdown("### Your next step")
        next_skill = gap['missing'][0] if gap['missing'] else "Build a portfolio project"
        st.info(f"**Learn {next_skill}**  \nIt is the next recommended step based on your skill gap.")
        if st.button("Continue Roadmap →", type="primary"): go("Career Roadmap")
        st.markdown("### Quick actions")
        actions = [("🧭 Explore Careers", "Career Explorer"), ("📊 Analyze Skill Gap", "Skill Gap Analysis"), ("📄 Analyze Resume", "Resume ATS Analyzer"), ("💻 Find Projects", "Project Recommendations"), ("🎓 Find Courses", "Course Recommendations"), ("🤖 Ask AI Mentor", "AI Career Chatbot")]
        for col, (label, dest) in zip(st.columns(3) * 2, actions):
            with col:
                if st.button(label, use_container_width=True): go(dest)

elif page == "Career Explorer":
    title("Career Explorer", "Find a career path that fits your interests.")
    query = st.text_input("Search careers", placeholder="Try AI, web, data…")
    categories = ["All"] + sorted({c['category'] for c in careers}); category = st.selectbox("Category", categories)
    filtered = [c for c in careers if (not query or query.lower() in (c['name'] + c['description']).lower()) and (category == "All" or c['category'] == category)]
    for c in filtered:
        with st.container(border=True):
            icon_col, a, b = st.columns([0.45, 3.55, 1])
            with icon_col:
                visual = get_visual(c['category'])
                render_html(f"<div style='background:{visual['color']};height:64px;width:64px;border-radius:14px;margin-top:.15rem;display:grid;place-items:center;box-shadow:0 6px 14px rgba(62,15,141,.18)'><i class='{visual['icon']}' style='font-size:1.5rem;color:#fff'></i></div>")
            a.subheader(c['name']); a.caption(c['category']); a.write(c['description'])
            a.write(" · ".join(all_skills(c)[:6]));
            if b.button("Choose this career", key=c['id']): choose(c)
            with st.expander("View full career details"):
                for level, skills in c['skills'].items(): st.write(f"**{level}:** " + ", ".join(skills))
                st.write("**Tools & technologies**"); tech_badges(c['tools'])
                st.write("**Prerequisites:** " + ", ".join(c['prerequisites'])); st.write("**Certifications:** " + ", ".join(c['certifications']))

elif page == "Skill Gap Analysis":
    title("Skill Gap Analysis", "Compare what you know with what your target role needs.")
    if not require_career():
        options = sorted(set(all_skills(career) + [s for c in careers for s in all_skills(c)]))
        selected = st.multiselect("Select your current skills", options, default=[s for s in st.session_state.current_skills if s in options], key="skillgap_current_skills")
        typed = st.text_input("Or add comma-separated skills", placeholder="Python, HTML, CSS")
        additions = [normalize_skill(x, skill_data.get('aliases', {})) for x in typed.split(',') if x.strip()]
        st.session_state.current_skills = list(dict.fromkeys(selected + additions))
        gap = analyze(career, st.session_state.current_skills)
        ring_col, m1, m2, m3, m4 = st.columns([1.1, 1, 1, 1, 1])
        with ring_col: progress_ring(gap['readiness'], "Career readiness", color="#3E0F8D")
        for col, label, value in zip((m1, m2, m3, m4), ["Required", "Acquired", "Matched", "Missing"], [len(gap['required']), len(st.session_state.current_skills), len(gap['matched']), len(gap['missing'])]): col.metric(label, value)
        chart_col, detail_col = st.columns([1, 2])
        with chart_col:
            st.caption("Skill breakdown")
            pie_chart(["Matched", "Missing", "Extra"], [len(gap['matched']), len(gap['missing']), len(gap['extra'])], ["#16A34A", "#DC2626", "#5B4DE6"])
        with detail_col:
            for level, skills in gap['levels'].items(): st.write(f"**{level} — needs improvement:** " + (", ".join(skills) or "All matched"))
            st.write("**✓ Matched:** " + (", ".join(gap['matched']) or "None yet")); st.write("**Extra skills:** " + (", ".join(gap['extra']) or "None"))
        if st.button("Build My Roadmap", type="primary"): go("Career Roadmap")

elif page == "Career Roadmap":
    title("Personalized Career Roadmap", "A practical sequence from fundamentals to job readiness.")
    if not require_career():
        stats_col, art_col = st.columns([2.3, 1])
        with stats_col:
            s1, s2, s3 = st.columns(3)
            s1.metric("Total steps", len(career['learning_path'])); s2.metric("Career readiness", f"{gap['readiness']}%"); s3.metric("Skills missing", len(gap['missing']))
        with art_col:
            if has_asset("mountains.png"): st.image(asset_path("mountains.png"), use_container_width=True)
            else: mini_mountain_card()
        STATUS_OPTIONS = ["Not Started", "In Progress", "Completed"]
        st.markdown("### Basic → advanced roadmap")
        with st.container():
            render_html(draw_snake_backdrop(len(career['learning_path'])))
            for i, skill in enumerate(career['learning_path'], 1):
                level = next((lvl for lvl, values in career['skills'].items() if skill in values), "Project")
                current = st.session_state.skill_status.get(skill, "Completed" if skill in gap['matched'] else "Not Started")
                node_class = "done" if current == "Completed" else ("progress" if current == "In Progress" else "")
                visual = get_visual(skill)
                pin_html = f"""
                <div class='step-node {node_class}' style='background:{"" if node_class else visual["color"]}'>
                  <i class='{visual["icon"]}'></i>
                  <span class='step-node-badge'>{'✓' if current == 'Completed' else i}</span>
                </div>"""
                is_left = (i - 1) % 2 == 0
                if is_left:
                    node_col, card_col = st.columns([0.14, 0.86])
                else:
                    card_col, node_col = st.columns([0.86, 0.14])
                with node_col:
                    render_html(pin_html)
                with card_col:
                    with st.container(border=True):
                        render_html(f"<span class='step-level'>{level}</span>")
                        status = st.selectbox(f"{i}. {skill}", STATUS_OPTIONS, index=STATUS_OPTIONS.index(current), key=f"status_{skill}")
                        st.session_state.skill_status[skill] = status
                        st.caption(f"Why: required for {career['name']}. Apply it in: {career['projects'][min(i-1, len(career['projects'])-1)]}.")
        graph = build_graph(career['learning_path']); start = st.selectbox("Starting skill", career['learning_path']); target = st.selectbox("Target skill", career['learning_path'], index=len(career['learning_path'])-1)
        paths = {"BFS": bfs(graph,start,target), "DFS": dfs(graph,start,target), "A*": astar(graph,start,target)}
        st.markdown("### AI skill-path demonstration")
        edges = graph_edges_from(graph, career['learning_path'])
        algo_tabs = st.tabs(list(paths.keys()))
        for tab, (name, path) in zip(algo_tabs, paths.items()):
            with tab:
                color = ALGO_COLORS.get(name, "#5B4DE6")
                path = path or []
                total = len(path)
                steps = total - 1 if total else 0
                summary = " → ".join(path) if path else "No forward dependency path"
                render_html(f"""
                <div class='section-hero' style='margin-bottom:.6rem'>
                  <span class='section-hero-icon' style='background:{color}'><i class='fa-solid fa-diagram-project'></i></span>
                  <div><h3>{name} traversal — {steps} step{'s' if steps != 1 else ''}</h3><p>{summary}</p></div>
                </div>""")
                reveal_key = f"algo_reveal_{name}_{career['id']}"
                if reveal_key not in st.session_state or st.session_state.get(f"{reveal_key}_path") != path:
                    st.session_state[reveal_key] = 0
                    st.session_state[f"{reveal_key}_path"] = path
                reveal = min(st.session_state[reveal_key], total)
                restart_col, prev_col, next_col, status_col = st.columns([1, 1, 1.2, 3])
                with restart_col:
                    if st.button("⟲ Restart", key=f"restart_{name}", use_container_width=True, disabled=total == 0):
                        st.session_state[reveal_key] = 0; st.rerun()
                with prev_col:
                    if st.button("◀ Prev", key=f"prev_{name}", use_container_width=True, disabled=reveal <= 0):
                        st.session_state[reveal_key] = max(0, reveal - 1); st.rerun()
                with next_col:
                    if st.button("Next ▶", key=f"next_{name}", type="primary", use_container_width=True, disabled=reveal >= total):
                        st.session_state[reveal_key] = min(total, reveal + 1); st.rerun()
                with status_col:
                    if total == 0:
                        st.caption("No traversal to animate for this start/target pair.")
                    elif reveal == 0:
                        st.caption("Click **Next ▶** to animate the traversal, one node at a time.")
                    else:
                        st.caption(f"Step {reveal} of {total} — highlighting **{path[reveal-1]}**")
                render_html(f"<div class='graph-card'>{draw_algo_graph(career['learning_path'], edges, path, color, reveal=reveal)}</div>")
                render_html(algo_output_list(path, reveal=reveal))
        ranked_projects = rank(projects, career['name'], gap['missing'], "project"); ranked_courses = rank(courses, career['name'], gap['missing'], "course")
        try:
            pdf = create_report(st.session_state.name, career, st.session_state.current_skills, gap, paths, ranked_projects, ranked_courses, st.session_state.ats)
            st.download_button("Download Roadmap PDF", pdf, "career_guidance_report.pdf", "application/pdf")
        except Exception as error: st.warning(f"PDF report is unavailable: {error}")

elif page in ("Project Recommendations", "Course Recommendations"):
    is_project = page.startswith("Project"); title(page, "Explainable recommendations based on your skill gap.")
    if not require_career():
        if is_project: section_hero("fa-code", "Hands-on projects", "Build real things that prove the skills on your resume.")
        else: section_hero("fa-graduation-cap", "Curated courses", "Structured lessons picked to close your specific skill gaps.")
        difficulty = st.selectbox("Difficulty", ["All", "Beginner", "Intermediate", "Advanced"])
        pricing = st.selectbox("Price", ["All", "Free", "Paid"]) if not is_project else "All"
        items = rank(projects if is_project else courses, career['name'], gap['missing'], "project" if is_project else "course")
        filtered_items = []
        for item in items:
            level = item.get('difficulty', item.get('level'))
            if difficulty != "All" and level != difficulty: continue
            if pricing != "All" and item.get('pricing') != pricing: continue
            filtered_items.append((item, level))
        if not filtered_items:
            st.info("No items match these filters yet — try widening Difficulty or Price.")
        columns_per_row = 3
        for row_start in range(0, len(filtered_items), columns_per_row):
            row = filtered_items[row_start:row_start + columns_per_row]
            cols = st.columns(columns_per_row)
            for col, (item, level) in zip(cols, row):
                with col:
                    with st.container(border=True):
                        name = item['title'] if is_project else item['name']
                        meta = f"{level} · {item.get('category', item.get('platform'))}"
                        badge = item.get('pricing') if not is_project else level
                        reco_card(name, meta, item['description'], item['why'], badge=badge)
                        if is_project:
                            st.caption("Skills: " + ", ".join(item['skills'])); tech_badges(item['technologies'])
                        elif item.get('url'):
                            st.link_button("Open Course ↗", item['url'], use_container_width=True)

elif page == "Resume ATS Analyzer":
    title("Resume ATS Analyzer", "An ATS-style estimated score — not a commercial ATS result.")
    if not require_career():
        uploaded = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
        if uploaded and st.button("Analyze Resume", type="primary"):
            try:
                text = extract_text(uploaded)
                if not text.strip(): st.warning("This file does not contain readable text.")
                else: st.session_state.ats = analyze_resume(text, career)
            except Exception as error: st.error(str(error))
        if st.session_state.ats:
            result = st.session_state.ats
            ring_col, pie_col, text_col = st.columns([1, 1, 2])
            with ring_col: progress_ring(result['score'], "ATS score", color="#3E0F8D")
            with pie_col: pie_chart(["Matched", "Missing"], [len(result['matched']), len(result['missing'])], ["#16A34A", "#DC2626"])
            with text_col:
                st.write("**✓ Matched skills:** " + (", ".join(result['matched']) or "None")); st.write("**! Missing skills:** " + (", ".join(result['missing']) or "None")); st.write("**Detected sections:** " + (", ".join(result['sections']) or "None"))
            st.markdown("#### Recommendations")
            for suggestion in result['suggestions']:
                st.write("- " + suggestion)

elif page == "AI Career Chatbot":
    title("AI Career Mentor", "Ask grounded questions about your selected career path.")
    if not require_career():
        for role, text in st.session_state.chat: st.chat_message(role).write(text)
        if question := st.chat_input("What should I learn first?"):
            st.session_state.chat.append(("user", question)); st.session_state.chat.append(("assistant", reply(question, career, gap, st.session_state.ats))); st.rerun()

elif page == "Profile":
    title("Your Profile", "Keep your learning plan personal and current.")
    photo_col, details_col = st.columns([1, 4])
    with photo_col:
        if st.session_state.avatar_path and Path(st.session_state.avatar_path).exists():
            st.image(st.session_state.avatar_path, width=105)
        elif has_asset("profile (2).png"):
            st.image(asset_path("profile (2).png"), width=105)
        else:
            fallback_avatar(st.session_state.name)
    with details_col:
        photo = st.file_uploader("Profile photo", type=["png", "jpg", "jpeg", "webp"], help="Upload a clear profile photo. It is saved only for your account on this app.")
        if photo:
            destination_dir = ROOT / "data" / "profile_images"; destination_dir.mkdir(parents=True, exist_ok=True)
            suffix = Path(photo.name).suffix.lower() or ".png"
            destination = destination_dir / f"user_{st.session_state.user_id}{suffix}"
            destination.write_bytes(photo.getvalue())
            st.session_state.avatar_path = str(destination)
            st.success("Profile photo updated.")
    st.session_state.name = st.text_input("Name", st.session_state.name); st.session_state.goal = st.text_area("Career goal", st.session_state.goal)
    selected_name = st.selectbox("Target career", ["Not selected"] + [c['name'] for c in careers], index=0 if not career else [c['name'] for c in careers].index(career['name']) + 1)
    if selected_name != "Not selected": st.session_state.career_id = next(c['id'] for c in careers if c['name'] == selected_name)
    if career:
        st.write(f"**Target career:** {career['name']}"); st.write(f"**Current skills:** {', '.join(st.session_state.current_skills) or 'Not added yet'}")
        rc1, rc2 = st.columns(2)
        with rc1: progress_ring(gap['readiness'], "Career readiness", color="#3E0F8D")
        with rc2: progress_ring(st.session_state.ats['score'] if st.session_state.ats else 0, "ATS score", color="#9564DD")

elif page == "Settings":
    title("Settings", "Control your session preferences.")
    st.caption("Your profile is stored only for this browser session.")
    default = st.selectbox("Default career for this session", ["None"] + [c['name'] for c in careers], index=0 if not career else [c['name'] for c in careers].index(career['name']) + 1)
    if default != "None": st.session_state.career_id = next(c['id'] for c in careers if c['name'] == default)
    confirm = st.checkbox("I understand this clears my profile, progress, and resume analysis.")
    if st.button("Clear current session data", disabled=not confirm):
        st.session_state.goal = ""
        st.session_state.career_id = None
        st.session_state.current_skills = []
        st.session_state.skill_status = {}
        st.session_state.ats = None
        st.session_state.chat = []
        st.session_state.page = "Dashboard"
        st.session_state.pop("nav_radio", None)
        st.rerun()


if st.session_state.get("authenticated") and st.session_state.get("user_id") is not None:
    save_profile(
        st.session_state.user_id,
        {key: st.session_state.get(key) for key in ("name", "goal", "career_id", "current_skills", "skill_status", "ats", "avatar_path")},
    )
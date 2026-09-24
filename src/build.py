"""Static site generator for gheslan.github.io.

Reads the content files in content/*.toml and writes the HTML pages
(English at the root, French under fr/), plus sitemap.xml and robots.txt.

Usage:   python src/build.py
Requires Python 3.11+ (standard library only).
"""
import html
import json
import math
import os
import re
import tomllib

from figures import FIGURES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ("en", "fr")


def load(name):
    with open(os.path.join(ROOT, "content", name), "rb") as f:
        return tomllib.load(f)


SITE = load("site.toml")
RESEARCH = load("research.toml")
CV = load("cv.toml")
TEACH = load("teaching.toml")
BASE = SITE["base_url"].rstrip("/") + "/"
WRITTEN = []  # (path relative to ROOT) of generated pages, for the sitemap


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def tr(v, lang):
    """Content value that may be a plain string or a {en, fr} table."""
    if isinstance(v, dict):
        return v.get(lang, "")
    return v if v is not None else ""


_BARE_AMP = re.compile(r"&(?!#?\w+;)")


def h(text):
    """Content is trusted HTML; only escape bare ampersands."""
    return _BARE_AMP.sub("&amp;", text or "")


def attr(text):
    return html.escape(re.sub(r"<[^>]+>", "", text or ""), quote=True)


MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
}


def month(date, lang):
    y, m = date.split("-")[:2]
    return f"{MONTHS[lang][int(m) - 1]} {y}"


UI = {
    "en": dict(
        nav=[("", "About"), ("research.html", "Research"), ("cv.html", "CV"), ("teaching.html", "Teaching")],
        skip="Skip to content", nav_aria="Main", menu="Menu", other="Version française", other_label="FR", locale="en_GB",
        interests="Interests", profiles="Profiles", research_h="Research", research_more="Abstracts and preliminary results",
        news_h="Recent",
        r_title="Research — Guewen Heslan", r_desc="Working papers and presentations of Guewen Heslan on trade, environmental policy and maritime transport.",
        r_h1="Research", r_lead="Papers in preparation. The results summarised below are preliminary and may change; drafts are not yet circulated.",
        wp_h="Working papers", findings="Preliminary results", note="Preliminary results, subject to change.",
        wip_h="Work in progress", talks_h="Conferences and presentations",
        map_aria="Map of the cities where I presented my work", map_note="Circle size reflects the number of presentations. Lines start from Nantes (LEMNA).",
        talk_one="presentation", talk_many="presentations",
        cv_title="CV — Guewen Heslan", cv_desc="Curriculum vitae of Guewen Heslan.", cv_h1="Curriculum vitae",
        edu_h="Education", teach_h="Teaching", emp_h="Employment", award_h="Awards", skills_h="Skills", print="Print / save as PDF",
        t_title="Teaching — Guewen Heslan", t_desc="Courses taught by Guewen Heslan.", t_h1="Teaching",
        t_lead2="Course materials are posted on each course page.", cur_h="Current courses", prev_h="Previous courses",
        soon="Materials coming soon", n_materials="documents", open_course="Course page",
        c_back="All courses", c_about="About the course", c_info="Practical information", c_materials="Materials",
        c_empty="Materials will be posted here during the semester.",
        kinds=dict(slides="Slides", exercises="Exercises", solutions="Solutions", exam="Exam", reading="Reading", other="Document"),
        stats_note="This site uses GoatCounter, a cookie-free and privacy-friendly visitor counter.",
        nf_title="Page not found", nf_text="This page does not exist or has moved.", home="Home",
    ),
    "fr": dict(
        nav=[("", "Présentation"), ("research.html", "Recherche"), ("cv.html", "CV"), ("teaching.html", "Enseignement")],
        skip="Aller au contenu", nav_aria="Navigation principale", menu="Menu", other="English version", other_label="EN", locale="fr_FR",
        interests="Thèmes", profiles="Profils", research_h="Recherche", research_more="Résumés et résultats préliminaires",
        news_h="Actualités",
        r_title="Recherche — Guewen Heslan", r_desc="Documents de travail et communications de Guewen Heslan sur le commerce, la politique environnementale et le transport maritime.",
        r_h1="Recherche", r_lead="Articles en préparation. Les résultats présentés ci-dessous sont préliminaires et susceptibles d’évoluer ; les versions de travail ne sont pas encore diffusées.",
        wp_h="Documents de travail", findings="Résultats préliminaires", note="Résultats préliminaires, susceptibles d’évoluer.",
        wip_h="Travaux en cours", talks_h="Conférences et communications",
        map_aria="Carte des villes où j’ai présenté mes travaux", map_note="La taille des cercles reflète le nombre de présentations. Les lignes partent de Nantes (LEMNA).",
        talk_one="présentation", talk_many="présentations",
        cv_title="CV — Guewen Heslan", cv_desc="Curriculum vitae de Guewen Heslan.", cv_h1="Curriculum vitae",
        edu_h="Formation", teach_h="Enseignement", emp_h="Expérience professionnelle", award_h="Distinctions", skills_h="Compétences", print="Imprimer / enregistrer en PDF",
        t_title="Enseignement — Guewen Heslan", t_desc="Cours enseignés par Guewen Heslan.", t_h1="Enseignement",
        t_lead2="Les supports sont disponibles sur la page de chaque cours.", cur_h="Cours actuels", prev_h="Cours précédents",
        soon="Supports bientôt disponibles", n_materials="documents", open_course="Page du cours",
        c_back="Tous les cours", c_about="Présentation du cours", c_info="Informations pratiques", c_materials="Supports",
        c_empty="Les supports seront publiés ici au fil du semestre.",
        kinds=dict(slides="Diapositives", exercises="Exercices", solutions="Corrigés", exam="Examen", reading="Lecture", other="Document"),
        stats_note="Ce site utilise GoatCounter, un compteur de visites sans cookies et respectueux de la vie privée.",
        nf_title="Page introuvable", nf_text="Cette page n’existe pas ou a été déplacée.", home="Accueil",
    ),
}

FONTS = "https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Crimson+Pro:ital,wght@0,400;0,500;1,400&display=swap"
CHEVRON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>'
ICONS = {
    "math": '<path d="M17 5H7l6 7-6 7h10"/>',
    "macro": '<path d="M3 17l5-5 4 3 8-8"/><path d="M15 7h5v5"/>',
    "stats": '<path d="M3 20h18"/><path d="M6 20v-7M12 20V5M18 20v-10"/>',
    "env": '<path d="M5 19c0-8 6-14 15-14 0 9-6 15-14 15z"/><path d="M5 19l7-7"/>',
    "energy": '<path d="M13 3 5 14h6l-1 7 8-11h-6z"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
}
LOGOS = [
    ("Paris Cité", "paris-cite.svg", "Université Paris Cité"),
    ("Nantes Université", "nantes-universite.png", "Nantes Université"),
    ("IMT Atlantique", "imt-atlantique.svg", "IMT Atlantique"),
]


def icon(k):
    return (f'<span class="course-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS[k]}</svg></span>')


def logos_for(org, root):
    imgs = [f'<span class="logo"><img src="{root}assets/img/logos/{f}" alt="{alt}" loading="lazy" decoding="async"></span>'
            for key, f, alt in LOGOS if key in (org or "")]
    return f'<span class="logos">{"".join(imgs)}</span>' if imgs else ""


# ---------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------
def page(lang, rel, title, desc, body, jsonld=None, noindex=False):
    """rel: path of the page relative to the language root, e.g. 'cv.html' or 'teaching/statistics.html'."""
    u = UI[lang]
    depth = rel.count("/") + (1 if lang == "fr" else 0)
    root = "../" * depth                      # to the site root
    lroot = root + ("fr/" if lang == "fr" else "")  # to the language root
    other_root = root + ("" if lang == "fr" else "fr/")
    page_url = rel if not rel.endswith("index.html") else rel[: -len("index.html")]
    url_en = BASE + page_url
    url_fr = BASE + "fr/" + page_url
    canonical = url_fr if lang == "fr" else url_en
    section = rel.split("/")[0] if "/" in rel else rel
    if section == "teaching":
        section = "teaching.html"
    nav_items = []
    for n, (href, label) in enumerate(u["nav"]):
        target = (lroot + href) if href else (lroot or "./")
        current = ' aria-current="page"' if (href or "index.html") == section else ""
        nav_items.append(f'        <li style="--n:{n}"><a href="{target}"{current}>{label}</a></li>')
    nav = "\n".join(nav_items)
    og_img = BASE + "assets/img/og-image.png"
    ld = f'\n  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    robots = '\n  <meta name="robots" content="noindex">' if noindex else ""
    stats = ""
    if SITE.get("goatcounter"):
        stats = (f'\n  <script data-goatcounter="https://{SITE["goatcounter"]}.goatcounter.com/count" '
                 f'async src="//gc.zgo.at/count.js"></script>')
    footer_stats = f'\n      <p class="stats-note">{u["stats_note"]}</p>' if SITE.get("goatcounter") else ""
    out = f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{attr(desc)}">{robots}
  <link rel="canonical" href="{canonical}">
  <link rel="alternate" hreflang="en" href="{url_en}">
  <link rel="alternate" hreflang="fr" href="{url_fr}">
  <link rel="alternate" hreflang="x-default" href="{url_en}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{SITE['name']}">
  <meta property="og:title" content="{attr(title)}">
  <meta property="og:description" content="{attr(desc)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og_img}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:locale" content="{u['locale']}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#ffffff">
  <link rel="icon" href="{root}assets/img/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="{FONTS}" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="{FONTS}"></noscript>
  <script>document.documentElement.classList.add("js");</script>
  <link rel="stylesheet" href="{root}assets/css/style.css">{ld}{stats}
</head>
<body>
  <a class="skip-link" href="#main">{u['skip']}</a>

  <header class="site-header">
    <nav class="container nav" aria-label="{u['nav_aria']}">
      <a class="brand" href="{lroot or './'}">{SITE['name']}</a>
      <ul class="nav-links" id="nav-links">
{nav}
        <li class="nav-lang-mobile" style="--n:4"><a href="{other_root}{rel if not rel.endswith('index.html') else ''}" hreflang="{'en' if lang == 'fr' else 'fr'}">{u['other']}</a></li>
      </ul>
      <div class="nav-actions">
        <a class="lang-switch" href="{other_root}{rel if not rel.endswith('index.html') else ''}" hreflang="{'en' if lang == 'fr' else 'fr'}" lang="{'en' if lang == 'fr' else 'fr'}" aria-label="{u['other']}">{u['other_label']}</a>
        <button class="icon-btn menu-toggle" type="button" aria-label="{u['menu']}" aria-expanded="false" aria-controls="nav-links">
          <span class="burger" aria-hidden="true"><span></span><span></span><span></span></span>
        </button>
      </div>
    </nav>
  </header>

  <main id="main" class="container">
{body.strip(chr(10))}
  </main>

  <footer class="site-footer">
    <div class="container">
      <span>© <span id="year">2026</span> {SITE['name']}</span>
      <a href="mailto:{SITE['contact']['emails'][0]['address']}">{SITE['contact']['emails'][0]['address']}</a>{footer_stats}
    </div>
  </footer>

  <script src="{root}assets/js/main.js" defer></script>
</body>
</html>
"""
    out = out.replace('href=""', 'href="./"')
    path = os.path.join(ROOT, *(["fr"] if lang == "fr" else []), *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    if lang == "en" and not noindex:
        WRITTEN.append(rel)


# ---------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------
def entry(when, title, org=None, desc=None, bullets=None, talk=False, extra_attr=""):
    parts = [f'      <span class="when">{when}</span>', "      <div>"]
    if talk:
        parts.append(f'        <h3 class="talk-title" lang="en">{h(title)}</h3>')
    elif title:
        parts.append(f"        <h3>{h(title)}</h3>")
    if org:
        parts.append(f'        <p class="org">{h(org)}</p>')
    if desc:
        parts.append(f'        <p class="desc">{h(desc)}</p>')
    if bullets:
        parts.append("        <ul>" + "".join(f"<li>{h(b)}</li>" for b in bullets) + "</ul>")
    parts.append("      </div>")
    return f"    <li{extra_attr}>\n" + "\n".join(parts) + "\n    </li>"


def section(title, inner, cls="entries", extra=""):
    return f"""
  <section class="section reveal"{extra}>
    <h2>{title}</h2>
    <ol class="{cls}">
{inner}
    </ol>
  </section>"""


def iso_lines():
    lines = []
    for i in range(7):
        y = 40 + i * 52
        a = 10 + (i % 3) * 5
        d = f"M0 {y} Q150 {y - a} 300 {y} " + " ".join(f"T{x} {y}" for x in range(600, 2401, 300))
        cls = ' class="warm"' if i == 2 else ""
        lines.append(f'      <g style="--dur:{55 + i * 14}s"><path{cls} d="{d}"/></g>')
    return ('    <svg class="isolines" viewBox="0 0 1200 420" preserveAspectRatio="none" aria-hidden="true" focusable="false">\n'
            + "\n".join(lines) + "\n    </svg>")


def link_name(l, lang):
    return tr(l["name"], lang)


# ---------------------------------------------------------------------
# Conference map
# ---------------------------------------------------------------------
BASEMAP = json.load(open(os.path.join(ROOT, "src", "data", "basemap.json"), encoding="utf-8"))


def project(lon, lat):
    b = BASEMAP
    x = (lon - b["lon0"]) / (b["lon1"] - b["lon0"]) * b["width"]
    y = (b["lat1"] - lat) / (b["lat1"] - b["lat0"]) * b["height"]
    return x, y


def write_basemap_svg():
    b = BASEMAP
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {b["width"]:.0f} {b["height"]:.0f}">'
           f'<path d="{b["d"]}" fill="#e9ecef" stroke="#ffffff" stroke-width="0.8" stroke-linejoin="round"/></svg>')
    with open(os.path.join(ROOT, "assets", "img", "conference-basemap.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)


def conference_map(lang, root):
    u = UI[lang]
    locs = RESEARCH["locations"]
    groups = {}
    for t in RESEARCH["talks"]:
        groups.setdefault(t["location"], []).append(t)
    # crop window (degrees) around the talks
    x0, y0 = project(-11.5, 62.2)
    x1, y1 = project(31.5, 32.0)
    vb = f"{x0:.0f} {y0:.0f} {x1 - x0:.0f} {y1 - y0:.0f}"
    home = "nantes"
    hx, hy = project(locs[home]["lon"], locs[home]["lat"])
    arcs, markers, data = [], [], {}
    for n, (key, talks) in enumerate(sorted(groups.items(), key=lambda kv: -locs[kv[0]]["lat"])):
        loc = locs[key]
        x, y = project(loc["lon"], loc["lat"])
        name = tr(loc["name"], lang)
        count = len(talks)
        r = 4.5 + 2.2 * (count - 1)
        if key != home:
            mx, my = (hx + x) / 2, (hy + y) / 2
            dx, dy = x - hx, y - hy
            length = math.hypot(dx, dy)
            nx, ny = -dy / length, dx / length
            if ny > 0:
                nx, ny = -nx, -ny
            cx, cy = mx + nx * length * 0.18, my + ny * length * 0.18
            arcs.append(f'<path class="map-arc draw" style="--d:{0.3 + n * 0.15:.2f}s" pathLength="1" d="M{hx:.1f} {hy:.1f} Q{cx:.1f} {cy:.1f} {x:.1f} {y:.1f}"/>')
        label_left = loc["lon"] > 20
        lx = x - r - 4 if label_left else x + r + 4
        anchor = "end" if label_left else "start"
        count_txt = f"{count} {u['talk_one'] if count == 1 else u['talk_many']}"
        markers.append(
            f'<g class="map-marker pop{" home" if key == home else ""}" style="--d:{0.5 + n * 0.12:.2f}s" data-loc="{key}" tabindex="0" role="button" '
            f'aria-label="{attr(name)} — {count_txt}">'
            f'<circle class="map-pulse" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>'
            f'<circle class="map-dot" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>'
            f'<text class="map-label" x="{lx:.1f}" y="{y + 4:.1f}" text-anchor="{anchor}">{name}</text></g>')
        data[key] = {"name": name, "count": count_txt,
                     "items": [{"date": month(t["date"], lang), "title": t["title"], "venue": re.sub(r"<[^>]+>", "", tr(t["venue"], lang))} for t in talks]}
    return f"""    <figure class="figure conf-map reveal">
      <div class="map-wrap">
        <svg viewBox="{vb}" style="max-width: {540 * (x1 - x0) / (y1 - y0):.0f}px" role="img" aria-label="{u['map_aria']}">
          <image href="{root}assets/img/conference-basemap.svg" x="0" y="0" width="{BASEMAP['width']:.0f}" height="{BASEMAP['height']:.0f}"/>
          {"".join(arcs)}
          {"".join(markers)}
        </svg>
        <div class="map-tip" role="status" aria-live="polite" hidden></div>
      </div>
      <figcaption>{u['map_note']}</figcaption>
      <script type="application/json" class="map-data">{json.dumps(data, ensure_ascii=False)}</script>
    </figure>"""


# ---------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------
def build_home(lang):
    u, hm = UI[lang], SITE["home"]
    positions = "\n".join(f"      <li>{h(p)}</li>" for p in hm["positions"][lang])
    emails = "\n".join(f'      <li><a href="mailto:{e["address"]}">{e["address"]}</a></li>' for e in SITE["contact"]["emails"])
    profiles = " ".join(
        f'<li><a href="{l["url"]}" target="_blank" rel="noopener me">{link_name(l, lang)}</a></li>'
        for l in SITE["links"] if l.get("url"))
    plist = "\n".join(
        f'      <li><a href="research.html#{p["id"]}"><span><span class="title" lang="en">{h(p["title"])}</span>'
        + (f'<br><span class="meta">{h(tr(p["authors"], lang))}</span>' if p.get("authors") else "")
        + '</span><span class="arrow" aria-hidden="true">→</span></a></li>' for p in RESEARCH["papers"])
    news = "\n".join(entry(month(n["date"], lang), "", desc=tr(n["text"], lang)) for n in SITE["news"])
    body = f"""
  <section class="intro hero-in">
{iso_lines()}
    <h1>{SITE['name']}<span class="dot">.</span></h1>
    <ul class="positions">
{positions}
    </ul>
    <p class="lead">{h(hm['lead'][lang])}</p>
    <p>{h(hm['bio'][lang])}</p>
    <p class="muted"><strong>{u['interests']}:</strong> {", ".join(hm['interests'][lang])}.</p>
    <ul class="contact-line">
{emails}
    </ul>
    <ul class="profile-links" aria-label="{u['profiles']}">{profiles}</ul>
  </section>

  <section class="section reveal">
    <h2>{u['research_h']}</h2>
    <ul class="plain-list">
{plist}
    </ul>
    <a class="more" href="research.html">{u['research_more']} →</a>
  </section>
{section(u['news_h'], news)}
""".replace(f"<strong>{u['interests']}:</strong>", f"<strong>{u['interests']}{' ' if lang == 'fr' else ''}:</strong>")
    same_as = [l["url"] for l in SITE["links"] if l.get("url")]
    jsonld = {
        "@context": "https://schema.org", "@type": "Person", "name": SITE["name"], "url": BASE,
        "image": BASE + "assets/img/og-image.png",
        "jobTitle": "PhD candidate in Economics" if lang == "en" else "Doctorant en économie",
        "affiliation": [{"@type": "CollegeOrUniversity", "name": "Nantes Université", "department": {"@type": "Organization", "name": "LEMNA"}},
                        {"@type": "CollegeOrUniversity", "name": "Université Paris Cité"}],
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Université Paris Dauphine – PSL"},
                     {"@type": "CollegeOrUniversity", "name": "Université Paris-Saclay"},
                     {"@type": "CollegeOrUniversity", "name": "AgroParisTech"}],
        "email": "mailto:" + SITE["contact"]["emails"][0]["address"],
        "knowsAbout": hm["interests"]["en"] + ["EU ETS", "gravity models", "shipping decarbonization"],
        "award": "Marcel Boiteux Prize 2024 (FAEE)",
        "sameAs": same_as,
    }
    page(lang, "index.html", tr(hm["title"], lang), tr(hm["description"], lang), body, jsonld=jsonld)


def build_research(lang):
    u = UI[lang]
    root = "../" if lang == "fr" else ""
    items = []
    for p in RESEARCH["papers"]:
        fl = "\n".join(f"            <li>{h(x)}</li>" for x in p["findings"][lang])
        fig = FIGURES[p["figure"]](lang) if p.get("figure") in FIGURES else ""
        st = f'\n      <p class="status">{h(tr(p["status"], lang))}</p>' if p.get("status") else ""
        au = f'\n      <p class="authors">{h(tr(p["authors"], lang))}</p>' if p.get("authors") else ""
        items.append(f"""    <li class="reveal" id="{p['id']}">
      <h3 lang="en">{h(p['title'])}</h3>{au}{st}
      <p class="abstract">{h(p['abstract'][lang])}</p>
{fig}
      <details class="findings">
        <summary>{CHEVRON}{u['findings']}</summary>
        <div class="findings-body">
          <ul>
{fl}
          </ul>
          <p class="note">{u['note']}</p>
        </div>
      </details>
    </li>""")
    wip = "\n".join(f"""      <li>
        <h3 lang="en">{h(w['title'])}</h3>
        <p class="authors">{h(tr(w.get('authors'), lang))}</p>
      </li>""" for w in RESEARCH.get("work_in_progress", []))
    talks = "\n".join(entry(month(t["date"], lang), t["title"], org=tr(t["venue"], lang), talk=True,
                            extra_attr=f' data-loc="{t["location"]}"') for t in RESEARCH["talks"])
    body = f"""
  <header class="hero-in">
    <h1 class="page-title">{u['r_h1']}</h1>
    <p class="page-lead">{u['r_lead']}</p>
  </header>

  <section class="section">
    <h2 class="reveal">{u['wp_h']}</h2>
    <ol class="papers">
{chr(10).join(items)}
    </ol>
  </section>

  <section class="section reveal">
    <h2>{u['wip_h']}</h2>
    <ul class="papers">
{wip}
    </ul>
  </section>

  <section class="section" id="talks">
    <h2 class="reveal">{u['talks_h']}</h2>
{conference_map(lang, root)}
    <ol class="entries talks reveal">
{talks}
    </ol>
  </section>
"""
    page(lang, "research.html", u["r_title"], u["r_desc"], body)


def build_cv(lang):
    u = UI[lang]

    def entries(key, with_bullets=False):
        out = []
        for e in CV.get(key, []):
            out.append(entry(tr(e["when"], lang), tr(e["title"], lang), org=tr(e.get("org"), lang),
                             desc=tr(e.get("desc"), lang) or None,
                             bullets=e["bullets"][lang] if with_bullets and e.get("bullets") else None))
        return "\n".join(out)

    skills = "\n".join(f"      <div><dt>{tr(s['label'], lang)}</dt><dd>{h(tr(s['value'], lang))}</dd></div>" for s in CV["skills"])
    body = f"""
  <header class="hero-in page-head">
    <div>
      <h1 class="page-title">{u['cv_h1']}</h1>
      <p class="page-lead">{h(tr(CV['lead'], lang))}</p>
    </div>
    <button class="print-btn" type="button" data-print>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 14h12v7H6z"/></svg>
      {u['print']}
    </button>
  </header>
  <p class="print-only print-contact">{SITE['name']} · {" · ".join(e["address"] for e in SITE["contact"]["emails"])} · {BASE}</p>
{section(u['edu_h'], entries('education', True))}
{section(u['teach_h'], entries('teaching'))}
{section(u['emp_h'], entries('employment'))}
{section(u['award_h'], entries('awards'))}

  <section class="section reveal">
    <h2>{u['skills_h']}</h2>
    <dl class="skills">
{skills}
    </dl>
  </section>
"""
    page(lang, "cv.html", u["cv_title"], u["cv_desc"], body)


def material_count(c):
    return len(c.get("materials", []))


def build_teaching(lang):
    u = UI[lang]
    root = "../" if lang == "fr" else ""
    cards = []
    for n, c in enumerate(TEACH["courses"]):
        k = material_count(c)
        status = f'{k} {u["n_materials"]}' if k else u["soon"]
        cards.append(f"""      <li class="course reveal" style="--i:{n}">
        <a class="course-link" href="teaching/{c['slug']}.html">
          {icon(c['icon'])}
          <h3>{h(tr(c['name'], lang))}</h3>
          <p class="course-meta">{h(tr(c['level'], lang))} · {h(tr(c['format'], lang))}</p>
          <p class="course-soon">{status}<span class="course-go" aria-hidden="true">→</span></p>
        </a>
      </li>""")
    prev = "\n".join(f"""      <li class="course row reveal" style="--i:{n}">
        {logos_for(p['org'], root)}
        <div>
          <h3>{h(tr(p['name'], lang))}</h3>
          <p class="course-meta">{h(tr(p['audience'], lang))}</p>
        </div>
        <p class="course-when"><strong>{h(p['org'])}</strong><span>{p['years']}</span></p>
      </li>""" for n, p in enumerate(TEACH["previous"]))
    body = f"""
  <header class="hero-in">
    <h1 class="page-title">{u['t_h1']}</h1>
    <p class="page-lead">{(h(tr(TEACH.get('lead'), lang)) + ' ' if tr(TEACH.get('lead'), lang) else '') + u['t_lead2']}</p>
  </header>

  <section class="section">
    <h2 class="reveal">{u['cur_h']}</h2>
    <p class="section-sub with-logo reveal">{logos_for(TEACH['current_institution'], root)}<span>{TEACH['current_institution']} · {TEACH['current_year']}</span></p>
    <ul class="course-grid">
{chr(10).join(cards)}
    </ul>
  </section>

  <section class="section">
    <h2 class="reveal">{u['prev_h']}</h2>
    <ul class="course-list">
{prev}
    </ul>
  </section>
"""
    page(lang, "teaching.html", u["t_title"], u["t_desc"], body)

    # One page per current course
    for c in TEACH["courses"]:
        name = tr(c["name"], lang)
        croot = root + "../"
        mats = c.get("materials", [])
        if mats:
            rows = "\n".join(f"""      <li>
        <a href="{croot}{m['file']}" download>
          <span class="mat-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS['file']}</svg></span>
          <span class="mat-title">{h(tr(m['title'], lang))}</span>
          <span class="mat-meta">{u['kinds'].get(m.get('kind', 'other'), u['kinds']['other'])}{' · ' + month(m['date'], lang) if m.get('date') else ''}</span>
        </a>
      </li>""" for m in mats)
            materials = f'    <ul class="materials">\n{rows}\n    </ul>'
        else:
            materials = f'    <p class="empty-state">{u["c_empty"]}</p>'
        about = tr(c.get("description"), lang)
        info = tr(c.get("info"), lang)
        body = f"""
  <nav class="crumbs hero-in" aria-label="breadcrumb"><a href="../teaching.html">← {u['c_back']}</a></nav>
  <header class="hero-in course-head">
    {icon(c['icon'])}
    <div>
      <h1 class="page-title">{h(name)}</h1>
      <p class="page-lead">{TEACH['current_institution']} · {h(tr(c['level'], lang))} · {h(tr(c['format'], lang))} · {TEACH['current_year']}</p>
    </div>
  </header>
{f'''
  <section class="section reveal">
    <h2>{u['c_about']}</h2>
    <p>{h(about)}</p>
  </section>''' if about else ''}
{f'''
  <section class="section reveal">
    <h2>{u['c_info']}</h2>
    <p>{h(info)}</p>
  </section>''' if info else ''}

  <section class="section reveal">
    <h2>{u['c_materials']}</h2>
{materials}
  </section>
"""
        page(lang, f"teaching/{c['slug']}.html", f"{name} — {SITE['name']}", f"{name}: {tr(c['level'], lang)}, {TEACH['current_institution']}.", body)


def build_404():
    u = UI["en"]
    body = f"""
  <section class="notfound">
    <h1 class="page-title">{u['nf_title']}</h1>
    <p class="page-lead">{u['nf_text']} <span lang="fr">{UI['fr']['nf_text']}</span></p>
    <p><a href="/">{u['home']}</a> · <a href="/fr/" lang="fr">{UI['fr']['home']}</a></p>
  </section>
"""
    page("en", "404.html", f"{u['nf_title']} — {SITE['name']}", u["nf_text"], body, noindex=True)
    # 404 is served from any path: use absolute asset URLs
    p = os.path.join(ROOT, "404.html")
    s = open(p, encoding="utf-8").read()
    s = s.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/')
    s = s.replace('href="research.html"', 'href="/research.html"').replace('href="cv.html"', 'href="/cv.html"')
    s = s.replace('href="teaching.html"', 'href="/teaching.html"').replace('href="fr/', 'href="/fr/').replace('href="./"', 'href="/"')
    open(p, "w", encoding="utf-8", newline="\n").write(s)


def build_sitemap():
    urls = []
    for rel in WRITTEN:
        page_url = rel if not rel.endswith("index.html") else rel[: -len("index.html")]
        for lang in LANGS:
            loc = BASE + ("fr/" if lang == "fr" else "") + page_url
            urls.append(f"""  <url>
    <loc>{loc}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{BASE + page_url}"/>
    <xhtml:link rel="alternate" hreflang="fr" href="{BASE + 'fr/' + page_url}"/>
  </url>""")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n")


def main():
    write_basemap_svg()
    for lang in LANGS:
        build_home(lang)
        build_research(lang)
        build_cv(lang)
        build_teaching(lang)
    build_404()
    build_sitemap()
    print(f"Built {len(WRITTEN)} pages × {len(LANGS)} languages, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()

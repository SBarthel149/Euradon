"""Baut die EURADON-Website als statische Seiten nach dist/.

Aufruf:  python3 build.py            (Vorschau mit Entwurfs-Hinweis)
         python3 build.py --live     (ohne Entwurfs-Hinweis, für die Veröffentlichung)
"""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

HERE = Path(__file__).parent
DIST = HERE / "dist"

LAENDER = {"DE": "Deutschland", "AT": "Österreich", "CZ": "Tschechien"}
NAV = [
    {"key": "radon", "label": "Radontherapie", "href": "radontherapie/index.html"},
    {"key": "baeder", "label": "Heilbäder", "href": "heilbaeder/index.html"},
    {"key": "fach", "label": "Für Fachkreise", "href": "fachkreise/index.html"},
    {"key": "verein", "label": "Verein", "href": "verein/index.html"},
    {"key": "kontakt", "label": "Kontakt", "href": "kontakt.html"},
]

# (Vorlage, Zielpfad, Bereich, Titel, Beschreibung)
PAGES = [
    ("index.html", "index.html", "", "EURADON", "Verein Europäische Radonheilbäder: Informationen zu Radon, zur Radonkur und zu den Mitgliedsbädern in Deutschland, Österreich und Tschechien."),
    ("radontherapie.html", "radontherapie/index.html", "radon", "Radon und Radonkur", "Was Radon ist, wie eine Radonkur abläuft und für wen sie nicht geeignet ist."),
    ("sicherheit.html", "radontherapie/sicherheit.html", "radon", "Sicherheit und Strahlung", "Radon ist radioaktiv: was das für eine Radonkur bedeutet."),
    ("fragen.html", "radontherapie/fragen.html", "radon", "Häufige Fragen", "Kurze Antworten auf häufige Fragen zu Radon und Radonkur."),
    ("heilbaeder.html", "heilbaeder/index.html", "baeder", "Heilbäder", "Die Mitglieder von EURADON in Deutschland, Österreich und Tschechien."),
    ("fachkreise.html", "fachkreise/index.html", "fach", "Für Fachkreise", "Studien, Vorträge und Literatur zur Radonbalneologie."),
    ("verein.html", "verein/index.html", "verein", "Über uns", "Aufgaben und Geschichte des Vereins EURADON."),
    ("tagungen.html", "verein/tagungen.html", "verein", "Tagungen", "Herbsttagung 2026 und Rückblick auf frühere Tagungen."),
    ("mitglied.html", "verein/mitglied-werden.html", "verein", "Mitglied werden", "Mitgliedschaft im Verein Europäische Radonheilbäder."),
    ("kontakt.html", "kontakt.html", "kontakt", "Kontakt", "Kontakt zur Geschäftsstelle von EURADON."),
    ("impressum.html", "impressum.html", "", "Impressum", "Impressum des Vereins EURADON."),
    ("datenschutz.html", "datenschutz.html", "", "Datenschutz", "Datenschutzhinweise des Vereins EURADON."),
]


def main():
    draft = "--live" not in sys.argv
    logo = json.loads((HERE / "content/logo.json").read_text(encoding="utf-8"))
    orte = json.loads((HERE / "content/mitglieder.json").read_text(encoding="utf-8"))["orte"]

    env = Environment(loader=FileSystemLoader(HERE / "templates"), undefined=StrictUndefined, autoescape=True)
    base = {"logo": logo, "nav": NAV, "laender": LAENDER, "orte": orte, "draft": draft, "year": date.today().year}

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(HERE / "static", DIST)
    (DIST / "img/favicon.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -10 {logo["SW"] + 60} {logo["H"] + 20}">'
        f'<rect x="-30" y="-10" width="{logo["SW"] + 60}" height="{logo["H"] + 20}" rx="24" fill="#faf8f3"/>'
        f'{logo["sym"].replace("currentColor", "#0f6b66")}</svg>',
        encoding="utf-8",
    )

    def render(template, out, section, title, description, **extra):
        root = "../" * out.count("/")
        html = env.get_template(template).render(**base, root=root, section=section, title=title, description=description, **extra)
        target = DIST / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")

    for page in PAGES:
        render(*page)
    for o in orte:
        render("profil.html", f"heilbaeder/{o['slug']}.html", "baeder", o["name"],
               f"Radonheilbad {o['name']}, {o['region']}: Anwendungsform und Kontakt.", o=o)

    count = len(PAGES) + len(orte)
    print(f"{count} Seiten nach {DIST} geschrieben ({'Vorschau' if draft else 'live'}).")


if __name__ == "__main__":
    main()

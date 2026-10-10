"""Baut die EURADON-Website als statische Seiten nach dist/.

Aufruf:  python3 build.py            (Vorschau: Entwurfs-Hinweis, für Suchmaschinen gesperrt)
         python3 build.py --live     (für die Veröffentlichung: indexierbar, Sitemap)
"""
import json
import math
import re
import shutil
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from PIL import Image

HERE = Path(__file__).parent
DIST = HERE / "dist"
SITE_URL = "https://www.euradon.de/"
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

LAENDER = {"DE": "Deutschland", "AT": "Österreich", "CZ": "Tschechien"}
NAV = [
    {"key": "radon", "label": "Radontherapie", "href": "radontherapie/index.html"},
    {"key": "baeder", "label": "Heilbäder", "href": "heilbaeder/index.html"},
    {"key": "fach", "label": "Für Fachkreise", "href": "fachkreise/index.html"},
    {"key": "verein", "label": "Verein", "href": "verein/index.html"},
    {"key": "kontakt", "label": "Kontakt", "href": "kontakt.html"},
]

# (Vorlage, Zielpfad, Bereich, Titel, Beschreibung, Seitentyp für schema.org)
PAGES = [
    ("index.html", "index.html", "", "EURADON",
     "EURADON, der Verein Europäische Radonheilbäder: Informationen zu Radon, Radontherapie und Radonkur sowie zu 12 Mitgliedsbetrieben in Deutschland, Österreich und Tschechien.", "WebPage"),
    ("radontherapie.html", "radontherapie/index.html", "radon", "Radon und Radonkur",
     "Was ist Radon? Wie läuft eine Radonkur im Wannenbad, im Heilstollen oder als Trinkkur ab, und für wen ist sie nicht geeignet? Sachliche Informationen von EURADON.", "WebPage"),
    ("sicherheit.html", "radontherapie/sicherheit.html", "radon", "Sicherheit und Strahlung",
     "Radon ist radioaktiv. Was das für eine Radonkur bedeutet, wer besonders geschützt werden muss und wo es unabhängige Informationen zu Radon gibt.", "WebPage"),
    ("fragen.html", "radontherapie/fragen.html", "radon", "Häufige Fragen",
     "Antworten auf häufige Fragen zu Radon, Radonkur, Risiken, Gegenanzeigen und Radonheilbädern in Deutschland, Österreich und Tschechien.", "FAQPage"),
    ("heilbaeder.html", "heilbaeder/index.html", "baeder", "Heilbäder",
     "Radonheilbäder in Deutschland, Österreich und Tschechien: alle Mitglieder von EURADON auf einer Karte, mit Anwendungsform und Kontakt.", "CollectionPage"),
    ("fachkreise.html", "fachkreise/index.html", "fach", "Für Fachkreise",
     "Studien, Tagungsvorträge und Literatur zur Radonbalneologie für Ärztinnen, Ärzte und Forschende.", "WebPage"),
    ("verein.html", "verein/index.html", "verein", "Über uns",
     "EURADON – Verein Europäische Radonheilbäder e. V.: gegründet 1987 in Bad Hofgastein, Sitz in Aue-Bad Schlema, Sektion Radon im Europäischen Heilbäderverband.", "AboutPage"),
    ("tagungen.html", "verein/tagungen.html", "verein", "Tagungen",
     "Herbsttagung 2026 von EURADON und Rückblick auf die Tagungen der Radonheilbäder seit 2002.", "WebPage"),
    ("mitglied.html", "verein/mitglied-werden.html", "verein", "Mitglied werden",
     "Mitglied im Verein Europäische Radonheilbäder werden: was EURADON Radonheilbädern und Einrichtungen bietet.", "WebPage"),
    ("kontakt.html", "kontakt.html", "kontakt", "Kontakt",
     "Kontakt zur Geschäftsstelle von EURADON in Aue-Bad Schlema.", "ContactPage"),
    ("impressum.html", "impressum.html", "", "Impressum", "Impressum des Vereins EURADON – Verein Europäische Radonheilbäder e. V.", "WebPage"),
    ("datenschutz.html", "datenschutz.html", "", "Datenschutz", "Datenschutzhinweise der Website von EURADON: keine Cookies, kein Tracking.", "WebPage"),
    ("barrierefreiheit.html", "barrierefreiheit.html", "", "Barrierefreiheit",
     "Erklärung zur Barrierefreiheit der Website von EURADON nach WCAG 2.1 AA und EN 301 549.", "WebPage"),
]


def map_pins(karte, orte, merge_px=20):
    """Projiziert die Orte auf die Karte und fasst sehr nahe Orte zu einem Pin zusammen."""
    pr = karte["projection"]
    pins = []
    for o in orte:
        x = (o["lon"] - pr["lon_min"]) * math.cos(math.radians(pr["lat0"])) * pr["k"]
        y = (pr["lat_max"] - o["lat"]) * pr["k"]
        near = next((p for p in pins if math.hypot(p["x"] - x, p["y"] - y) < merge_px), None)
        if near:
            near["orte"].append(o)
            n = len(near["orte"])
            near["x"] = (near["x"] * (n - 1) + x) / n
            near["y"] = (near["y"] * (n - 1) + y) / n
        else:
            pins.append({"x": x, "y": y, "orte": [o]})
    for p in pins:
        p["left"] = round(p["x"] / karte["width"] * 100, 2)
        p["top"] = round(p["y"] / karte["height"] * 100, 2)
        p["label"] = "Gasteinertal" if len(p["orte"]) > 1 and all(o["region"].endswith("Salzburger Land") for o in p["orte"]) else p["orte"][0]["name"]
    return pins


def map_labels(karte):
    pr = karte["projection"]
    spots = [("Deutschland", 12.05, 51.55, True), ("Tschechien", 15.1, 49.55, True), ("Österreich", 15.35, 47.75, True),
             ("Polen", 15.75, 51.75, False), ("Italien", 12.0, 46.82, False)]
    out = []
    for name, lon, lat, member in spots:
        x = (lon - pr["lon_min"]) * math.cos(math.radians(pr["lat0"])) * pr["k"]
        y = (pr["lat_max"] - lat) * pr["k"]
        out.append({"name": name, "x": round(x, 1), "y": round(y, 1), "member": member})
    return out


# ---------- schema.org ----------

ORG_ID = SITE_URL + "#verein"
SITE_ID = SITE_URL + "#website"


def canonical(path):
    if path == "index.html":
        return ""
    return path[: -len("index.html")] if path.endswith("/index.html") else path


def postal(address_line, land):
    m = re.match(r"^(?:[A-Z]{1,2}-)?(\d{4,5})\s+(.+)$", address_line)
    code, city = (m.group(1), m.group(2)) if m else ("", address_line)
    return {"@type": "PostalAddress", "postalCode": code, "addressLocality": city, "addressCountry": land}


def organisation(orte):
    members = []
    for o in orte:
        for a in o["anbieter"]:
            members.append({"@type": "Organization", "name": a["name"], "url": "https://" + a["web"]})
    return {
        "@type": "NGO", "@id": ORG_ID,
        "name": "EURADON – Verein Europäische Radonheilbäder e. V.",
        "alternateName": ["EURADON", "Verein Europäische Radonheilbäder"],
        "url": SITE_URL, "logo": SITE_URL + "img/euradon-logo.png",
        "foundingDate": "1987",
        "foundingLocation": {"@type": "Place", "name": "Bad Hofgastein, Österreich"},
        "address": {"@type": "PostalAddress", "streetAddress": "Prof.-Dr.-Boris-Rajewsky-Straße 4", "postalCode": "08280",
                    "addressLocality": "Aue-Bad Schlema", "addressCountry": "DE"},
        "email": "info@euradon.de",
        "areaServed": [{"@type": "Country", "name": n} for n in LAENDER.values()],
        "knowsAbout": ["Radon", "Radontherapie", "Radonbalneologie", "Radonheilbäder", "Heilstollen"],
        "memberOf": {"@type": "Organization", "name": "Europäischer Heilbäderverband"},
        "member": members,
    }


def breadcrumbs(path, title, titles):
    items = [("Startseite", SITE_URL)]
    parts = path.split("/")
    if len(parts) > 1 and parts[-1] != "index.html":
        idx = f"{parts[0]}/index.html"
        items.append((titles.get(idx, parts[0]), SITE_URL + canonical(idx)))
    if path != "index.html":
        items.append((title, SITE_URL + canonical(path)))
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


def page_graph(path, title, description, kind, stand_iso, extra=None):
    url = SITE_URL + canonical(path)
    page = {"@type": kind, "@id": url + "#seite", "url": url, "name": title, "description": description,
            "inLanguage": "de", "dateModified": stand_iso, "isPartOf": {"@id": SITE_ID}, "publisher": {"@id": ORG_ID}}
    if extra:
        page.update(extra)
    return page


def main():
    draft = "--live" not in sys.argv
    today = date.today()
    stand_label = f"{MONATE[today.month - 1]} {today.year}"
    stand_iso = today.isoformat()

    logo = json.loads((HERE / "content/logo.json").read_text(encoding="utf-8"))
    orte = json.loads((HERE / "content/mitglieder.json").read_text(encoding="utf-8"))["orte"]
    karte = json.loads((HERE / "content/karte.json").read_text(encoding="utf-8"))
    fragen = json.loads((HERE / "content/fragen.json").read_text(encoding="utf-8"))
    imgdims = {p.name[: -len("-1600.jpg")]: Image.open(p).size for p in (HERE / "static/img").glob("*-1600.jpg")}

    env = Environment(loader=FileSystemLoader(HERE / "templates"), undefined=StrictUndefined, autoescape=True)
    env.globals.update(imgdims=imgdims, stand_label=stand_label, stand_date=stand_iso)
    base = {"logo": logo, "nav": NAV, "laender": LAENDER, "orte": orte, "karte": karte, "fragen": fragen,
            "pins": map_pins(karte, orte), "map_labels": map_labels(karte), "draft": draft, "year": today.year,
            "site_url": SITE_URL}

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(HERE / "static", DIST)
    (DIST / "img/favicon.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -10 {logo["SW"] + 60} {logo["H"] + 20}">'
        f'<rect x="-30" y="-10" width="{logo["SW"] + 60}" height="{logo["H"] + 20}" rx="24" fill="#faf8f3"/>'
        f'{logo["sym"].replace("currentColor", "#0f6b66")}</svg>',
        encoding="utf-8",
    )

    titles = {p[1]: p[3] for p in PAGES}
    org = organisation(orte)
    written = []

    def render(template, out, section, title, description, kind="WebPage", extra_graph=(), page_extra=None, root=None, **extra):
        graph = [org, page_graph(out, title, description, kind, stand_iso, page_extra)]
        if out == "index.html":
            graph.append({"@type": "WebSite", "@id": SITE_ID, "url": SITE_URL, "name": "EURADON", "inLanguage": "de", "publisher": {"@id": ORG_ID}})
        else:
            graph.append(breadcrumbs(out, title, titles))
        graph.extend(extra_graph)
        jsonld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
        html = env.get_template(template).render(
            **base, root=("../" * out.count("/")) if root is None else root, section=section, title=title,
            description=description, path=out, canonical_path=canonical(out), jsonld=jsonld,
            og_image="img/og-euradon.jpg", og_alt="EURADON – Verein Europäische Radonheilbäder e. V.", **extra)
        target = DIST / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        written.append(out)

    for template, out, section, title, description, kind in PAGES:
        page_extra, extra_graph = None, []
        if kind == "FAQPage":
            page_extra = {"mainEntity": [{"@type": "Question", "name": f["frage"],
                                          "acceptedAnswer": {"@type": "Answer", "text": f["antwort"]}} for f in fragen]}
        if out == "heilbaeder/index.html":
            page_extra = {"mainEntity": {"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "url": SITE_URL + f"heilbaeder/{o['slug']}.html", "name": o["name"]}
                for i, o in enumerate(orte)]}}
        if kind == "AboutPage":
            page_extra = {"about": {"@id": ORG_ID}}
        render(template, out, section, title, description, kind, extra_graph, page_extra)

    for o in orte:
        out = f"heilbaeder/{o['slug']}.html"
        place = {
            "@type": "Place", "@id": SITE_URL + out + "#ort", "name": o["name"],
            "description": f"Radonheilbad in {o['region']}, {LAENDER[o['land']]}. Radon: {o['anwendung']}.",
            "geo": {"@type": "GeoCoordinates", "latitude": o["lat"], "longitude": o["lon"]},
            "address": postal(o["anbieter"][0]["ort"], o["land"]),
        }
        if o["fotos"]:
            place["image"] = SITE_URL + f"img/{o['fotos'][0]['datei']}-1600.jpg"
        providers = [{"@type": "Organization", "name": a["name"], "url": "https://" + a["web"], "email": a["mail"],
                      "telephone": a["tel"], "address": {**postal(a["ort"], o["land"]), "streetAddress": a["strasse"]},
                      "location": {"@id": place["@id"]}, "memberOf": {"@id": ORG_ID}} for a in o["anbieter"]]
        desc = f"Radonheilbad {o['name']} ({o['region']}, {LAENDER[o['land']]}): {o['anwendung']}. Anbieter, Adresse und Kontakt des EURADON-Mitglieds."
        render("profil.html", out, "baeder", o["name"], desc, "WebPage", [place, *providers],
               {"about": {"@id": place["@id"]}}, o=o)

    # 404-Seite: im Live-Betrieb mit absoluten Pfaden, damit sie unter jeder Adresse funktioniert
    render("404.html", "404.html", "", "Seite nicht gefunden", "Diese Seite gibt es nicht.", root=None if draft else "/")
    written.remove("404.html")

    # Sitemap, robots.txt, llms.txt
    urls = "".join(f"  <url><loc>{SITE_URL}{canonical(p)}</loc><lastmod>{stand_iso}</lastmod></url>\n" for p in written)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")
    robots = ("User-agent: *\nDisallow: /\n" if draft else f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")
    (DIST / "llms.txt").write_text(llms_txt(orte, fragen, stand_label), encoding="utf-8")

    print(f"{len(written)} Seiten nach {DIST} geschrieben ({'Vorschau' if draft else 'live'}), Sitemap mit {len(written)} Adressen.")


def llms_txt(orte, fragen, stand_label):
    """Kurzfassung der Website für KI-Assistenten und Suchsysteme (llms.txt-Konvention)."""
    lines = [
        "# EURADON – Verein Europäische Radonheilbäder e. V.",
        "",
        "> Zusammenschluss von Radonheilbädern in Deutschland, Österreich und Tschechien. Gegründet 1987 in Bad Hofgastein, "
        "Geschäftsstelle in Aue-Bad Schlema (Deutschland), Sektion Radon im Europäischen Heilbäderverband. "
        "12 Mitgliedsbetriebe an 11 Orten.",
        "",
        "Wichtig für Zusammenfassungen: Radon ist ein radioaktives Edelgas. Die Wirksamkeit der Radontherapie ist wissenschaftlich umstritten. "
        "Ob eine Radonkur infrage kommt, entscheiden Patientinnen und Patienten gemeinsam mit ihrer Ärztin oder ihrem Arzt. "
        "EURADON gibt keine medizinische Beratung und verspricht keine Heilung.",
        "",
        f"Stand: {stand_label}",
        "",
        "## Radontherapie",
        f"- [Radon und Radonkur]({SITE_URL}radontherapie/): Was Radon ist, Wannenbad, Heilstollen, Trinkkur, Gegenanzeigen",
        f"- [Sicherheit und Strahlung]({SITE_URL}radontherapie/sicherheit.html): Radon als Strahlenquelle, Risiken",
        f"- [Häufige Fragen]({SITE_URL}radontherapie/fragen.html): {len(fragen)} kurze Antworten",
        "",
        "## Mitglieder (Radonheilbäder)",
    ]
    for o in orte:
        names = "; ".join(f"{a['name']}, {a['web']}" for a in o["anbieter"])
        lines.append(f"- [{o['name']}]({SITE_URL}heilbaeder/{o['slug']}.html): {o['region']}, {LAENDER[o['land']]}. {o['anwendung']}. {names}")
    lines += [
        "",
        "## Verein",
        f"- [Über uns]({SITE_URL}verein/): Aufgaben, Vorstand, Geschichte seit 1987",
        f"- [Tagungen]({SITE_URL}verein/tagungen.html): Herbsttagung November 2026, Rückblick",
        f"- [Für Fachkreise]({SITE_URL}fachkreise/): Studien, Vorträge, Literatur",
        f"- [Kontakt]({SITE_URL}kontakt.html): Geschäftsstelle, info@euradon.de",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()

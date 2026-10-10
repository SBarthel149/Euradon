"""Erzeugt content/karte.json: Ländergrenzen als SVG-Pfade für die Mitgliederkarte.

Grundlage: Natural Earth (gemeinfrei) über das npm-Paket world-atlas@2.0.2, Datei countries-50m.json.
Aufruf:  python3 tools/make_map.py /pfad/zu/countries-50m.json
"""
import json
import math
import sys
from pathlib import Path

# Kartenausschnitt (Grad) und Größe der Zeichenfläche
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = 10.9, 16.3, 46.7, 52.0
WIDTH = 700
LAT0 = (LAT_MIN + LAT_MAX) / 2
KX = WIDTH / ((LON_MAX - LON_MIN) * math.cos(math.radians(LAT0)))
HEIGHT = round((LAT_MAX - LAT_MIN) * KX)

MEMBERS = {"276": "Deutschland", "040": "Österreich", "203": "Tschechien"}
NEIGHBOURS = {"616": "Polen", "756": "Schweiz", "703": "Slowakei", "348": "Ungarn", "705": "Slowenien",
              "380": "Italien", "250": "Frankreich", "438": "Liechtenstein", "191": "Kroatien", "442": "Luxemburg"}


def project(lon, lat):
    x = (lon - LON_MIN) * math.cos(math.radians(LAT0)) * KX
    y = (LAT_MAX - lat) * KX
    return x, y


def decode_arcs(topo):
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def ring_points(ring, arcs):
    pts = []
    for i in ring:
        a = arcs[i] if i >= 0 else list(reversed(arcs[~i]))
        pts.extend(a if not pts else a[1:])
    return pts


def to_path(polys, arcs):
    out = []
    for poly in polys:
        for ring in poly:
            pts = [project(*p) for p in ring_points(ring, arcs)]
            # Ringe weit außerhalb des Ausschnitts weglassen
            if all(x < -200 or x > WIDTH + 200 or y < -200 or y > HEIGHT + 200 for x, y in pts):
                continue
            simplified = [pts[0]]
            for p in pts[1:]:
                if abs(p[0] - simplified[-1][0]) + abs(p[1] - simplified[-1][1]) >= 1.2:
                    simplified.append(p)
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in simplified) + "Z")
    return "".join(out)


def main():
    topo = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    arcs = decode_arcs(topo)
    countries = []
    for g in topo["objects"]["countries"]["geometries"]:
        cid = g.get("id")
        if cid not in MEMBERS and cid not in NEIGHBOURS:
            continue
        polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        countries.append({"id": cid, "name": MEMBERS.get(cid) or NEIGHBOURS[cid], "member": cid in MEMBERS, "d": to_path(polys, arcs)})
    data = {
        "quelle": "Natural Earth (gemeinfrei), world-atlas@2.0.2 countries-50m",
        "width": WIDTH, "height": HEIGHT,
        "projection": {"lon_min": LON_MIN, "lat_max": LAT_MAX, "lat0": LAT0, "k": KX},
        "countries": countries,
    }
    out = Path(__file__).parent.parent / "content/karte.json"
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"{out} geschrieben: {len(countries)} Länder, {out.stat().st_size // 1024} KB, {WIDTH}x{HEIGHT}")


if __name__ == "__main__":
    main()

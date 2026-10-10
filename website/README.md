# EURADON-Website

Statische Website, gebaut aus Vorlagen (Jinja2). Farbwelt „Thermal“, Schrift „Modern“ (Lexend + Atkinson Hyperlegible, lokal eingebunden), Motiv „Bögen“.

- `content/mitglieder.json` – Mitglieder und Kontaktdaten (Quelle: Broschüre, 12. Auflage)
- `templates/` – Seitenvorlagen
- `static/` – CSS, Schriften, Fotos
- `build.py` – erzeugt die Seiten in `dist/`

```
pip install jinja2
python3 build.py          # Vorschau mit Entwurfs-Hinweis, nicht indexierbar
python3 build.py --live   # für die Veröffentlichung
```

Texte mit Gesundheitsbezug folgen dem Textleitfaden (`konzept/textleitfaden.html`) und gehen vor der Veröffentlichung zur Prüfung an die Kanzlei.

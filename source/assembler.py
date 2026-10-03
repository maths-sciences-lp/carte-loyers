"""Assemble index.html à partir de template.html et des fichiers JSON.

Usage : python3 assembler.py   (écrit ../index.html)
"""
from pathlib import Path

ICI = Path(__file__).parent
DESC = ("Carte des loyers en France, commune par commune : prix au m², loyer d'un 1 ou 2 pièces, "
        "d'un 3 pièces et d'une maison, filtre budget et comparaison de communes. Données officielles 2025.")
CREDIT = "Carte réalisée pour la chaîne Maths·Sciences LP. "

t = (ICI / "template.html").read_text()
for cle, fichier in (("__DATA__", "data.json"), ("__GEO__", "geo.json"), ("__COMGEO__", "communes.json"), ("__VILLES__", "villes.json")):
    t = t.replace(cle, (ICI / fichier).read_text())
t = t.replace('document.getElementById("note").innerHTML = `Source : ',
              'document.getElementById("note").innerHTML = `' + CREDIT + 'Source : ', 1)
i = t.index("</style>") + len("</style>")
html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{DESC}">
<meta property="og:title" content="Loyers au m² en France">
<meta property="og:description" content="{DESC}">
<meta property="og:type" content="website">
<meta name="color-scheme" content="light dark">
{t[:i]}
<style>body{{margin:0}}img{{max-width:100%}}</style>
</head>
<body>
{t[i:]}
</body>
</html>
"""
(ICI.parent / "index.html").write_text(html)
print("index.html :", len(html), "caractères")

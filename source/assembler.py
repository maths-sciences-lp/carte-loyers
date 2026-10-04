"""Assemble index.html à partir de template.html et des fichiers JSON.

Usage : python3 assembler.py   (écrit ../index.html)
"""
from pathlib import Path

ICI = Path(__file__).parent
DESC = ("Louer ou acheter en France, commune par commune : loyers et prix de vente au m², loyer et prix d'un "
        "1 ou 2 pièces, d'un 3 pièces et d'une maison, filtre budget et comparaison de communes. Données officielles.")
URL = "https://maths-sciences-lp.github.io/carte-loyers/"
ICONE = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
         "%3Crect width='32' height='32' rx='7' fill='%231c5cab'/%3E"
         "%3Cpath d='M16 7 5 16h3v9h6v-6h4v6h6v-9h3z' fill='white'/%3E%3C/svg%3E")
CREDIT = "Carte réalisée pour la chaîne Maths·Sciences LP."

t = (ICI / "template.html").read_text()
for cle, fichier in (("__DATA__", "data.json"), ("__GEO__", "geo.json"), ("__COMGEO__", "communes.json"), ("__VILLES__", "villes.json"), ("__VENTES__", "ventes.json"), ("__REVENUS__", "revenus.json"), ("__INDIC__", "indicateurs.json")):
    t = t.replace(cle, (ICI / fichier).read_text())
t = t.replace("__CREDIT__", f'<p class="credit">{CREDIT}</p>', 1)
i = t.index("</style>") + len("</style>")
html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{DESC}">
<meta property="og:title" content="Loyers et prix au m² en France">
<meta property="og:description" content="{DESC}">
<meta property="og:type" content="website">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{URL}apercu.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{ICONE}">
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

"""Niveau de vie médian par commune (INSEE, Filosofi 2021, géographie 2025).

Le niveau de vie est le revenu disponible du ménage (après impôts, avec les aides) divisé par le
nombre d'unités de consommation ; pour une personne seule, c'est son revenu disponible.
Valeur annuelle en euros. Les communes trop petites ne sont pas publiées (secret statistique).
Sortie : revenus.json. Usage : python3 preparer_revenus.py
"""
import csv, io, json, urllib.request, zipfile
from pathlib import Path

ICI = Path(__file__).parent
CACHE = ICI / "cache"; CACHE.mkdir(exist_ok=True)
URL = "https://www.insee.fr/fr/statistiques/fichier/7756729/base-cc-filosofi-2021-geo2025_csv.zip"

def main():
    z = CACHE / "filosofi.zip"
    if not z.exists():
        z.write_bytes(urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})).read())
    with zipfile.ZipFile(z) as zf:
        texte = zf.read("DS_FILOSOFI_CC_data.csv").decode("utf-8")
    sortie = {"coms": {}, "deps": {}, "fr": None, "annee": 2021}
    for r in csv.DictReader(io.StringIO(texte), delimiter=";"):
        if r["FILOSOFI_MEASURE"] != "MED_SL" or not r["OBS_VALUE"]:
            continue
        v = round(float(r["OBS_VALUE"]))
        if r["GEO_OBJECT"] in ("COM", "ARM"): sortie["coms"][r["GEO"]] = v
        elif r["GEO_OBJECT"] == "DEP": sortie["deps"][r["GEO"]] = v
        elif r["GEO_OBJECT"] == "FRANCE": sortie["fr"] = v
    (ICI / "revenus.json").write_text(json.dumps(sortie, separators=(",", ":")))
    print(len(sortie["coms"]), "communes ou arrondissements,", len(sortie["deps"]), "départements, France :", sortie["fr"])

if __name__ == "__main__":
    main()

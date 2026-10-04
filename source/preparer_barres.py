"""Barres d'entrée du mouvement inter-académique, PLP mathématiques-sciences physiques (P1315).

- Années publiées par le ministère (comparateur « info-mutations », barème du dernier entrant et
  nombre d'entrants) : récupérées automatiquement.
- 2022 et 2023 : bilan publié par SUD éducation (mutations.sudeducation.org/plp/), recopié ci-dessous.
Une barre absente = aucun entrant ou un seul (le ministère ne l'affiche pas).
Sortie : barres.json. Usage : python3 preparer_barres.py (après preparer_zones.py)
"""
import json, subprocess, unicodedata
from pathlib import Path

ICI = Path(__file__).parent
API = "https://info-mutations.phm.education.gouv.fr/cmpmo-back/resultats/"
DISCIPLINE = "P1315"

# SUD éducation, barres inter PLP maths-sciences : [2023, 2022] ; None = pas de barre publiée
SUD = {"AIX-MARSEILLE": [374, 471], "AMIENS": [14, 14], "BESANCON": [655, 621], "BORDEAUX": [785, 560],
       "CLERMONT-FERRAND": [381, 414], "CORSE": [None, None], "CRETEIL": [14, 14], "DIJON": [811, 41],
       "GRENOBLE": [164, 164], "GUADELOUPE": [1515, None], "GUYANE": [280, 88], "LILLE": [164, 14],
       "LIMOGES": [364, 464], "LYON": [215, 171], "MARTINIQUE": [2161, None], "MAYOTTE": [215, 41],
       "MONTPELLIER": [604, 524], "NANCY-METZ": [171, 14], "NANTES": [583, 364], "NICE": [314, 370],
       "NORMANDIE": [521, 314.3], "ORLEANS-TOURS": [421, 130], "PARIS": [34, 63], "POITIERS": [474, 361],
       "REIMS": [54, 554], "RENNES": [734, 583], "REUNION": [1474, 1349], "STRASBOURG": [171, 364],
       "TOULOUSE": [528, 820], "VERSAILLES": [14, 14]}
NOTES = {"NORMANDIE": {"2022": "deux valeurs publiées (« * » et 314,3), sans doute les anciennes académies de Caen et de Rouen"}}

def cle(n):
    n = unicodedata.normalize("NFD", n).encode("ascii", "ignore").decode().upper().replace("*", "").strip()
    return n.removeprefix("LA ")

def api(chemin, corps=None):
    # curl plutôt qu'urllib : Python ne reconnaît pas la chaîne de certificats de ce site
    cmd = ["curl", "-s", "-m", "60", "-A", "Mozilla/5.0", API + chemin]
    if corps: cmd += ["-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps(corps)]
    return json.loads(subprocess.run(cmd, capture_output=True, check=True).stdout)

def main():
    noms = {cle(a): a for a in {v[0] for v in json.loads((ICI / "zones.json").read_text())["deps"].values()}}
    aca = {n: {} for n in noms.values()}
    for i, an in enumerate((2023, 2022)):
        for k, v in SUD.items():
            if k in noms: aca[noms[k]][str(an)] = [v[i], None]
    annees_off = sorted(api("annee"))
    for an in annees_off:
        for r in api("search", {"annee": an, "disciplineCode": DISCIPLINE, "typeMvtCode": "INTER", "typeEnsCode": "2D"}):
            k = cle(r["academieLib"])
            if k not in noms: continue
            b = r["barreEntrant"] or None
            aca[noms[k]][str(an)] = [round(b, 1) if b else None, r["nbEntrants"]]
    annees = sorted({int(a) for v in aca.values() for a in v})
    notes = {noms[k]: v for k, v in NOTES.items() if k in noms}
    (ICI / "barres.json").write_text(json.dumps({"discipline": "PLP mathématiques-sciences physiques", "annees": annees,
        "officielles": annees_off, "aca": aca, "notes": notes}, ensure_ascii=False, separators=(",", ":")))
    print("années", annees, "| officielles", annees_off, "|", len(aca), "académies")
    print("Normandie", aca.get("Normandie"))

if __name__ == "__main__":
    main()

"""Indicateurs complémentaires par commune : zonage ABC, logements vacants, encadrement des loyers.

- Zonage ABC (ministère de la Transition écologique, en vigueur au 26 juin 2026) : tension du marché,
  de A bis (la plus tendue) à C (la moins tendue). Paris, Lyon et Marseille : zone de la ville.
- Logements vacants du parc privé (LOVAC, ministère, Cerema) : part des logements privés vides au
  1er janvier 2024 (édition 2025), commune par commune ; petites valeurs non publiées (secret).
- Encadrement des loyers : liste de service-public.gouv.fr (fiche F1314, vérifiée le 1er août 2026) ;
  2 = toute la commune, 1 = une partie de la commune.
Sortie : indicateurs.json. Usage : python3 preparer_indicateurs.py (après preparer_donnees.py)
"""
import csv, io, json, unicodedata, urllib.request
from pathlib import Path

ICI = Path(__file__).parent
CACHE = ICI / "cache"; CACHE.mkdir(exist_ok=True)
ABC = "https://static.data.gouv.fr/resources/liste-des-communes-selon-le-zonage-abc/20260703-091314/liste-ensemble-des-communes-zonage-abc-en-vigueur-26-juin-2026.csv"
LOVAC = "https://static.data.gouv.fr/resources/logements-vacants-du-parc-prive-par-commune-departement-region-france/20260625-163627/lovac-opendata-communes26.csv"

# Territoires où les loyers sont plafonnés (service-public.gouv.fr, F1314, vérifié le 1er août 2026)
ENCADREMENT = {
    "75": ["Paris"],
    "93": ["Bagnolet", "Bobigny", "Bondy", "Le Pré-Saint-Gervais", "Les Lilas", "Montreuil", "Noisy-le-Sec", "Pantin", "Romainville",
           "Aubervilliers", "La Courneuve", "Épinay-sur-Seine", "L'Île-Saint-Denis", "Saint-Denis", "Saint-Ouen-sur-Seine", "Stains", "Villetaneuse"],
    "33": ["Bordeaux"],
    "59": ["Lille"],          # avec Hellemmes et Lomme, communes associées de Lille
    "69": ["Lyon", "Villeurbanne"],
    "34": ["Montpellier"],
    "64": ["Ahetze", "Anglet", "Arbonne", "Arcangues", "Ascain", "Bassussarry", "Bayonne", "Biarritz", "Bidart", "Biriatou", "Boucau",
           "Ciboure", "Guéthary", "Hendaye", "Jatxou", "Lahonce", "Larressore", "Mouguerre", "Saint-Jean-de-Luz", "Saint-Pierre-d'Irube",
           "Urcuit", "Urrugne", "Ustaritz", "Villefranque"],
    "38": ["Bresson", "Claix", "Domène", "Eybens", "Fontanil-Cornillon", "Gières", "Meylan", "Murianette", "Poisat", "La Tronche",
           "Seyssins", "Varces-Allières-et-Risset", "Venon"],
}
ENCADREMENT_PARTIEL = {"38": ["Échirolles", "Fontaine", "Grenoble", "Le Pont-de-Claix", "Saint-Égrève", "Saint-Martin-d'Hères", "Sassenage", "Seyssinet-Pariset"]}

def get(url, nom):
    f = CACHE / nom
    if not f.exists():
        f.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read())
    return f.read_bytes()

def norm(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return " ".join(s.replace("-", " ").replace("'", " ").split())

def ville(code):
    return "75056" if code.startswith("751") else "69123" if code.startswith("6938") else "13055" if code.startswith("132") else None

def main():
    coms = json.loads((ICI / "data.json").read_text())["coms"]   # [code, nom, dep, ...]
    codes = {c[0] for c in coms}

    abc = {}
    for r in csv.reader(io.StringIO(get(ABC, "abc.csv").decode("utf-8-sig")), delimiter=";"):
        if len(r) >= 4 and r[0] != "CODGEO": abc[r[0]] = r[3].replace("Abis", "A bis")
    zone = {c: abc.get(c) or abc.get(ville(c) or "") for c in codes}

    vac = {}
    for r in csv.DictReader(io.StringIO(get(LOVAC, "lovac.csv").decode("latin-1")), delimiter=";"):
        v, total = r["pp_vacant_25"], r["ff_pp_total_25"]
        if v.isdigit() and total.isdigit() and int(total) > 0:
            vac[r["CODGEO_26"]] = round(100 * int(v) / int(total), 1)

    enc, trouve = {}, set()
    index = {(c[2], norm(c[1])): c[0] for c in coms}
    for niveau, table in ((2, ENCADREMENT), (1, ENCADREMENT_PARTIEL)):
        for dep, noms in table.items():
            for nom in noms:
                if dep == "75" or (dep == "69" and nom == "Lyon"):
                    pref = "751" if dep == "75" else "6938"
                    for c in codes:
                        if c.startswith(pref): enc[c] = niveau
                    trouve.add(nom); continue
                c = index.get((dep, norm(nom)))
                if c: enc[c] = niveau; trouve.add(nom)
                else: print("introuvable :", dep, nom)

    sortie = {"abc": {c: z for c, z in zone.items() if z}, "vac": {c: v for c, v in vac.items() if c in codes}, "enc": enc}
    (ICI / "indicateurs.json").write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")))
    print("zones :", len(sortie["abc"]), "| vacance :", len(sortie["vac"]), "| encadrement :", len(enc), "communes ou arrondissements")

if __name__ == "__main__":
    main()

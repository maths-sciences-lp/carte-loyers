"""Gare la plus proche (SNCF) et services sur place (INSEE, base permanente des équipements 2025).

- Gares : « Gares de voyageurs » (SNCF, open data), avec leur catégorie A (intérêt national),
  B (régional) ou C (local). Distance à vol d'oiseau depuis le centre de la commune
  (geo.api.gouv.fr) jusqu'à la gare la plus proche, et jusqu'à la gare de catégorie A la plus proche.
  Pas de valeur en Corse (Chemins de fer de la Corse, hors fichier SNCF) ni outre-mer.
- Services : nombre d'équipements dans la commune (BPE 2025, géographie au 1er janvier 2026) :
  médecin généraliste, pharmacie, école (maternelle, primaire ou élémentaire), collège,
  supermarché ou hypermarché, boulangerie.
Sortie : services.json. Usage : python3 preparer_services.py (après preparer_donnees.py)
"""
import csv, io, json, math, urllib.request, zipfile
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).parent
CACHE = ICI / "cache"; CACHE.mkdir(exist_ok=True)
GARES = "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/gares-de-voyageurs/exports/csv?use_labels=true"
BPE = "https://www.insee.fr/fr/statistiques/fichier/8217527/DS_BPE_CSV_FR.zip"
ARR = "https://geo.api.gouv.fr/communes?type=arrondissement-municipal&fields=code,centre&format=json"
COMMUNES = "https://geo.api.gouv.fr/communes?fields=nom,code,population,centre,codeDepartement&format=json"
# Types d'équipements retenus (codes INSEE) : clé -> codes
TYPES = {"med": ["D265"], "pha": ["D307"], "eco": ["C107", "C108", "C109"], "col": ["C201"],
         "sup": ["B104", "B105"], "bou": ["B207"]}

def get(url, nom):
    f = CACHE / nom
    if not f.exists():
        f.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read())
    return f.read_bytes()

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))

class Grille:
    """Recherche du point le plus proche par cases de 0,25° (Python pur, sans numpy)."""
    def __init__(self, pts, pas=0.25):
        self.pas, self.cases = pas, defaultdict(list)
        for i, (la, lo) in enumerate(pts): self.cases[(int(la // pas), int(lo // pas))].append(i)
        self.pts = pts
    def proche(self, p, rmax=40):
        ci, cj = int(p[0] // self.pas), int(p[1] // self.pas)
        best, bi = 1e9, None
        for r in range(rmax + 1):
            for i in range(ci - r, ci + r + 1):
                for j in range(cj - r, cj + r + 1):
                    if max(abs(i - ci), abs(j - cj)) != r: continue
                    for k in self.cases.get((i, j), ()):
                        d = km(p, self.pts[k])
                        if d < best: best, bi = d, k
            if bi is not None and best < r * self.pas * 75: break   # 0,25° ≥ ~18 km en France : marge large
        return bi, best

def main():
    codes = {c[0] for c in json.loads((ICI / "data.json").read_text())["coms"]}
    centre = {c["code"]: c["centre"]["coordinates"] for c in json.loads(get(COMMUNES, "communes.json")) if c.get("centre")}
    centre.update({a["code"]: a["centre"]["coordinates"] for a in json.loads(get(ARR, "arr-centres.json")) if a.get("centre")})

    noms, pts, cat = [], [], []
    for r in csv.DictReader(io.StringIO(get(GARES, "gares.csv").decode("utf-8-sig")), delimiter=";"):
        try: la, lo = map(float, r["Position géographique"].split(","))
        except ValueError: continue
        noms.append(r["Nom_Gare"]); pts.append((la, lo)); cat.append("A" in r["Segment(s) DRG"].split(";"))
    tout = Grille(pts)
    ia = [i for i, a in enumerate(cat) if a]
    grandes = Grille([pts[i] for i in ia], pas=0.5)

    with zipfile.ZipFile(io.BytesIO(get(BPE, "bpe.zip"))) as z:
        nom_csv = next(n for n in z.namelist() if n.endswith("_data.csv"))
        texte = z.read(nom_csv).decode("utf-8")
    vers = {code: k for k, l in TYPES.items() for code in l}
    nb = defaultdict(lambda: defaultdict(int))
    for r in csv.DictReader(io.StringIO(texte), delimiter=";"):
        if r["GEO_OBJECT"] in ("COM", "ARM") and r["FACILITY_TYPE"] in vers and r["BPE_MEASURE"] == "FACILITIES":
            nb[r["GEO"]][vers[r["FACILITY_TYPE"]]] += int(float(r["OBS_VALUE"] or 0))

    sortie, sans_centre = {}, 0
    for c in codes:
        e = [None, None, None, None] + [nb.get(c, {}).get(k, 0) for k in TYPES]
        # Outre-mer : pas de réseau SNCF ; Corse : trains des Chemins de fer de la Corse, absents du fichier SNCF
        if c in centre and not c.startswith(("97", "2A", "2B")):
            p = (centre[c][1], centre[c][0])
            i, d = tout.proche(p); e[0], e[1] = round(d, 1), i
            j, d2 = grandes.proche(p); e[2], e[3] = round(d2, 1), ia[j]
        elif c not in centre: sans_centre += 1
        sortie[c] = e
    (ICI / "services.json").write_text(json.dumps({"gares": noms, "coms": sortie, "types": list(TYPES)}, ensure_ascii=False, separators=(",", ":")))
    print(len(noms), "gares dont", len(ia), "de catégorie A |", len(sortie), "communes, sans centre :", sans_centre)

if __name__ == "__main__":
    main()

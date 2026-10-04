"""Académies et régions de chaque département, et leurs frontières pour la carte.

Source : « Référentiel géographique français » (ministère de l'Enseignement supérieur et de la
Recherche, data.enseignementsup-recherche.gouv.fr). Les frontières sont les tronçons de contour
partagés par deux départements de groupes différents (contours de geo.json).
Sortie : zones.json. Usage : python3 preparer_zones.py (après preparer_donnees.py)
"""
import csv, io, json, urllib.request
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).parent
CACHE = ICI / "cache"; CACHE.mkdir(exist_ok=True)
URL = "https://data.enseignementsup-recherche.gouv.fr/explore/dataset/fr-esr-referentiel-geographique/download/?format=csv&timezone=Europe/Berlin&use_labels_for_header=true"

def main():
    f = CACHE / "referentiel.csv"
    if not f.exists():
        f.write_bytes(urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})).read())
    deps = {}
    for r in csv.DictReader(io.StringIO(f.read_text(encoding="utf-8-sig")), delimiter=";"):
        deps[r["DEP_CODE"]] = [r["ACA_NOM"], r["REG_NOM"]]
    geo = json.loads((ICI / "geo.json").read_text())
    connus = {f["properties"]["c"] for f in geo["features"]}
    deps = {d: v for d, v in deps.items() if d in connus}

    seg = defaultdict(set)
    for feat in geo["features"]:
        d = feat["properties"]["c"]
        if len(d) == 3: continue
        for poly in feat["geometry"]["coordinates"]:
            for ring in poly:
                for a, b in zip(ring, ring[1:]):
                    seg[tuple(sorted((tuple(a), tuple(b))))].add(d)
    lignes = {}
    for i, cle in ((0, "aca"), (1, "reg")):
        l = []
        for (a, b), ds in seg.items():
            if len(ds) == 2:
                x, y = sorted(ds)
                if deps[x][i] != deps[y][i]: l.append([a[0], a[1], b[0], b[1]])
        lignes[cle] = l
    (ICI / "zones.json").write_text(json.dumps({"deps": deps, "lignes": lignes}, ensure_ascii=False, separators=(",", ":")))
    print(len(deps), "départements |", len({v[0] for v in deps.values()}), "académies |", len({v[1] for v in deps.values()}), "régions |",
          {k: len(v) for k, v in lignes.items()}, "tronçons de frontière")

if __name__ == "__main__":
    main()

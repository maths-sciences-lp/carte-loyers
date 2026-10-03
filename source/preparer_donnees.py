"""Télécharge les données officielles et fabrique les fichiers JSON de la carte.

Sorties (dans ce dossier) : data.json, geo.json, communes.json, villes.json.
Usage : python3 preparer_donnees.py
"""
import csv, gzip, io, json, urllib.request
from pathlib import Path

ICI = Path(__file__).parent
CACHE = ICI / "cache"
CACHE.mkdir(exist_ok=True)

# Carte des loyers 2025 (ANIL, ministère du Logement) : un fichier par type de logement
LOYERS = {
    "a":   "https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/20251211-145010/pred-app-mef-dhup.csv",
    "m":   "https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/20251211-145039/pred-mai-mef-dhup.csv",
    "a12": "https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/20251211-144934/pred-app12-mef-dhup.csv",
    "a3":  "https://static.data.gouv.fr/resources/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/20251211-144951/pred-app3-mef-dhup.csv",
}
DEP_METRO = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
DEP_OM = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-avec-outre-mer.geojson"
COM_1000 = "https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/latest/geojson/communes-1000m.geojson.gz"
COM_100 = "https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/latest/geojson/communes-100m.geojson.gz"
POP = "https://geo.api.gouv.fr/communes?fields=nom,code,population,centre,codeDepartement&format=json"
POP_ARR = "https://geo.api.gouv.fr/communes?type=arrondissement-municipal&fields=code,population&format=json"


def get(url, name):
    f = CACHE / name
    if not f.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 carte-loyers"})
        f.write_bytes(urllib.request.urlopen(req).read())
    data = f.read_bytes()
    return gzip.decompress(data) if name.endswith(".gz") else data


def lire_loyers(key):
    texte = get(LOYERS[key], f"{key}.csv").decode("latin-1")
    return {r["INSEE_C"]: (r["LIBGEO"], r["DEP"], float(r["loypredm2"].replace(",", ".")))
            for r in csv.DictReader(io.StringIO(texte), delimiter=";")}


def main():
    src = {k: lire_loyers(k) for k in LOYERS}
    communes_api = json.loads(get(POP, "communes.json"))
    pop = {c["code"]: c.get("population") or 0 for c in communes_api}
    for a in json.loads(get(POP_ARR, "arrondissements.json")):
        pop[a["code"]] = a.get("population") or 0

    # Départements : moyenne des communes pondérée par la population
    dep_geo = json.loads(get(DEP_METRO, "dep.geojson"))
    noms = {f["properties"]["code"]: f["properties"]["nom"] for f in dep_geo["features"]}
    noms.update({"971": "Guadeloupe", "972": "Martinique", "973": "Guyane", "974": "La Réunion"})
    deps, fr = {}, {}
    for key, s in src.items():
        acc = {}
        for code, (_, dep, v) in s.items():
            w = pop.get(code, 0); x = acc.setdefault(dep, [0, 0]); x[0] += w * v; x[1] += w
        for dep, (sv, sw) in acc.items():
            deps.setdefault(dep, {"n": noms.get(dep, dep)})[key] = round(sv / sw, 1)
        fr[key] = round(sum(pop.get(c, 0) * v for c, (_, _, v) in s.items()) / sum(pop.get(c, 0) for c in s), 1)
    val = lambda key, code: round(src[key][code][2], 1) if code in src[key] else None
    coms = sorted(([c, n, d, val("a", c), val("m", c), pop.get(c, 0), val("a12", c), val("a3", c)]
                   for c, (n, d, _) in src["a"].items()), key=lambda c: -c[5])
    (ICI / "data.json").write_text(json.dumps({"deps": deps, "fr": fr, "coms": coms}, ensure_ascii=False, separators=(",", ":")))

    # Contours des départements (métropole + outre-mer simplifié)
    def rnd(ring, step=1):
        pts = ring[::step]
        if pts[-1] != ring[-1]: pts.append(ring[-1])
        out = []
        for x, y in pts:
            p = [round(x, 3), round(y, 3)]
            if not out or out[-1] != p: out.append(p)
        return out if len(out) >= 4 else None

    def simpl(g, maxpts):
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        res = []
        for poly in polys:
            rings = []
            for i, r in enumerate(poly):
                rr = rnd(r, max(1, len(r) // maxpts))
                if rr: rings.append(rr)
                elif i == 0: break
            if rings: res.append(rings)
        return {"type": "MultiPolygon", "coordinates": res}

    feats = [{"type": "Feature", "properties": {"c": f["properties"]["code"]}, "geometry": simpl(f["geometry"], 100000)}
             for f in dep_geo["features"]]
    for f in json.loads(get(DEP_OM, "depom.geojson"))["features"]:
        if len(f["properties"]["code"]) == 3:
            feats.append({"type": "Feature", "properties": {"c": f["properties"]["code"]}, "geometry": simpl(f["geometry"], 250)})
    (ICI / "geo.json").write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))

    # Contours des communes, regroupés par département (coordonnées au millième de degré, en écarts successifs).
    # Contours plus précis (100 m) pour Paris, la petite couronne et les arrondissements de Lyon et Marseille.
    g1 = json.loads(get(COM_1000, "com1000.geojson.gz"))
    g2 = {f["properties"]["code"]: f for f in json.loads(get(COM_100, "com100.geojson.gz"))["features"]}
    fin = lambda c, d: d in {"75", "92", "93", "94"} or c.startswith("6938") or c.startswith("132")

    def encode(geom):
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        enc = []
        for poly in polys:
            rings = []
            for i, r in enumerate(poly):
                q = []
                for x, y in r:
                    p = (round(x * 1000), round(y * 1000))
                    if not q or q[-1] != p: q.append(p)
                if len(q) < 4:
                    if i == 0: break
                    continue
                flat = [q[0][0], q[0][1]]
                for a, b in zip(q, q[1:]): flat += [b[0] - a[0], b[1] - a[1]]
                rings.append(flat)
            if rings: enc.append(rings)
        return enc

    out, faits = {}, set()
    for f in g1["features"]:
        c, d = f["properties"]["code"], f["properties"]["departement"]
        if c not in src["a"]: continue
        geom = g2[c]["geometry"] if fin(c, d) and c in g2 else f["geometry"]
        e = encode(geom)
        if e: out.setdefault(d, []).append([c, e]); faits.add(c)
    for c in set(src["a"]) - faits:  # commune effacée par la simplification : version 100 m
        if c in g2:
            e = encode(g2[c]["geometry"])
            if e: out.setdefault(g2[c]["properties"]["departement"], []).append([c, e])
    (ICI / "communes.json").write_text(json.dumps(out, separators=(",", ":")))

    # Villes de plus de 100 000 habitants
    big = sorted((c for c in communes_api if (c.get("population") or 0) >= 100000), key=lambda c: -c["population"])
    villes = [[c["nom"], c["codeDepartement"], round(c["centre"]["coordinates"][0], 4), round(c["centre"]["coordinates"][1], 4), c["population"]] for c in big]
    (ICI / "villes.json").write_text(json.dumps(villes, ensure_ascii=False, separators=(",", ":")))
    print(len(coms), "communes,", len(villes), "grandes villes")


if __name__ == "__main__":
    main()

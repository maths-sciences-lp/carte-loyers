"""Prix de vente au m² par commune, à partir des « Demandes de valeurs foncières » (DGFiP, version géolocalisée Etalab).

Méthode :
- ventes de 2024 et 2025 (nature « Vente ») ;
- une vente est gardée si elle porte sur un seul logement (une maison ou un appartement),
  avec ou sans dépendance (garage, cave), sans local commercial ;
- prix au m² = valeur foncière / surface réelle bâtie, gardé entre 300 et 30 000 €/m² ;
- médiane par commune si au moins 20 ventes ; sinon, pour un arrondissement de Paris, Lyon ou
  Marseille, médiane de la ville entière ; sinon médiane de l'intercommunalité (EPCI) si elle en
  compte au moins 20 ; sinon pas de valeur.
Types : appartements (tous), appartements de 1 ou 2 pièces, de 3 pièces ou plus, maisons.
Sortie : ventes.json. Usage : python3 preparer_ventes.py
"""
import csv, gzip, io, json, statistics, urllib.request
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).parent
CACHE = ICI / "cache"; CACHE.mkdir(exist_ok=True)
ANNEES = [2024, 2025]
SEUIL = 20

def fichier(annee):
    f = CACHE / f"dvf{annee}.csv.gz"
    if not f.exists():
        url = f"https://files.data.gouv.fr/geo-dvf/latest/csv/{annee}/full.csv.gz"
        f.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})).read())
    return f

def ventes():
    """Renvoie (commune, type, pièces, prix au m²) pour chaque vente d'un seul logement."""
    for annee in ANNEES:
        with gzip.open(fichier(annee), "rt", encoding="utf-8") as fh:
            courant, lignes = None, []
            for r in csv.DictReader(fh):
                if r["id_mutation"] != courant:
                    if lignes: yield from traiter(lignes)
                    courant, lignes = r["id_mutation"], []
                lignes.append(r)
            if lignes: yield from traiter(lignes)

def traiter(lignes):
    if lignes[0]["nature_mutation"] != "Vente": return
    logements = [r for r in lignes if r["type_local"] in ("Maison", "Appartement")]
    if len(logements) != 1: return
    if any(r["type_local"].startswith("Local") for r in lignes): return
    r = logements[0]
    try:
        valeur, surface = float(r["valeur_fonciere"]), float(r["surface_reelle_bati"] or 0)
        pieces = int(r["nombre_pieces_principales"] or 0)
    except ValueError:
        return
    if valeur < 10000 or surface < 9: return
    prix = valeur / surface
    if not 300 <= prix <= 30000: return
    yield r["code_commune"], r["type_local"], pieces, prix

def ville_de(c):
    """Paris, Lyon ou Marseille pour un code d'arrondissement, sinon None."""
    return "Paris" if c.startswith("751") else "Lyon" if c.startswith("6938") else "Marseille" if c.startswith("132") else None

def main():
    loyers = csv.DictReader(io.StringIO((CACHE / "a.csv").read_bytes().decode("latin-1")), delimiter=";")
    epci_de = {r["INSEE_C"]: r["EPCI"] for r in loyers}
    dep_de = {c: c[:3] if c.startswith("97") else c[:2] for c in epci_de}
    par = {k: defaultdict(list) for k in ("a", "a12", "a3", "m")}
    hors = 0
    for commune, typ, pieces, prix in ventes():
        if commune not in epci_de: hors += 1; continue
        if typ == "Maison":
            par["m"][commune].append(prix)
        else:
            par["a"][commune].append(prix)
            if pieces in (1, 2): par["a12"][commune].append(prix)
            elif pieces >= 3: par["a3"][commune].append(prix)
    med = lambda l: round(statistics.median(l) / 10) * 10
    sortie = {"coms": {}, "deps": {}, "fr": {}}
    for k, d in par.items():
        epci = defaultdict(list); dep = defaultdict(list); ville = defaultdict(list); tout = []
        for c, l in d.items():
            epci[epci_de[c]] += l; dep[dep_de[c]] += l; tout += l
            if ville_de(c): ville[ville_de(c)] += l
        for c in epci_de:
            l = d.get(c, [])
            if len(l) >= SEUIL: v, z = med(l), "c"
            elif ville_de(c) and len(ville[ville_de(c)]) >= SEUIL: v, z = med(ville[ville_de(c)]), "v"
            elif len(epci[epci_de[c]]) >= SEUIL: v, z = med(epci[epci_de[c]]), "e"
            else: continue
            e = sortie["coms"].setdefault(c, {})
            e[k] = v; e[k + "z"] = z; e[k + "n"] = len(l)
        for dp, l in dep.items():
            if len(l) >= SEUIL: sortie["deps"].setdefault(dp, {})[k] = med(l)
        sortie["fr"][k] = med(tout)
    # format compact : code -> [a, m, a12, a3, nA, nM, zone a, zone m, zone a12, zone a3] (zone : c commune, v ville, e EPCI)
    compact = {c: [e.get("a"), e.get("m"), e.get("a12"), e.get("a3"), e.get("an", 0), e.get("mn", 0),
                   e.get("az"), e.get("mz"), e.get("a12z"), e.get("a3z")] for c, e in sortie["coms"].items()}
    (ICI / "ventes.json").write_text(json.dumps({"coms": compact, "deps": sortie["deps"], "fr": sortie["fr"],
                                                 "periode": "2024-2025"}, separators=(",", ":")))
    n = {k: sum(len(l) for l in d.values()) for k, d in par.items()}
    print("ventes retenues :", n, "| hors communes connues :", hors)
    print("communes avec valeur appart :", sum(1 for e in sortie["coms"].values() if "a" in e),
          "dont propre :", sum(1 for e in sortie["coms"].values() if e.get("az") == "c"),
          "| maison :", sum(1 for e in sortie["coms"].values() if "m" in e),
          "dont propre :", sum(1 for e in sortie["coms"].values() if e.get("mz") == "c"))
    print("France :", sortie["fr"])

if __name__ == "__main__":
    main()

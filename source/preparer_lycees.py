"""Lycées publics à voie professionnelle, par commune (annuaire de l'éducation, ministère de l'Éducation nationale).

On compte, dans chaque commune, les établissements publics de l'Éducation nationale où l'on enseigne
en voie professionnelle :
- lycées professionnels (nature 320) ;
- lycées polyvalents (nature 306, ou 310 lycée climatique) qui ont une voie professionnelle :
  « voie_professionnelle » à 1, ou une section d'enseignement professionnel (SEP, nature 334) rattachée.
Une SEP située dans la même commune que son lycée est comptée avec lui (une seule fois) ;
une SEP installée dans une autre commune compte dans la sienne.
Non comptés : établissements privés, lycées agricoles, maritimes et militaires (autres ministères).

Pour chaque lycée (même ministère, mêmes jeux de données ouverts) :
- élèves en voie professionnelle à la rentrée 2025 (effectifs des lycées professionnels, par établissement) ;
- IPS de la voie professionnelle, rentrée 2025-2026 (indice de position sociale des lycées) ;
- taux de réussite au bac pro, session 2025, et valeur ajoutée (indicateurs de résultat des lycées pro).
Les sections professionnelles des lycées polyvalents sont publiées sous le numéro du lycée.

Sortie : lycees.json {maj, ref, coms: {code commune: [identifiants]},
                      etab: {identifiant: [nom, 0 lycée pro | 1 polyvalent, élèves, IPS, réussite %, valeur ajoutée, longitude, latitude]}}.
Usage : python3 preparer_lycees.py (après preparer_donnees.py)
"""
import json, subprocess
from collections import defaultdict
from pathlib import Path

ICI = Path(__file__).parent
CACHE = ICI / "cache"; CACHE.mkdir(exist_ok=True)
CHAMPS = ("identifiant_de_l_etablissement,nom_etablissement,type_etablissement,statut_public_prive,code_commune,"
          "nom_commune,code_departement,code_nature,voie_professionnelle,etablissement_mere,"
          "type_rattachement_etablissement_mere,etat,ministere_tutelle,date_maj_ligne,latitude,longitude")
URL = ("https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/exports/json"
       f"?select={CHAMPS}&where=type_etablissement%20in%20(%22Lyc%C3%A9e%22,%22EREA%22)")
EN = "MINISTERE DE L'EDUCATION NATIONALE"
API = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/"
IPS_AN, EFF_AN, RES_AN = "2025-2026", "2025", "2025"
IPS = API + f"fr-en-ips-lycees-ap2023/exports/json?select=uai,ips_voie_pro&where=rentree_scolaire%3D%22{IPS_AN}%22"
EFF = API + f"fr-en-lycee_pro-effectifs-niveau-sexe-lv/exports/json?select=numero_lycee,nombre_d_eleves&refine=rentree_scolaire:{EFF_AN}"
RES = API + f"fr-en-indicateurs-de-resultat-des-lycees-pro_v2/exports/json?select=uai,taux_reu_total,va_reu_total&refine=annee:{RES_AN}"

def telecharger(url, nom):
    f = CACHE / nom
    if not f.exists():
        # curl plutôt qu'urllib : le certificat du site n'est pas reconnu par le Python du système
        subprocess.run(["curl", "-sSfL", "-A", "Mozilla/5.0", "-o", str(f), url], check=True)
    return json.loads(f.read_text())

def nombre(v):
    try: return round(float(v), 1)
    except (TypeError, ValueError): return None

def court(nom):
    for long, abr in (("Lycée professionnel ", "LP "), ("Lycée polyvalent ", "LPO "),
                      ("Section d'enseignement professionnel ", "SEP "), ("Section d'Enseignement Professionnel ", "SEP ")):
        if nom.startswith(long): return abr + nom[len(long):].strip()
    return nom.strip()

def main():
    tous = telecharger(URL, "annuaire_lycees.json")
    ips = {r["uai"]: nombre(r["ips_voie_pro"]) for r in telecharger(IPS, f"ips_lycees_{IPS_AN}.json")}
    eff = {r["numero_lycee"]: r["nombre_d_eleves"] for r in telecharger(EFF, f"effectifs_lp_{EFF_AN}.json")}
    res = {r["uai"]: (nombre(r["taux_reu_total"]), nombre(r["va_reu_total"])) for r in telecharger(RES, f"resultats_lp_{RES_AN}.json")}
    par_id = {x["identifiant_de_l_etablissement"]: x for x in tous}
    pub = [x for x in tous if x["statut_public_prive"] == "Public" and x["ministere_tutelle"] == EN and x["etat"] == "OUVERT"]
    lieux = defaultdict(dict)   # commune -> {identifiant: (type, nom)}
    rattache = {}               # identifiant retenu -> SEP rattachée (chiffres publiés parfois sous son numéro)
    for x in pub:
        n = x["code_nature"]
        if n == 320:
            lieux[x["code_commune"]][x["identifiant_de_l_etablissement"]] = ("lp", court(x["nom_etablissement"]))
        elif n in (306, 310) and x["voie_professionnelle"] == "1":
            lieux[x["code_commune"]][x["identifiant_de_l_etablissement"]] = ("lpo", court(x["nom_etablissement"]))
    for x in pub:
        if x["code_nature"] != 334: continue
        m = par_id.get(x["etablissement_mere"])
        if m and m["code_commune"] == x["code_commune"]:
            ident, typ, nom = m["identifiant_de_l_etablissement"], "lp" if m["code_nature"] == 320 else "lpo", court(m["nom_etablissement"])
        else:
            ident, typ, nom = x["identifiant_de_l_etablissement"], "lpo", court(x["nom_etablissement"])
        lieux[x["code_commune"]].setdefault(ident, (typ, nom))
        rattache.setdefault(ident, x["identifiant_de_l_etablissement"])
    codes = {c[0] for c in json.loads((ICI / "data.json").read_text())["coms"]}
    def val(table, ident):
        v = table.get(ident)
        return v if v is not None else table.get(rattache.get(ident))
    coms, etab, hors = {}, {}, 0
    for code, d in sorted(lieux.items()):
        if code not in codes: hors += 1; continue
        ids = sorted(d, key=lambda i: (d[i][0] != "lp", d[i][1]))
        coms[code] = ids
        for i in ids:
            r = val(res, i) or (None, None)
            x = par_id[i]
            pos = [round(x["longitude"], 4), round(x["latitude"], 4)] if x.get("longitude") is not None else [None, None]
            etab[i] = [d[i][1], 0 if d[i][0] == "lp" else 1, val(eff, i), val(ips, i), r[0], r[1], *pos]
    v = [e[3] for e in etab.values() if e[3] is not None]
    ref = {"ips": round(sum(v) / len(v), 1), "ips_an": IPS_AN, "eff_an": EFF_AN, "res_an": RES_AN}
    maj = max(x["date_maj_ligne"] for x in tous if x.get("date_maj_ligne"))
    (ICI / "lycees.json").write_text(json.dumps({"maj": maj, "ref": ref, "coms": coms, "etab": etab}, ensure_ascii=False, separators=(",", ":")))
    n = lambda k: sum(1 for e in etab.values() if e[k] is not None)
    print(f"{len(coms)} communes, {sum(e[1] == 0 for e in etab.values())} lycées pro, {sum(e[1] == 1 for e in etab.values())} lycées polyvalents ;"
          f" élèves {n(2)}, IPS {n(3)}, résultats {n(4)} ; IPS moyen {ref['ips']} ;"
          f" {hors} communes hors carte (outre-mer non couvert) ; données du {maj}")

if __name__ == "__main__":
    main()

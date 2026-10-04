# Louer ou acheter en France, commune par commune

Carte interactive des loyers et des prix de vente des logements en France, réalisée pour la chaîne **Maths·Sciences LP**. Un bouton « Louer / Acheter » change toute la page.

Page en ligne : https://maths-sciences-lp.github.io/carte-loyers/

## Ce que montre la carte

- le prix au m² par département et par commune (appartements, maisons) ;
- le loyer par mois d'un appartement de 1 ou 2 pièces (37 m²), de 3 pièces ou plus (72 m²) et d'une maison (92 m²), pour les 5 plus grandes villes de chaque département ;
- un découpage au choix : régions, départements ou académies ;
- un filtre « mon budget » et la comparaison de deux communes ;
- en mode Acheter : prix de vente médian au m² et prix estimé des mêmes logements ;
- « Je gagne… » : le budget de loyer réglé sur un tiers du salaire net ;
- dans les bulles et la comparaison : niveau de vie médian, part du loyer d'un 1 ou 2 pièces dans ce revenu, tension du marché (zonage ABC), loyers plafonnés, logements vacants, gare la plus proche et services sur place (médecin, pharmacie, école, collège, supermarché, boulangerie).

Le loyer par mois est calculé ainsi : prix au m² publié par la source × surface du logement de référence de la source.

## Sources

- Loyers : « Carte des loyers – Indicateurs de loyers d'annonce par commune en 2025 », ANIL et ministère chargé du Logement, sur data.gouv.fr (Licence Ouverte 2.0). Loyers d'annonce charges comprises, logements non meublés, annonces leboncoin et SeLoger publiées jusqu'au 30 septembre 2025.
- Populations : INSEE, via geo.api.gouv.fr.
- Contours des communes et des départements : IGN Admin Express, via Etalab et france-geojson (Licence Ouverte).

- Prix de vente : « Demandes de valeurs foncières géolocalisées » (DGFiP, Etalab, Licence Ouverte), ventes 2024 et 2025. Ventes d'un seul logement, prix au m² = prix ÷ surface habitable, médiane par commune si au moins 20 ventes, sinon ville entière (Paris, Lyon, Marseille) puis intercommunalité. Alsace, Moselle et Mayotte ne sont pas couvertes par la source.

- Niveau de vie médian : INSEE, Filosofi 2021 (dernière édition), géographie 2025.
- Tension du marché : zonage ABC du ministère de la Transition écologique, en vigueur au 26 juin 2026.
- Logements vacants : LOVAC (ministère, Cerema), parc privé au 1er janvier 2024.
- Gares : « Gares de voyageurs » (SNCF, octobre 2026), distance à vol d'oiseau depuis le centre de la commune ; grande gare nationale = catégorie A. Corse et outre-mer non couverts par ce fichier.
- Services sur place : INSEE, base permanente des équipements 2025.
- Régions et académies : référentiel géographique du ministère de l'Enseignement supérieur et de la Recherche ; valeur d'un groupe = moyenne de ses communes pondérée par la population.
- Loyers plafonnés : liste de service-public.gouv.fr (fiche F1314) vérifiée le 1er août 2026 ; dispositif prévu jusqu'au 24 novembre 2026, à revérifier ensuite (liste dans `preparer_indicateurs.py`).

Les cartes des loyers des différentes années ne sont pas comparables entre elles (avertissement de la source).

## Mettre à jour la carte

Les fichiers de fabrication sont dans `source/` :

- `preparer_donnees.py` télécharge les données officielles et produit `data.json`, `geo.json`, `communes.json` et `villes.json` ;
- `preparer_ventes.py` télécharge les ventes (DVF) et produit `ventes.json` (à lancer après `preparer_donnees.py`) ;
- `preparer_revenus.py` (INSEE Filosofi) produit `revenus.json` ;
- `preparer_indicateurs.py` (zonage ABC, logements vacants, encadrement) produit `indicateurs.json` (après `preparer_donnees.py`) ;
- `preparer_services.py` (gares SNCF, équipements INSEE) produit `services.json` (après `preparer_donnees.py`) ;
- `preparer_zones.py` (académies, régions et leurs frontières) produit `zones.json` (après `preparer_donnees.py`) ;
- `template.html` contient la page (mise en forme et code) ;
- `assembler.py` réunit le tout dans `index.html`.

```bash
cd source
python3 preparer_donnees.py
python3 preparer_ventes.py
python3 preparer_revenus.py
python3 preparer_indicateurs.py
python3 preparer_services.py
python3 preparer_zones.py
python3 assembler.py
```

Pour une nouvelle édition de la carte des loyers, remplacer les adresses des fichiers CSV en tête de `preparer_donnees.py` ; pour de nouvelles années de ventes, changer `ANNEES` dans `preparer_ventes.py` ; puis relancer les commandes.

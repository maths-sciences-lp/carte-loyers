# Louer ou acheter en France, commune par commune

Carte interactive des loyers et des prix de vente des logements en France, réalisée pour la chaîne **Maths·Sciences LP**. Un bouton « Louer / Acheter » change toute la page.

Page en ligne : https://maths-sciences-lp.github.io/carte-loyers/

## Ce que montre la carte

- le prix au m² par département et par commune (appartements, maisons) ;
- le loyer par mois d'un appartement de 1 ou 2 pièces (37 m²), de 3 pièces ou plus (72 m²) et d'une maison (92 m²), pour les 5 plus grandes villes de chaque département ;
- un filtre « mon budget » et la comparaison de deux communes ;
- en mode Acheter : prix de vente médian au m² et prix estimé des mêmes logements.

Le loyer par mois est calculé ainsi : prix au m² publié par la source × surface du logement de référence de la source.

## Sources

- Loyers : « Carte des loyers – Indicateurs de loyers d'annonce par commune en 2025 », ANIL et ministère chargé du Logement, sur data.gouv.fr (Licence Ouverte 2.0). Loyers d'annonce charges comprises, logements non meublés, annonces leboncoin et SeLoger publiées jusqu'au 30 septembre 2025.
- Populations : INSEE, via geo.api.gouv.fr.
- Contours des communes et des départements : IGN Admin Express, via Etalab et france-geojson (Licence Ouverte).

- Prix de vente : « Demandes de valeurs foncières géolocalisées » (DGFiP, Etalab, Licence Ouverte), ventes 2024 et 2025. Ventes d'un seul logement, prix au m² = prix ÷ surface habitable, médiane par commune si au moins 20 ventes, sinon ville entière (Paris, Lyon, Marseille) puis intercommunalité. Alsace, Moselle et Mayotte ne sont pas couvertes par la source.

Les cartes des loyers des différentes années ne sont pas comparables entre elles (avertissement de la source).

## Mettre à jour la carte

Les fichiers de fabrication sont dans `source/` :

- `preparer_donnees.py` télécharge les données officielles et produit `data.json`, `geo.json`, `communes.json` et `villes.json` ;
- `preparer_ventes.py` télécharge les ventes (DVF) et produit `ventes.json` (à lancer après `preparer_donnees.py`) ;
- `template.html` contient la page (mise en forme et code) ;
- `assembler.py` réunit le tout dans `index.html`.

```bash
cd source
python3 preparer_donnees.py
python3 preparer_ventes.py
python3 assembler.py
```

Pour une nouvelle édition de la carte des loyers, remplacer les adresses des fichiers CSV en tête de `preparer_donnees.py` ; pour de nouvelles années de ventes, changer `ANNEES` dans `preparer_ventes.py` ; puis relancer les trois commandes.

# Thesis
# DATA_2025 — Analyse hédonique des prix immobiliers à Paris (75)

Ce projet porte sur l'**analyse économétrique des prix de l'immobilier résidentiel à Paris** sur la période 2018–2024, à partir des données DVF (*Demandes de Valeurs Foncières*) géolocalisées publiées par l'État.  
L'objectif est d'estimer l'effet de caractéristiques spatiales et environnementales sur les prix au m² : proximité des gares, niveau de bruit, criminalité, qualité des lycées, distance au centre, tissu urbain (carreaux INSEE 200 m), DPE, etc.  
La méthode centrale est un **modèle de mélange gaussien estimé par algorithme EM stochastique** (inspiré de travaux en économétrie spatiale), qui permet d'identifier des **classes latentes** d'arrondissements avec des niveaux de prix différenciés.

---

## Structure du projet

```
DATA_2025/
├── Recupere/           # Consolidation des données annuelles (DVF + variables spatiales)
├── Lille/              # Algorithme EM stochastique pour l'estimation des classes latentes
├── Carreaux/
│   ├── code/           # Jointure spatiale DVF ↔ carreaux INSEE 200 m + calcul d'indicateurs
│   └── resultats/      # Sorties : shapefiles, CSV enrichis
├── Bruit/              # Jointure DVF ↔ données de bruit (LDEN)
├── Gares/              # Jointure DVF ↔ gares RAIL/METRO (trafic, correspondances)
├── Crime/              # Jointure DVF ↔ criminalité (cambriolages, taux par zone)
├── DPE/                # Jointure DVF ↔ DPE (diagnostic de performance énergétique)
├── Centre/             # Calcul distance au centre (Place Dauphine)
├── Lycees/ & Meilleurs/# Jointure DVF ↔ lycées (tous / meilleurs)
├── Quartiers/          # Jointure DVF ↔ quartiers administratifs Paris
├── Bootstrap/          # Bootstrap sur les paramètres EM estimés
├── Simulations/        # Données consolidées pour les estimations
└── Visualisation/      # Cartes et graphiques
```

---

## Description des codes principaux

### 1. `Recupere/Recupere_V4.py` — Consolidation des données annuelles

**Ce que fait ce code :**  
Pour chaque année de 2018 à 2024, ce script charge le fichier DVF géolocalisé du département 75, puis lui joint (via `id_mutation` + `num_ordre`) l'ensemble des variables spatiales issues des prétraitements SIG réalisés en amont :

| Source jointe         | Variable produite         | Pourquoi                                                   |
|-----------------------|---------------------------|------------------------------------------------------------|
| Bruit (LDEN)          | `gridcode`, `Classe`      | Exposition sonore autour du bien                           |
| Gares RATP/SNCF       | `dist_gare`, `Trafic`, `nb_correspondances` | Accessibilité en transports          |
| Lycées (tous)         | `dist_lycee`              | Proximité à l'offre scolaire générale                      |
| Meilleurs lycées      | `dist_m`                  | Proximité aux lycées d'excellence                          |
| Centre de Paris       | `dist_centre`             | Distance à la Place Dauphine (centre historique)           |
| Criminalité           | `C51_68` … `C186_226`     | Classes de taux de cambriolage (infra-communal 2018)       |
| Quartiers admin.      | `c_qu`                    | Code quartier INSEE                                        |
| Kebabs                | `dist_kebabs`             | Variable expérimentale d'aménités / nuisances de voisinage |

Le résultat (`joint<AAAA>`) est un DataFrame pandas consolidé prêt pour l'estimation économétrique, avec toutes les variables d'un bien immobilier dans une seule ligne.

**Pourquoi cette approche :** les sources de données proviennent de traitements SIG distincts (QGIS / Python GeoPandas). Ce script fait office de colle entre tous ces fichiers produits séparément.

---

### 2. `Lille/lille_K2_python_BIC.py` — Algorithme EM stochastique (modèle de mélange)

**Ce que fait ce code :**  
Ce script est le cœur du modèle économétrique. Il implémente un **algorithme EM stochastique** pour estimer un modèle de mélange gaussien de la forme :

$$\ln(P_i) = X_i \beta + g_{k(i)} + \varepsilon_i, \quad \varepsilon_i \sim \mathcal{N}(0, \sigma^2)$$

où $k(i) \in \{1,\ldots,K\}$ est la **classe latente** de l'observation $i$, et $d_{c,k} = P(k(i)=k \mid \text{arrondissement } c)$ est la probabilité a priori d'appartenir à la classe $k$ dans l'arrondissement $c$.

**Variables explicatives :** années (effets fixes temporels), nombre de pièces, surface, log-surface, dépendance, distances (centre, lycées, meilleurs lycées), proximité gare (<200 m / >300 m), niveau de trafic, nombre de correspondances, classes de bruit, criminalité, surface et nombre de pièces moyens dans le quartier.

**Algorithme (stochastique EM) :**
1. **E-step :** calcul des probabilités a posteriori d'appartenir à chaque classe, par observation.
2. **Stochastic step :** tirage multinomial (`NbSimu` simulations par observation) pour simuler l'appartenance aux classes.
3. **M-step :** régression OLS pondérée (équations normales) pour mettre à jour $\beta$, $g_k$ et $\sigma^2$.
4. **Mise à jour des priors** $d_{c,k}$ par fréquence empirique au sein de chaque arrondissement.

Conversion depuis le langage **Gauss** vers Python (`numpy` / `scipy`). Fonctionne pour $K \geq 2$ classes.

---

### 3. `Lille/lille_bic.py` — Sélection du nombre de classes par critère BIC

**Ce que fait ce code :**  
Ce script orchestre la recherche du nombre optimal de classes latentes $K$ en faisant tourner `run_em` (importé depuis `lille_K2_python_BIC.py`) pour $K = 2, 3, \ldots, 15$, puis en calculant le **BIC** (*Bayesian Information Criterion*) pour chaque valeur de $K$ :

$$\text{BIC}(K) = -2 \ln \hat{L} + \ln(n) \cdot df_K$$

avec $df_K = p_\beta + K + 20(K-1)$ (coefficients de régression + constantes de classes + probabilités a priori par arrondissement).

Pour chaque $K$, un fichier texte de résultats est sauvegardé (`resultats_lille_bicK={K}.txt`) contenant le BIC, la matrice $d$ par arrondissement, les coefficients $\beta$ et les constantes $g_k$.

**Pourquoi :** le BIC pénalise la complexité du modèle, évitant le sur-ajustement. Il permet de choisir le $K$ optimal de façon rigoureuse.

---

### 4. `Carreaux/code/carreaux.py` — Filtrage de la grille INSEE 200 m à Paris

**Ce que fait ce code :**  
À partir du shapefile national des carreaux INSEE 200 m (`carreaux_200m_met.shp`), ce script :
1. Charge les limites des quartiers parisiens (`quartier_paris.shp`).
2. Reprojette les deux couches dans un système de coordonnées commun si nécessaire.
3. Effectue une **jointure spatiale** (intersection) pour ne conserver que les carreaux qui intersectent Paris intra-muros.
4. Déduplique les carreaux présents dans plusieurs quartiers.
5. Sauvegarde le résultat dans `carreaux/resultats/carreaux_paris.shp`.

Utilise `GeoPandas` pour les opérations géospatiales et `pyogrio` pour lire les métadonnées du shapefile sans le charger intégralement en mémoire.

---

### 5. `Carreaux/code/carreaux_2018.py` — Jointure spatiale DVF 2018 ↔ carreaux Paris

**Ce que fait ce code :**  
Ce script joint spatialement les transactions DVF 2018 (points GPS) avec les carreaux INSEE 200 m de Paris (polygones) afin d'affecter à chaque bien immobilier son carreau de résidence.

Étapes :
1. Lecture du DVF 2018 (CSV) → création d'un `GeoDataFrame` avec les coordonnées WGS84.
2. Lecture du shapefile `carreaux_paris.shp` produit par `carreaux.py`.
3. Reprojection des deux couches en **Lambert 93 (EPSG:2154)** — système officiel français, indispensable pour les distances métriques.
4. `sjoin` (jointure spatiale gauche) pour identifier, pour chaque transaction, le carreau INSEE correspondant.
5. Export du résultat en CSV (`dvf752018Carreaux.csv`).

Il existe une version équivalente par année (`carreaux_2019.py` … `carreaux_2024.py`).

---

### 6. `Carreaux/code/carreaux_indicateurs.py` — Calcul d'indicateurs socio-démographiques par carreau

**Ce que fait ce code :**  
Pour chaque année de 2018 à 2024, ce script lit le fichier `dvf75{AAAA}Carreaux.csv` produit précédemment et calcule, au niveau du carreau affecté à chaque transaction, une série d'**indicateurs socio-démographiques INSEE** :

| Indicateur calculé                          | Source INSEE (carreau)                    | Intérêt pour le modèle hédonique         |
|---------------------------------------------|-------------------------------------------|------------------------------------------|
| `pct_individus_jeunes_lt18`                 | `ind_0_3 + ind_4_5 + ind_6_10 + ind_11_17` | Structure démographique locale           |
| `pct_menages_pauvres`                       | `men_pauv / men`                          | Niveau socio-économique du voisinage     |
| `pct_menages_proprietaires`                 | `men_prop / men`                          | Mix locataires/propriétaires             |
| `nb_individus` & `densite_ind_km2`          | `ind / 0.04 km²`                          | Densité résidentielle                    |
| `pct_logements_apres_1990_sans_sociaux`     | `log_ap90 / total_logements`              | Vétusté / modernité du parc immobilier   |

Les divisions par zéro sont gérées proprement (`safe_pct` / `safe_pct_zero_when_den_zero`). Le fichier de sortie `dvf75{AAAA}Carreaux_indicateurs.csv` est prêt à être incorporé dans les données d'estimation.

---

## Données sources

| Donnée                    | Source                         | Granularité       |
|---------------------------|--------------------------------|-------------------|
| DVF géolocalisé           | data.gouv.fr / Etalab          | Transaction       |
| Carreaux 200 m            | INSEE Filosofi                 | 200 m × 200 m     |
| Bruit LDEN                | Bruitparif / PPBE              | Zone SIG          |
| Gares                     | IDFM / SNCF open data          | Point             |
| Criminalité infra-communale| SSMSI / Ministère de l'Intérieur | Quartier IRIS    |
| DPE                       | ADEME open data                | Logement          |
| Lycées / Meilleurs lycées | Open data Éducation Nationale  | Établissement     |
| Quartiers parisiens       | Ville de Paris open data       | Quartier admin.   |

---

## Dépendances Python

```
pandas
numpy
scipy
statsmodels
geopandas
pyogrio
```

---

## Auteurs

Projet réalisé dans le cadre d'une recherche en économétrie immobilière.  
Codes développés et adaptés par **Marc Chkeiban** (avec contributions de T. Kamionka).

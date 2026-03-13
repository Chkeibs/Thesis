# DATA_2025 — Hedonic Analysis of Residential Property Prices in Paris (75)

This project focuses on the **econometric analysis of residential property prices in Paris** over the 2018–2024 period, based on geolocated DVF (*Demandes de Valeurs Foncières*) data published by the French State.  
The objective is to estimate the effect of spatial and environmental characteristics on price per square meter: proximity to train/metro stations, noise levels, crime, school quality, distance to the city centre, urban fabric (INSEE 200 m grid cells), energy performance certificates (DPE), etc.  
The core method is a **Gaussian mixture model estimated via a stochastic EM algorithm** (inspired by spatial econometrics research), which identifies **latent classes** of arrondissements with differentiated price levels.


## Description of Main Scripts

### 1. `Recupere/Recupere_V4.py` — Annual Data Consolidation

**What this script does:**  
For each year from 2018 to 2024, this script loads the geolocated DVF file for département 75, then joins (via `id_mutation` + `num_ordre`) all spatial variables produced by upstream GIS preprocessing:

| Joined source         | Variable produced         | Why                                                        |
|-----------------------|---------------------------|------------------------------------------------------------|
| Noise (LDEN)          | `gridcode`, `Classe`      | Noise exposure around the property                         |
| RATP/SNCF stations    | `dist_gare`, `Trafic`, `nb_correspondances` | Public transport accessibility          |
| Schools (all)         | `dist_lycee`              | Proximity to general schooling supply                      |
| Top schools           | `dist_m`                  | Proximity to elite high schools                            |
| Paris city centre     | `dist_centre`             | Distance to Place Dauphine (historic centre)               |
| Crime                 | `C51_68` … `C186_226`     | Burglary rate classes (infra-communal 2018)                |
| Admin. districts      | `c_qu`                    | INSEE district code                                        |
| Kebabs                | `dist_kebabs`             | Experimental amenity/nuisance variable (neighbourhood)     |

The output (`joint<YEAR>`) is a consolidated pandas DataFrame ready for econometric estimation, with all variables for a property in a single row.

**Why this approach:** the data sources come from separate GIS pipelines (QGIS / Python GeoPandas). This script acts as the glue between all these independently produced files.

---

### 2. `Lille/lille_K2_python_BIC.py` — Stochastic EM Algorithm (Mixture Model)

**What this script does:**  
This script is the core of the econometric model. It implements a **stochastic EM algorithm** to estimate a Gaussian mixture model of the form:

$$\ln(P_i) = X_i \beta + g_{k(i)} + \varepsilon_i, \quad \varepsilon_i \sim \mathcal{N}(0, \sigma^2)$$

where $k(i) \in \{1,\ldots,K\}$ is the **latent class** of observation $i$, and $d_{c,k} = P(k(i)=k \mid \text{arrondissement } c)$ is the prior probability of belonging to class $k$ in arrondissement $c$.

**Explanatory variables:** year fixed effects, number of rooms, floor area, log-area, outbuildings, distances (centre, schools, top schools), station proximity (<200 m / >300 m), traffic level, number of connections, noise classes, crime, average floor area and average number of rooms in the district.

**Algorithm (stochastic EM):**
1. **E-step:** compute the posterior probability of class membership for each observation.
2. **Stochastic step:** multinomial draw (`NbSimu` simulations per observation) to simulate class assignments.
3. **M-step:** weighted OLS regression (normal equations) to update $\beta$, $g_k$ and $\sigma^2$.
4. **Prior update:** $d_{c,k}$ updated as the empirical frequency within each arrondissement.

Ported from **Gauss** to Python (`numpy` / `scipy`). Works for $K \geq 2$ classes.

---

### 3. `Lille/lille_bic.py` — Optimal Number of Classes via BIC

**What this script does:**  
This script searches for the optimal number of latent classes $K$ by running `run_em` (imported from `lille_K2_python_BIC.py`) for $K = 2, 3, \ldots, 15$, then computing the **BIC** (*Bayesian Information Criterion*) for each value of $K$:

$$\text{BIC}(K) = -2 \ln \hat{L} + \ln(n) \cdot df_K$$

with $df_K = p_\beta + K + 20(K-1)$ (regression coefficients + class intercepts + prior probabilities per arrondissement).

For each $K$, a text result file is saved (`resultats_lille_bicK={K}.txt`) containing the BIC, the $d$ matrix by arrondissement, the $\beta$ coefficients and the class intercepts $g_k$.

**Why:** the BIC penalises model complexity, preventing overfitting. It allows the optimal $K$ to be chosen rigorously.

---

### 4. `Carreaux/code/carreaux.py` — Filtering the INSEE 200 m Grid to Paris

**What this script does:**  
Starting from the national INSEE 200 m grid shapefile (`carreaux_200m_met.shp`), this script:
1. Loads the boundaries of Parisian districts (`quartier_paris.shp`).
2. Reprojects both layers to a common coordinate system if necessary.
3. Performs a **spatial join** (intersection) to retain only the grid cells that intersect intra-muros Paris.
4. Deduplicates cells that appear in multiple districts.
5. Saves the result to `carreaux/resultats/carreaux_paris.shp`.

Uses `GeoPandas` for geospatial operations and `pyogrio` to read shapefile metadata without loading the full file into memory.

---

### 5. `Carreaux/code/carreaux_2018.py` — Spatial Join DVF 2018 ↔ Paris Grid Cells

**What this script does:**  
This script spatially joins DVF 2018 transactions (GPS points) with the Paris INSEE 200 m grid cells (polygons) in order to assign each property to its residential grid cell.

Steps:
1. Read DVF 2018 (CSV) → create a `GeoDataFrame` with WGS84 coordinates.
2. Read the `carreaux_paris.shp` shapefile produced by `carreaux.py`.
3. Reproject both layers to **Lambert 93 (EPSG:2154)** — the official French metric CRS, required for accurate distance calculations.
4. `sjoin` (left spatial join) to identify, for each transaction, the corresponding INSEE grid cell.
5. Export the result to CSV (`dvf752018Carreaux.csv`).

An equivalent version exists for each year (`carreaux_2019.py` … `carreaux_2024.py`).

---

### 6. `Carreaux/code/carreaux_indicateurs.py` — Socio-demographic Indicators per Grid Cell

**What this script does:**  
For each year from 2018 to 2024, this script reads the `dvf75{YEAR}Carreaux.csv` file produced previously and computes, at the grid-cell level assigned to each transaction, a set of **INSEE socio-demographic indicators**:

| Computed indicator                          | INSEE source (grid cell)                  | Role in the hedonic model                |
|---------------------------------------------|-------------------------------------------|------------------------------------------|
| `pct_individus_jeunes_lt18`                 | `ind_0_3 + ind_4_5 + ind_6_10 + ind_11_17` | Local demographic structure            |
| `pct_menages_pauvres`                       | `men_pauv / men`                          | Socio-economic level of the neighbourhood|
| `pct_menages_proprietaires`                 | `men_prop / men`                          | Owner/tenant mix                         |
| `nb_individus` & `densite_ind_km2`          | `ind / 0.04 km²`                          | Residential density                      |
| `pct_logements_apres_1990_sans_sociaux`     | `log_ap90 / total_logements`              | Age / modernity of the housing stock     |

Division by zero is handled cleanly (`safe_pct` / `safe_pct_zero_when_den_zero`). The output file `dvf75{YEAR}Carreaux_indicateurs.csv` is ready to be incorporated into the estimation dataset.

---

### 7. `kebabs/kebabs-1.py` — Web Scraping of Paris Kebab Shops

**What this script does:**  
This script automatically collects the list of all kebab establishments located in Paris intra-muros from the website `kebab-frites.com`. It proceeds in two stages:

1. **Sitemap parsing:** the script fetches the site's XML sitemap (handling both index sitemaps and standard URL sitemaps, as well as gzip-compressed responses), then filters the URLs corresponding to individual establishment pages (pattern `/kebab/<city>-<name>.html`, excluding city-level index pages).
2. **Page scraping:** for each filtered URL, it downloads the HTML page, extracts the establishment name (`<h1>` tag) and the address, and filters exclusively for Paris postal codes (75001–75020) using a regular expression. The arrondissement is also extracted when present.

The result is saved to `kebabs_paris_from_sitemap.csv` with the columns: `name`, `arrondissement`, `address`, `url`.

**Why:** the distance to the nearest kebab shop (`dist_kebabs`) is used as an experimental spatial amenity/nuisance variable in the hedonic model — a proxy for a certain type of neighbourhood commercial environment.

---

### 8. `kebabs/geocode_kebabs-1.py` — Geocoding Kebab Shop Addresses

**What this script does:**  
This script takes the `kebabs_paris_from_sitemap.csv` file produced by the scraper and geocodes each address (i.e. converts a textual address into geographic coordinates), adding `latitude` and `longitude` columns.

The geocoding uses a two-step strategy with automatic fallback:
1. **Primary:** Nominatim API (OpenStreetMap), restricted to France (`countrycodes=fr`). An email address can be provided via the `NOMINATIM_EMAIL` environment variable to comply with the API's usage policy.
2. **Fallback:** if Nominatim fails (HTTP error or exception), the script falls back to the French **BAN** (*Base Adresse Nationale*) API (`api-adresse.data.gouv.fr`).

A 1-second delay is respected between each request to comply with the APIs' rate limits. The output is saved to `kebabs_paris_with_coords.csv`.

---

### 9. `kebabs/add_lambert93_columns-1.py` — Conversion to Lambert 93

**What this script does:**  
This script takes the geocoded file `kebabs_paris_with_coords.csv` and converts the WGS84 geographic coordinates (`latitude`, `longitude`) to the **Lambert 93 projected coordinate system (EPSG:2154)** using `pyproj`, adding two new columns: `lambert93_x` and `lambert93_y`.

The transformation is done via a `Transformer` object (always with `always_xy=True` to avoid axis order ambiguity). Rows with missing or invalid coordinates are handled gracefully (empty strings in the output columns). The final file `kebabs_paris_with_coords_lambert93.csv` is the one used in the main DVF processing pipeline to compute the distance `dist_kebabs` for each property transaction.

**Why Lambert 93:** all distance calculations in the project are performed in this metric projected CRS (same as all other GIS layers), ensuring consistency and accuracy in metre-based distance computations.

---

### 10. `Visualisation/map_paris_features.py` — Interactive Multi-layer Map of Paris

**What this script does:**  
This script builds an interactive HTML map of Paris (Folium/Leaflet) for a given year (`--year`), combining transaction-level and zone-level layers from the project pipeline.

It automatically loads (when available) the yearly feature files and adds:
- Heatmaps: noise, crime, station traffic, DPE, optional price CSV.
- Point layers: stations, high schools, kebab shops, DVF transactions.
- Polygon/outline layers: arrondissements, quartiers, full Paris 200 m INSEE grid.
- Choropleths: average price per m² by arrondissement and by quartier.

The output is saved to `Visualisation/resultats/paris_carte_features_<YEAR>.html`.

**Main inputs used by year (`_year_paths`)**

| Logical layer | File pattern |
|---------------|--------------|
| Noise | `Bruit/dvf75{YEAR}Bruit.csv` |
| Crime | `Crime/dvf75{YEAR}Crime.csv` |
| High schools | `Lycees/dvf75{YEAR}Lycees.csv` |
| Stations | `Gares/dvf75{YEAR}Gares.csv` |
| DPE | `DPE/dvf75{YEAR}Dpe.csv` |
| City centre distance | `Centre/dvf75{YEAR}Centre.csv` |
| District assignment | `Quartiers/dvf75{YEAR}Quartier.csv` |
| Grid-cell indicators/coords | `Carreaux/resultats/dvf75{YEAR}Carreaux_indicateurs.csv` |
| DVF prepared base | `DVFGEO/{YEAR}/75/dvf{YEAR}75_prepare.csv` |

**Additional static/default inputs:**
- Paris quartiers shapefile: `Quartiers/quartier_paris/quartier_paris.shp` (with associated `.dbf/.shx/.prj`).
- National INSEE 200 m grid shapefile: `Carreaux/data/carreaux_200m_met.shp`.
- Kebab points CSV (default CLI path): `kebabs_paris_with_coords_lambert93 (1).csv`.

**Quick role of each input file (one sentence each):**
- `Visualisation/map_paris_features.py`: main script that assembles all layers and exports the final interactive HTML map.
- `Visualisation/requirements.txt`: Python dependencies needed to run the visualization script.
- `Bruit/dvf75{YEAR}Bruit.csv`: yearly noise-enriched transaction points used for the noise heatmap.
- `Crime/dvf75{YEAR}Crime.csv`: yearly crime-enriched transaction points used for the crime heatmap.
- `Lycees/dvf75{YEAR}Lycees.csv`: yearly transaction points with lycée proximity used for school point overlay.
- `Gares/dvf75{YEAR}Gares.csv`: yearly transaction/station-enriched data used for station traffic heatmap and station points.
- `DPE/dvf75{YEAR}Dpe.csv`: yearly DPE attributes merged on mutation keys to build the DPE layer.
- `Centre/dvf75{YEAR}Centre.csv`: yearly distance-to-centre data used for optional zonal intensity metrics.
- `Quartiers/dvf75{YEAR}Quartier.csv`: yearly arrondissement/quartier identifiers per transaction used in zonal aggregations.
- `Carreaux/resultats/dvf75{YEAR}Carreaux_indicateurs.csv`: yearly grid-cell indicators and coordinates used for density/poverty layers and DPE coordinate merge.
- `DVFGEO/{YEAR}/75/dvf{YEAR}75_prepare.csv`: base yearly DVF transaction file used for price choropleths and transaction points.
- `Quartiers/quartier_paris/quartier_paris.shp` (+ sidecar files): Paris district geometries used for quartier and arrondissement boundaries.
- `Carreaux/data/carreaux_200m_met.shp` (+ sidecar files): INSEE 200 m grid geometries used for full-grid overlays and socio-demographic layers.
- `kebabs_paris_with_coords_lambert93 (1).csv`: geocoded kebab points shown as a dedicated point layer.

**Dependency bundle prepared in this repository:**
- `Visualisation/dependances_map_paris/`: folder that lists all required inputs for the map (inventory file + short descriptions) for quick inspection and execution context.
- `Visualisation/dependances_map_paris/bundle_no_shapefiles_2018/`: ready-to-use 2018 bundle without shapefiles (code + CSV + sample output HTML).

**Shapefile note (public datasets):**
- Quartier shapefile public source: `[ADD_LINK_HERE]`
- Carreaux 200m shapefile public source: `[ADD_LINK_HERE]`

**Key CLI options:**
- `--year`: selects annual files (2018–2024).
- `--decoupage-only`: draws only arrondissements/quartiers/carreaux outlines.
- `--zone-metric` + `--add-zonal-intensity-layers`: optional zonal intensity choropleths (`bruit`, `crime`, `densite`, `pauvrete`, `dpe`, `distance_centre`).
- `--kebabs-csv`: custom kebab points file.
- `--prix-csv`: optional external price file for an additional heatmap.
- `--output`: output HTML path.

**Why this script:** it centralises all produced spatial features into one visual QA and interpretation tool, making it easier to inspect yearly patterns and compare neighbourhood effects before/after econometric estimation.

---

## Data Sources

| Data                      | Source                               | Granularity       |
|---------------------------|--------------------------------------|-------------------|
| Geolocated DVF            | data.gouv.fr / Etalab                | Transaction       |
| INSEE 200 m grid cells    | INSEE Filosofi                       | 200 m × 200 m     |
| Noise LDEN                | Bruitparif / PPBE                    | GIS zone          |
| Metro/rail stations       | IDFM / SNCF open data                | Point             |
| Infra-communal crime      | SSMSI / Ministry of the Interior     | IRIS district     |
| DPE                       | ADEME open data                      | Dwelling          |
| Schools / Top schools     | Éducation Nationale open data        | Establishment     |
| Parisian districts        | Ville de Paris open data             | Admin. district   |
| Kebab shops               | kebab-frites.com (web scraping)      | Point             |

---

## Python Dependencies

```
pandas
numpy
scipy
statsmodels
geopandas
pyogrio
requests
beautifulsoup4
lxml
pyproj
```

---

## Authors

Project carried out as part of research in real estate econometrics.  
Code developed and adapted by **Marc Chkeiban** (with contributions from T. Kamionka).

---

## Appendix — Paris Map Dependency Bundles

This appendix centralises the practical bundle information for the Paris map workflow.

### A. Inventory Folder

- Folder: `Visualisation/dependances_map_paris/`
- Purpose: complete inventory of files used by the Paris map visualization for 2018.
- Main inventory file: `Visualisation/dependances_map_paris/fichiers_map_paris_2018.tsv` (inputs, file type, one-line role).
- Year adaptation note: for another year, replace `2018` with the target year in annual CSV paths.

### B. Ready-to-use Bundle (No Shapefiles)

- Folder: `Visualisation/dependances_map_paris/bundle_no_shapefiles_2018/`
- Purpose: practical 2018 package excluding heavy shapefiles.

Included subfolders:
- `code/`: visualization script and Python requirements.
- `data_2018/`: annual CSV inputs used by the map.
- `static/`: kebab points CSV.
- `output/`: generated 2018 HTML map example.

### C. Shapefiles Policy

Shapefiles are intentionally excluded from the lightweight bundle because they are large and publicly available datasets.

Public source links (to be filled):
- Quartier shapefile source: `[ADD_LINK_HERE]`
- Carreaux 200m shapefile source: `[ADD_LINK_HERE]`

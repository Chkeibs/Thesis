from pathlib import Path

import geopandas as gpd
import pyogrio as pgio


CARREAUX_DIR = Path(__file__).resolve().parent.parent
SHAPEFILE = CARREAUX_DIR / "carreaux_200m_met.shp"
BASE_DIR = CARREAUX_DIR.parent
PARIS_QUARTIER_SHP = BASE_DIR / "Quartiers" / "quartier_paris" / "quartier_paris.shp"
OUTPUT_PARIS = CARREAUX_DIR / "resultats" / "carreaux_paris.shp"


def load_carreaux_sample(rows: int = 5) -> gpd.GeoDataFrame:
	"""Load a small sample from the INSEE 200m grid shapefile."""
	if not SHAPEFILE.exists():
		raise FileNotFoundError(
			f"Shapefile not found: {SHAPEFILE}. Copy the carreaux files here."
		)
	return gpd.read_file(SHAPEFILE, rows=rows)


def get_carreaux_feature_count() -> int | None:
	"""Return total feature count without loading all geometries."""
	info = pgio.read_info(SHAPEFILE)
	return info.get("features")


def load_paris_quartiers() -> gpd.GeoDataFrame:
	"""Load the Paris quartier/arrondissement boundaries."""
	if not PARIS_QUARTIER_SHP.exists():
		raise FileNotFoundError(
			f"Paris quartier shapefile not found: {PARIS_QUARTIER_SHP}."
		)
	return gpd.read_file(PARIS_QUARTIER_SHP)


def filter_carreaux_to_paris() -> gpd.GeoDataFrame:
	"""Filter the 200m grid to only Paris (20 arrondissements)."""
	quartiers = load_paris_quartiers()

	# Read the CRS from the grid, then project Paris to match.
	carreaux_crs = gpd.read_file(SHAPEFILE, rows=1).crs
	if quartiers.crs != carreaux_crs:
		quartiers = quartiers.to_crs(carreaux_crs)

	# Read only cells within the Paris bounding box to avoid loading all France.
	bbox = tuple(quartiers.total_bounds)
	carreaux = gpd.read_file(SHAPEFILE, bbox=bbox)

	# Keep cells that intersect Paris boundaries.
	filtered = gpd.sjoin(carreaux, quartiers, predicate="intersects", how="inner")
	filtered = filtered.drop(columns=["index_right"], errors="ignore")

	# A cell can intersect multiple quartier polygons on boundaries.
	# Keep one row per INSEE 200m cell.
	if "idcar_200m" in filtered.columns:
		filtered = filtered.drop_duplicates(subset=["idcar_200m"]).copy()

	return filtered


if __name__ == "__main__":
	total = get_carreaux_feature_count()
	print(f"Total features: {total}")
	gdf = load_carreaux_sample()
	print(gdf.head())
	paris = filter_carreaux_to_paris()
	print(f"Paris features: {len(paris):,}")
	OUTPUT_PARIS.parent.mkdir(parents=True, exist_ok=True)
	paris.to_file(OUTPUT_PARIS)
	print(f"Saved: {OUTPUT_PARIS}")

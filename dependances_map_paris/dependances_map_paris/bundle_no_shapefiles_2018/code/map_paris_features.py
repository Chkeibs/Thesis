from __future__ import annotations

import argparse
import re
from pathlib import Path

import folium
import pandas as pd
from branca.colormap import LinearColormap
from folium.plugins import HeatMap
import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon, box


PARIS_CENTER = (48.8566, 2.3522)
HEAT_GRADIENT_INTENSITY = {
    0.00: "#2c7bb6",
    0.25: "#abd9e9",
    0.50: "#ffffbf",
    0.75: "#fdae61",
    1.00: "#d7191c",
}


def _find_first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def _coerce_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _read_csv_if_exists(csv_path: Path) -> pd.DataFrame | None:
    if not csv_path.exists():
        return None
    return pd.read_csv(csv_path)


def _parse_crime_class_to_numeric(series: pd.Series) -> pd.Series:
    pattern = re.compile(r"(-?\d+[\.,]?\d*)")

    def _extract_mean(value: object) -> float | None:
        if pd.isna(value):
            return None
        text = str(value)
        nums = [float(m.replace(",", ".")) for m in pattern.findall(text)]
        if not nums:
            return None
        if len(nums) == 1:
            return nums[0]
        return (nums[0] + nums[1]) / 2

    return series.apply(_extract_mean)


def _prepare_points_from_df(
    df: pd.DataFrame,
    lat_candidates: list[str],
    lon_candidates: list[str],
    value_candidates: list[str] | None = None,
    special_value_parser: str | None = None,
) -> pd.DataFrame:
    lat_col = _find_first_existing_column(df, lat_candidates)
    lon_col = _find_first_existing_column(df, lon_candidates)

    if lat_col is None or lon_col is None:
        return pd.DataFrame(columns=["lat", "lon", "value"])

    out = pd.DataFrame()
    out["lat"] = _coerce_numeric(df[lat_col])
    out["lon"] = _coerce_numeric(df[lon_col])

    if value_candidates:
        value_col = _find_first_existing_column(df, value_candidates)
        if value_col is not None:
            if special_value_parser == "crime_class":
                out["value"] = _parse_crime_class_to_numeric(df[value_col])
            else:
                out["value"] = _coerce_numeric(df[value_col])

    return out.dropna(subset=["lat", "lon"])


def _prepare_points_from_csv(
    csv_path: Path,
    lat_candidates: list[str],
    lon_candidates: list[str],
    value_candidates: list[str] | None = None,
    special_value_parser: str | None = None,
) -> pd.DataFrame:
    df = _read_csv_if_exists(csv_path)
    if df is None:
        return pd.DataFrame(columns=["lat", "lon", "value"])
    return _prepare_points_from_df(df, lat_candidates, lon_candidates, value_candidates, special_value_parser)


def _prepare_age_heat_points(quartiers_4326: gpd.GeoDataFrame, age_type: str = "vieux") -> pd.DataFrame:
    carreaux = _load_carreaux_paris_gdf(quartiers_4326)
    if carreaux.empty:
        return pd.DataFrame(columns=["lat", "lon", "value"])

    needed_young = ["ind_0_3", "ind_4_5", "ind_6_10", "ind_11_17"]
    needed_old = ["ind_65_79", "ind_80p"]
    needed_all = ["ind"]

    for col in needed_all:
        if col not in carreaux.columns:
            return pd.DataFrame(columns=["lat", "lon", "value"])

    data = carreaux.copy()
    data["ind"] = pd.to_numeric(data["ind"], errors="coerce")
    data = data[data["ind"] > 0].copy()

    if age_type == "jeunes":
        cols = [c for c in needed_young if c in data.columns]
        if not cols:
            return pd.DataFrame(columns=["lat", "lon", "value"])
        for c in cols:
            data[c] = pd.to_numeric(data[c], errors="coerce").fillna(0)
        data["age_sum"] = data[cols].sum(axis=1)
    else:
        cols = [c for c in needed_old if c in data.columns]
        if not cols:
            return pd.DataFrame(columns=["lat", "lon", "value"])
        for c in cols:
            data[c] = pd.to_numeric(data[c], errors="coerce").fillna(0)
        data["age_sum"] = data[cols].sum(axis=1)

    data["value"] = (data["age_sum"] / data["ind"]) * 100
    data_2154 = data.to_crs("EPSG:2154")
    centroids_2154 = data_2154.geometry.centroid
    centroids_4326 = gpd.GeoSeries(centroids_2154, crs="EPSG:2154").to_crs("EPSG:4326")
    data["lat"] = centroids_4326.y.values
    data["lon"] = centroids_4326.x.values

    return data[["lat", "lon", "value"]].dropna()


def _prepare_carreaux_heat_points(csv_path: Path, value_col: str) -> pd.DataFrame:
    df = _read_csv_if_exists(csv_path)
    if df is None:
        return pd.DataFrame(columns=["lat", "lon", "value"])

    required = {"id_car200m", "latitude", "longitude", value_col}
    if not required.issubset(df.columns):
        return pd.DataFrame(columns=["lat", "lon", "value"])

    data = df[["id_car200m", "latitude", "longitude", value_col]].copy()
    data["lat"] = _coerce_numeric(data["latitude"])
    data["lon"] = _coerce_numeric(data["longitude"])
    data["value"] = _coerce_numeric(data[value_col])
    data = data.dropna(subset=["id_car200m", "lat", "lon", "value"])
    if data.empty:
        return pd.DataFrame(columns=["lat", "lon", "value"])

    aggregated = (
        data.groupby("id_car200m", as_index=False)
        .agg(lat=("lat", "mean"), lon=("lon", "mean"), value=("value", "mean"))
    )
    return aggregated[["lat", "lon", "value"]]


def _merge_dpe_with_coords(dpe_csv: Path, coords_csv: Path) -> pd.DataFrame:
    dpe = _read_csv_if_exists(dpe_csv)
    coords = _read_csv_if_exists(coords_csv)
    if dpe is None or coords is None:
        return pd.DataFrame(columns=["lat", "lon", "value"])

    if not {"id_mutation", "num_ordre"}.issubset(dpe.columns):
        return pd.DataFrame(columns=["lat", "lon", "value"])
    if not {"id_mutation", "num_ordre", "latitude", "longitude"}.issubset(coords.columns):
        return pd.DataFrame(columns=["lat", "lon", "value"])

    subset = coords[["id_mutation", "num_ordre", "latitude", "longitude"]].copy()
    merged = dpe.merge(subset, on=["id_mutation", "num_ordre"], how="left")
    return _prepare_points_from_df(
        merged,
        lat_candidates=["latitude"],
        lon_candidates=["longitude"],
        value_candidates=["DPE_Complete", "DPE1", "DPE2", "DPE3", "DPE4", "DPE5", "DPE6", "DPE7"],
    )


def _load_quartiers_gdf() -> gpd.GeoDataFrame:
    quartiers_path = Path("Quartiers/quartier_paris/quartier_paris.shp")
    if not quartiers_path.exists():
        return gpd.GeoDataFrame()
    gdf = gpd.read_file(quartiers_path)
    gdf.columns = [column.lower() for column in gdf.columns]
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
    if "c_quinsee" in gdf.columns:
        gdf["c_quinsee"] = gdf["c_quinsee"].astype(str)
    if "c_ar" in gdf.columns:
        gdf["c_ar"] = gdf["c_ar"].astype(str)
    return gdf


def _remove_polygon_holes(geometry):
    if geometry is None or geometry.is_empty:
        return geometry

    geometry = geometry.buffer(0)

    if geometry.geom_type == "Polygon":
        return Polygon(geometry.exterior)
    if geometry.geom_type == "MultiPolygon":
        polygons = [Polygon(part.exterior) for part in geometry.geoms if not part.is_empty]
        return MultiPolygon(polygons) if polygons else geometry
    return geometry


def _build_complete_200m_grid(paris_geometry_3035) -> gpd.GeoDataFrame:
    if paris_geometry_3035 is None or paris_geometry_3035.is_empty:
        return gpd.GeoDataFrame()

    minx, miny, maxx, maxy = paris_geometry_3035.bounds
    start_x = int(minx // 200) * 200
    start_y = int(miny // 200) * 200
    end_x = int(maxx // 200 + 1) * 200
    end_y = int(maxy // 200 + 1) * 200

    geometries: list[Polygon] = []
    grid_ids: list[str] = []

    for x in range(start_x, end_x, 200):
        for y in range(start_y, end_y, 200):
            cell = box(x, y, x + 200, y + 200)
            if cell.intersects(paris_geometry_3035):
                geometries.append(cell)
                grid_ids.append(f"CRS3035RES200mN{y}E{x}")

    if not geometries:
        return gpd.GeoDataFrame()

    return gpd.GeoDataFrame(
        {"idcar_200m": grid_ids, "is_synthetic": True},
        geometry=geometries,
        crs="EPSG:3035",
    )


def _load_carreaux_paris_gdf(quartiers_4326: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    carreaux_path = Path("Carreaux/data/carreaux_200m_met.shp")
    if quartiers_4326.empty or not carreaux_path.exists():
        return gpd.GeoDataFrame()

    paris_2154 = quartiers_4326.to_crs("EPSG:2154")
    minx, miny, maxx, maxy = paris_2154.total_bounds

    paris_3035 = quartiers_4326.to_crs("EPSG:3035")
    paris_union_3035 = paris_3035.union_all() if hasattr(paris_3035, "union_all") else paris_3035.unary_union
    paris_union_3035 = _remove_polygon_holes(paris_union_3035)

    complete_grid = _build_complete_200m_grid(paris_union_3035)
    if complete_grid.empty:
        return gpd.GeoDataFrame()

    complete_grid["is_synthetic"] = True

    carreaux_src = gpd.read_file(carreaux_path, bbox=(minx, miny, maxx, maxy))
    carreaux_src.columns = [column.lower() for column in carreaux_src.columns]
    if not carreaux_src.empty and "idcar_200m" in carreaux_src.columns:
        if carreaux_src.crs is None:
            carreaux_src = carreaux_src.set_crs("EPSG:2154")
        carreaux_src = carreaux_src.to_crs("EPSG:3035")

        src_ids = set(carreaux_src["idcar_200m"].astype(str))
        complete_grid["is_synthetic"] = ~complete_grid["idcar_200m"].astype(str).isin(src_ids)

        attrs = carreaux_src.drop(columns=["geometry"]).drop_duplicates(subset=["idcar_200m"])
        complete_grid = complete_grid.merge(attrs, on="idcar_200m", how="left")

    return complete_grid.to_crs("EPSG:4326")


def _add_outline_layer(
    fmap: folium.Map,
    gdf: gpd.GeoDataFrame,
    layer_name: str,
    zone_label_col: str,
    show: bool,
    color: str,
    weight: float,
) -> None:
    if gdf.empty:
        return

    feature_group = folium.FeatureGroup(name=layer_name, show=show)
    style = {
        "fillColor": "#000000",
        "fillOpacity": 0.01,
        "color": color,
        "weight": weight,
    }

    tooltip = None
    if zone_label_col in gdf.columns:
        tooltip = folium.GeoJsonTooltip(fields=[zone_label_col], aliases=["Zone"], localize=True)

    folium.GeoJson(
        gdf,
        style_function=lambda _: style,
        highlight_function=lambda _: {"color": "#000000", "weight": max(weight + 0.6, 1.4), "fillOpacity": 0.05},
        tooltip=tooltip,
    ).add_to(feature_group)
    feature_group.add_to(fmap)


def _add_decoupage_layers(
    fmap: folium.Map,
    show_arrondissements: bool,
    show_quartiers: bool,
    show_carreaux: bool,
) -> None:
    quartiers = _load_quartiers_gdf()
    if quartiers.empty:
        return

    quartiers_layer = quartiers.copy()
    if "l_qu" in quartiers_layer.columns:
        quartiers_layer["zone_name"] = quartiers_layer["l_qu"].astype(str)
    else:
        quartiers_layer["zone_name"] = "Quartier"

    arrondissements = quartiers[["c_ar", "geometry"]].dissolve(by="c_ar", as_index=False)
    arrondissements["zone_name"] = "Arrondissement " + arrondissements["c_ar"].astype(str)

    carreaux = _load_carreaux_paris_gdf(quartiers)
    if not carreaux.empty:
        carreaux["zone_name"] = carreaux.get("idcar_200m", pd.Series(index=carreaux.index, dtype=str)).astype(str)

    _add_outline_layer(
        fmap,
        arrondissements,
        layer_name="Arrondissements (découpage)",
        zone_label_col="zone_name",
        show=show_arrondissements,
        color="#111111",
        weight=1.6,
    )
    _add_outline_layer(
        fmap,
        quartiers_layer,
        layer_name="Quartiers (découpage)",
        zone_label_col="zone_name",
        show=show_quartiers,
        color="#1f2937",
        weight=1.0,
    )
    _add_outline_layer(
        fmap,
        carreaux,
        layer_name="Carreaux 200m (découpage complet Paris)",
        zone_label_col="zone_name",
        show=show_carreaux,
        color="#111111",
        weight=0.6,
    )


def _build_zone_base(paths: dict[str, Path]) -> pd.DataFrame:
    quartier = _read_csv_if_exists(paths["quartier"])
    if quartier is None:
        return pd.DataFrame()

    required_cols = ["id_mutation", "num_ordre", "C_QUINSEE", "C_AR"]
    if not set(required_cols).issubset(quartier.columns):
        return pd.DataFrame()

    base = quartier[required_cols].copy()
    base.columns = ["id_mutation", "num_ordre", "c_quinsee", "c_ar"]
    base["c_quinsee"] = base["c_quinsee"].astype(str)
    base["c_ar"] = base["c_ar"].astype(str)

    bruit = _read_csv_if_exists(paths["bruit"])
    if bruit is not None and {"id_mutation", "num_ordre", "Classe"}.issubset(bruit.columns):
        data = bruit[["id_mutation", "num_ordre", "Classe"]].copy()
        data["bruit"] = _coerce_numeric(data["Classe"])
        base = base.merge(data[["id_mutation", "num_ordre", "bruit"]], on=["id_mutation", "num_ordre"], how="left")

    crime = _read_csv_if_exists(paths["crime"])
    if crime is not None and {"id_mutation", "num_ordre"}.issubset(crime.columns):
        crime_col = _find_first_existing_column(crime, ["classe", "Classe", "taux", "valeur"])
        if crime_col is not None:
            data = crime[["id_mutation", "num_ordre", crime_col]].copy()
            if crime_col.lower() == "classe":
                data["crime"] = _parse_crime_class_to_numeric(data[crime_col])
            else:
                data["crime"] = _coerce_numeric(data[crime_col])
            base = base.merge(data[["id_mutation", "num_ordre", "crime"]], on=["id_mutation", "num_ordre"], how="left")

    centre = _read_csv_if_exists(paths["centre"])
    if centre is not None and {"id_mutation", "num_ordre"}.issubset(centre.columns):
        distance_col = _find_first_existing_column(centre, ["distances", "distance", "Distance"])
        if distance_col is not None:
            data = centre[["id_mutation", "num_ordre", distance_col]].copy()
            data["distance_centre"] = _coerce_numeric(data[distance_col])
            base = base.merge(
                data[["id_mutation", "num_ordre", "distance_centre"]],
                on=["id_mutation", "num_ordre"],
                how="left",
            )

    dpe = _read_csv_if_exists(paths["dpe"])
    if dpe is not None and {"id_mutation", "num_ordre", "DPE_Complete"}.issubset(dpe.columns):
        data = dpe[["id_mutation", "num_ordre", "DPE_Complete"]].copy()
        data["dpe"] = _coerce_numeric(data["DPE_Complete"])
        base = base.merge(data[["id_mutation", "num_ordre", "dpe"]], on=["id_mutation", "num_ordre"], how="left")

    carreaux = _read_csv_if_exists(paths["carreaux"])
    if carreaux is not None and {"id_mutation", "num_ordre", "id_car200m"}.issubset(carreaux.columns):
        keep_cols = ["id_mutation", "num_ordre", "id_car200m", "densite_ind_km2", "pct_menages_pauvres"]
        present_cols = [column for column in keep_cols if column in carreaux.columns]
        data = carreaux[present_cols].copy()
        if "densite_ind_km2" in data.columns:
            data["densite"] = _coerce_numeric(data["densite_ind_km2"])
        if "pct_menages_pauvres" in data.columns:
            data["pauvrete"] = _coerce_numeric(data["pct_menages_pauvres"])
        merge_cols = ["id_mutation", "num_ordre", "id_car200m"]
        if "densite" in data.columns:
            merge_cols.append("densite")
        if "pauvrete" in data.columns:
            merge_cols.append("pauvrete")
        base = base.merge(data[merge_cols], on=["id_mutation", "num_ordre"], how="left")

    return base


def _add_choropleth_layer(
    fmap: folium.Map,
    gdf: gpd.GeoDataFrame,
    layer_name: str,
    value_col: str,
    zone_label_col: str,
    legend_caption: str,
    show: bool,
    add_legend: bool,
    colors: list[str] | None = None,
    tooltip_value_alias: str = "Intensité",
) -> None:
    if gdf.empty or value_col not in gdf.columns:
        return

    plot_df = gdf.copy()
    has_value = plot_df[value_col].notna()
    if not has_value.any():
        return

    min_value = float(plot_df.loc[has_value, value_col].min())
    max_value = float(plot_df.loc[has_value, value_col].max())
    if min_value == max_value:
        max_value = min_value + 1e-9

    palette = colors or ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]

    # Round min/max for a cleaner legend display (branca shows vmin/vmax directly)
    span = max_value - min_value
    if span > 100:
        display_min = round(min_value, 0)
        display_max = round(max_value, 0)
    elif span > 10:
        display_min = round(min_value, 1)
        display_max = round(max_value, 1)
    elif span > 1:
        display_min = round(min_value, 1)
        display_max = round(max_value, 1)
    else:
        display_min = round(min_value, 2)
        display_max = round(max_value, 2)

    # Ensure we don't shrink the range (use original for color mapping, rounded for display)
    colormap = LinearColormap(
        palette,
        vmin=display_min,
        vmax=display_max,
        caption=legend_caption,
    )

    feature_group = folium.FeatureGroup(name=layer_name, show=show)

    def _style_fn(feature: dict) -> dict:
        value = feature["properties"].get(value_col)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            fill_color = "#d9d9d9"
        else:
            fill_color = colormap(value)
        return {
            "fillColor": fill_color,
            "color": "#222222",
            "weight": 0.7,
            "fillOpacity": 0.65,
        }

    tooltip_fields = [zone_label_col, value_col]
    tooltip_aliases = ["Zone", tooltip_value_alias]
    folium.GeoJson(
        plot_df,
        style_function=_style_fn,
        highlight_function=lambda _: {"weight": 2, "color": "#000000", "fillOpacity": 0.75},
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_aliases, localize=True),
    ).add_to(feature_group)

    feature_group.add_to(fmap)
    if add_legend:
        import hashlib
        legend_id = "legend_" + hashlib.md5(layer_name.encode()).hexdigest()[:10]
        colormap_html = colormap._repr_html_()
        legend_html = f'''
        <div id="{legend_id}" style="display:{'block' if show else 'none'};
            position:fixed; bottom:30px; left:50px; z-index:9999;">
            {colormap_html}
        </div>
        '''
        fmap.get_root().html.add_child(folium.Element(legend_html))
        if not hasattr(fmap, '_legend_map'):
            fmap._legend_map = {}
        fmap._legend_map[layer_name] = legend_id


def _add_carreaux_insee_layers(fmap: folium.Map) -> None:
    quartiers = _load_quartiers_gdf()
    carreaux = _load_carreaux_paris_gdf(quartiers)
    if carreaux.empty:
        return

    data = carreaux.copy()
    for col in ["ind", "men", "men_pauv", "ind_0_3", "ind_4_5", "ind_6_10", "ind_11_17",
                "ind_65_79", "ind_80p"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    if "ind" in data.columns:
        area_km2 = 0.04
        data["densite_km2"] = data["ind"] / area_km2

    if {"men", "men_pauv"}.issubset(data.columns):
        safe_men = data["men"].replace(0, pd.NA)
        data["pct_pauvrete"] = (data["men_pauv"] / safe_men) * 100

    if {"ind", "ind_65_79", "ind_80p"}.issubset(data.columns):
        safe_ind = data["ind"].replace(0, pd.NA)
        data["pct_65_plus"] = ((data["ind_65_79"] + data["ind_80p"]) / safe_ind) * 100

    if {"ind", "ind_0_3", "ind_4_5", "ind_6_10", "ind_11_17"}.issubset(data.columns):
        safe_ind = data["ind"].replace(0, pd.NA)
        data["pct_moins_18"] = ((data["ind_0_3"] + data["ind_4_5"] + data["ind_6_10"] + data["ind_11_17"]) / safe_ind) * 100

    data["zone_name"] = data["idcar_200m"].astype(str)

    layers = [
        ("densite_km2", "Densité (hab/km²) par carreau", "Densité (hab/km²)",
         ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"]),
        ("pct_pauvrete", "Pauvreté (%) par carreau", "Ménages pauvres (%)",
         ["#fff5eb", "#fdd0a2", "#fd8d3c", "#d94801", "#7f2704"]),
        ("pct_65_plus", "Personnes âgées ≥65 ans (%) par carreau", "≥65 ans (%)",
         ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"]),
        ("pct_moins_18", "Jeunes <18 ans (%) par carreau", "<18 ans (%)",
         ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"]),
    ]

    for col, name, caption, palette in layers:
        if col not in data.columns:
            continue
        _add_choropleth_layer(
            fmap,
            data,
            layer_name=name,
            value_col=col,
            zone_label_col="zone_name",
            legend_caption=caption,
            show=False,
            add_legend=True,
            colors=palette,
        )


def _add_zone_layers(fmap: folium.Map, paths: dict[str, Path], metric_key: str) -> None:
    metric_mapping = {
        "bruit": ("bruit", "Bruit moyen"),
        "crime": ("crime", "Crime moyen"),
        "densite": ("densite", "Densité moyenne"),
        "pauvrete": ("pauvrete", "Pauvreté moyenne"),
        "dpe": ("dpe", "DPE moyen"),
        "distance_centre": ("distance_centre", "Distance moyenne au centre"),
    }
    if metric_key not in metric_mapping:
        return

    metric_col, metric_label = metric_mapping[metric_key]
    zone_base = _build_zone_base(paths)
    if zone_base.empty or metric_col not in zone_base.columns:
        return

    quartiers = _load_quartiers_gdf()
    if not quartiers.empty and {"c_quinsee", "l_qu", "c_ar"}.issubset(quartiers.columns):
        by_quartier = (
            zone_base.groupby("c_quinsee", as_index=False)[metric_col]
            .mean()
            .rename(columns={metric_col: "metric"})
        )
        quartiers_layer = quartiers.merge(by_quartier, on="c_quinsee", how="left")
        quartiers_layer["zone_name"] = quartiers_layer["l_qu"].astype(str)
        _add_choropleth_layer(
            fmap,
            quartiers_layer,
            layer_name=f"Intensité quartiers - {metric_label}",
            value_col="metric",
            zone_label_col="zone_name",
            legend_caption=f"Échelle intensité ({metric_label})",
            show=False,
            add_legend=True,
        )

        by_arr = (
            zone_base.groupby("c_ar", as_index=False)[metric_col]
            .mean()
            .rename(columns={metric_col: "metric"})
        )
        arr_polygons = quartiers[["c_ar", "geometry"]].dissolve(by="c_ar", as_index=False)
        arr_layer = arr_polygons.merge(by_arr, on="c_ar", how="left")
        arr_layer["zone_name"] = "Arrondissement " + arr_layer["c_ar"].astype(str)
        _add_choropleth_layer(
            fmap,
            arr_layer,
            layer_name=f"Intensité arrondissements - {metric_label}",
            value_col="metric",
            zone_label_col="zone_name",
            legend_caption=f"Échelle intensité ({metric_label})",
            show=False,
            add_legend=True,
        )

    if "id_car200m" in zone_base.columns:
        by_carreau = (
            zone_base.groupby("id_car200m", as_index=False)[metric_col]
            .mean()
            .rename(columns={metric_col: "metric"})
        )
        by_carreau["id_car200m"] = by_carreau["id_car200m"].astype(str)

        carreaux_full = _load_carreaux_paris_gdf(quartiers)
        if not carreaux_full.empty and "idcar_200m" in carreaux_full.columns:
            carreaux_full["id_car200m"] = carreaux_full["idcar_200m"].astype(str)
            carreaux_gdf = carreaux_full.merge(by_carreau, on="id_car200m", how="left")
            carreaux_gdf["zone_name"] = carreaux_gdf["id_car200m"].astype(str)
            _add_choropleth_layer(
                fmap,
                carreaux_gdf,
                layer_name=f"Intensité carreaux 200m - {metric_label}",
                value_col="metric",
                zone_label_col="zone_name",
                legend_caption=f"Échelle intensité ({metric_label})",
                show=False,
                add_legend=True,
            )


def _add_prix_m2_layers(fmap: folium.Map, paths: dict[str, Path]) -> None:
    """Add average prix/m² choropleth layers by quartier and by arrondissement."""
    dvf_path = paths.get("dvf_prepare")
    quartier_path = paths.get("quartier")
    if dvf_path is None or quartier_path is None:
        return

    dvf_df = _read_csv_if_exists(dvf_path)
    quartier_df = _read_csv_if_exists(quartier_path)
    if dvf_df is None or quartier_df is None:
        return

    if "prixm2" not in dvf_df.columns:
        return
    if not {"id_mutation", "num_ordre", "C_QUINSEE", "C_AR"}.issubset(quartier_df.columns):
        return

    dvf_df["prixm2"] = _coerce_numeric(dvf_df["prixm2"])
    merged = quartier_df.merge(
        dvf_df[["id_mutation", "num_ordre", "prixm2"]],
        on=["id_mutation", "num_ordre"],
        how="left",
    )
    merged["C_QUINSEE"] = merged["C_QUINSEE"].astype(str)
    merged["C_AR"] = merged["C_AR"].astype(str)

    quartiers_gdf = _load_quartiers_gdf()
    if quartiers_gdf.empty:
        return

    # ---------- By arrondissement ----------
    by_arr = (
        merged.groupby("C_AR", as_index=False)["prixm2"]
        .mean()
        .rename(columns={"prixm2": "prix_m2_moy"})
    )
    by_arr["C_AR"] = by_arr["C_AR"].astype(str)
    by_arr["prix_m2_moy"] = by_arr["prix_m2_moy"].round(0)

    arr_polygons = quartiers_gdf[["c_ar", "geometry"]].dissolve(by="c_ar", as_index=False)
    arr_polygons["c_ar"] = arr_polygons["c_ar"].astype(str)
    arr_layer = arr_polygons.merge(by_arr, left_on="c_ar", right_on="C_AR", how="left")
    arr_layer["zone_name"] = "Arr. " + arr_layer["c_ar"].astype(str)

    _add_choropleth_layer(
        fmap,
        arr_layer,
        layer_name="Prix moyen/m² par arrondissement",
        value_col="prix_m2_moy",
        zone_label_col="zone_name",
        legend_caption="Prix moyen/m² (€) – Arrondissements",
        show=False,
        add_legend=True,
        colors=["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"],
        tooltip_value_alias="Prix moy. €/m²",
    )

    # ---------- By quartier ----------
    by_qu = (
        merged.groupby("C_QUINSEE", as_index=False)["prixm2"]
        .mean()
        .rename(columns={"prixm2": "prix_m2_moy"})
    )
    by_qu["C_QUINSEE"] = by_qu["C_QUINSEE"].astype(str)
    by_qu["prix_m2_moy"] = by_qu["prix_m2_moy"].round(0)

    quartiers_layer = quartiers_gdf.copy()
    quartiers_layer["c_quinsee"] = quartiers_layer["c_quinsee"].astype(str)
    quartiers_layer = quartiers_layer.merge(by_qu, left_on="c_quinsee", right_on="C_QUINSEE", how="left")
    if "l_qu" in quartiers_layer.columns:
        quartiers_layer["zone_name"] = quartiers_layer["l_qu"].astype(str)
    else:
        quartiers_layer["zone_name"] = quartiers_layer["c_quinsee"].astype(str)

    _add_choropleth_layer(
        fmap,
        quartiers_layer,
        layer_name="Prix moyen/m² par quartier",
        value_col="prix_m2_moy",
        zone_label_col="zone_name",
        legend_caption="Prix moyen/m² (€) – Quartiers",
        show=False,
        add_legend=True,
        colors=["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"],
        tooltip_value_alias="Prix moy. €/m²",
    )


def _add_transaction_points_layers(fmap: folium.Map, paths: dict[str, Path]) -> None:
    """Add all 2018 DVF transaction points, colored by num_ordre, using efficient GeoJson."""
    dvf_path = paths.get("dvf_prepare")
    if dvf_path is None:
        return
    dvf_df = _read_csv_if_exists(dvf_path)
    if dvf_df is None:
        return

    required = {"latitude", "longitude", "num_ordre", "id_mutation", "prixm2"}
    if not required.issubset(dvf_df.columns):
        return

    data = dvf_df[["latitude", "longitude", "num_ordre", "id_mutation", "prixm2"]].copy()
    data["latitude"] = _coerce_numeric(data["latitude"])
    data["longitude"] = _coerce_numeric(data["longitude"])
    data["num_ordre"] = _coerce_numeric(data["num_ordre"]).fillna(1).astype(int)
    data["prixm2"] = _coerce_numeric(data["prixm2"])
    data = data.dropna(subset=["latitude", "longitude"])

    if data.empty:
        return

    # Categorize num_ordre for coloring
    def _cat(n: int) -> str:
        if n == 1:
            return "num_ordre = 1"
        if n == 2:
            return "num_ordre = 2"
        return "num_ordre ≥ 3"

    data["cat"] = data["num_ordre"].apply(_cat)

    # Color mapping – distinct colors
    color_map = {
        "num_ordre = 1": "#dc2626",   # red
        "num_ordre = 2": "#2563eb",   # blue
        "num_ordre ≥ 3": "#d97706",   # amber
    }

    for cat_label, color in color_map.items():
        subset = data[data["cat"] == cat_label].copy()
        if subset.empty:
            continue

        n = len(subset)
        gdf = gpd.GeoDataFrame(
            subset,
            geometry=gpd.points_from_xy(subset["longitude"], subset["latitude"]),
            crs="EPSG:4326",
        )
        # Build tooltip-friendly columns
        gdf["prix_m2_arrondi"] = gdf["prixm2"].round(0)
        gdf["tooltip_text"] = (
            gdf["id_mutation"].astype(str) + " | "
            + gdf["prixm2"].round(0).astype(int).astype(str) + " €/m²"
        )

        fg = folium.FeatureGroup(
            name=f"Transactions DVF – {cat_label} ({n:,})",
            show=False,
        )

        folium.GeoJson(
            gdf[["geometry", "tooltip_text"]],
            marker=folium.CircleMarker(radius=2, weight=0.5, fill=True, fill_opacity=0.7),
            style_function=lambda _, c=color: {
                "color": c,
                "fillColor": c,
                "radius": 2,
                "weight": 0.5,
                "fillOpacity": 0.7,
            },
            tooltip=folium.GeoJsonTooltip(fields=["tooltip_text"], aliases=["Transaction"], localize=True),
        ).add_to(fg)
        fg.add_to(fmap)


def _add_heat_layer(
    fmap: folium.Map,
    points: pd.DataFrame,
    layer_name: str,
    radius: int = 16,
    blur: int = 20,
    min_opacity: float = 0.55,
    show: bool = True,
) -> None:
    if points.empty:
        return

    if "value" in points.columns and points["value"].notna().any():
        heat_data = points[["lat", "lon", "value"]].dropna().values.tolist()
    else:
        heat_data = points[["lat", "lon"]].dropna().values.tolist()

    if not heat_data:
        return

    fg = folium.FeatureGroup(name=layer_name, show=show)
    HeatMap(
        heat_data,
        radius=radius,
        blur=blur,
        min_opacity=min_opacity,
        gradient=HEAT_GRADIENT_INTENSITY,
        max_zoom=14,
    ).add_to(fg)
    fg.add_to(fmap)


def _add_points_layer(
    fmap: folium.Map,
    points: pd.DataFrame,
    layer_name: str,
    color: str = "#111111",
    radius: int = 2,
    show: bool = False,
    max_points: int = 2500,
    popup_cols: list[str] | None = None,
) -> None:
    if points.empty:
        return

    dataset = points.copy().dropna(subset=["lat", "lon"]).drop_duplicates(subset=["lat", "lon"])
    if len(dataset) > max_points:
        dataset = dataset.sample(max_points, random_state=42)

    fg = folium.FeatureGroup(name=layer_name, show=show)
    for _, row in dataset.iterrows():
        popup_text = None
        if popup_cols:
            values = []
            for col in popup_cols:
                if col in dataset.columns and pd.notna(row.get(col)):
                    values.append(f"{col}: {row[col]}")
            if values:
                popup_text = "<br>".join(values)
        marker = folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            weight=1,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
        )
        if popup_text:
            marker.add_child(folium.Popup(popup_text, max_width=300))
        marker.add_to(fg)
    fg.add_to(fmap)


def _year_paths(year: int) -> dict[str, Path]:
    y = f"{year}"
    return {
        "bruit": Path(f"Bruit/dvf75{y}Bruit.csv"),
        "crime": Path(f"Crime/dvf75{y}Crime.csv"),
        "lycees": Path(f"Lycees/dvf75{y}Lycees.csv"),
        "gares": Path(f"Gares/dvf75{y}Gares.csv"),
        "dpe": Path(f"DPE/dvf75{y}Dpe.csv"),
        "centre": Path(f"Centre/dvf75{y}Centre.csv"),
        "quartier": Path(f"Quartiers/dvf75{y}Quartier.csv"),
        "carreaux": Path(f"Carreaux/resultats/dvf75{y}Carreaux_indicateurs.csv"),
        "dvf_prepare": Path(f"DVFGEO/{y}/75/dvf{y}75_prepare.csv"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crée une carte HTML de Paris avec couches multi-features."
    )
    parser.add_argument("--year", type=int, default=2018, help="Année DVF (ex: 2018)")
    parser.add_argument(
        "--kebabs-csv",
        type=Path,
        default=Path("kebabs_paris_with_coords_lambert93 (1).csv"),
        help="CSV kebabs avec colonnes latitude/longitude",
    )
    parser.add_argument(
        "--prix-csv",
        type=Path,
        default=None,
        help="CSV prix optionnel (colonnes latitude/longitude + prix ou valeur_fonciere)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Fichier HTML de sortie",
    )
    parser.add_argument("--zoom", type=int, default=12, help="Niveau de zoom initial")
    parser.add_argument(
        "--decoupage-only",
        action="store_true",
        help="Affiche uniquement les découpages (arrondissements, quartiers, carreaux 200m)",
    )
    parser.add_argument(
        "--zone-metric",
        type=str,
        default="bruit",
        choices=["bruit", "crime", "densite", "pauvrete", "dpe", "distance_centre"],
        help="Métrique utilisée pour colorer arrondissement/quartier/carreaux",
    )
    parser.add_argument(
        "--add-zonal-intensity-layers",
        action="store_true",
        help="Ajoute les couches d'intensité par zones (arrondissement/quartier/carreaux)",
    )
    args = parser.parse_args()

    output = args.output or Path(f"Visualisation/resultats/paris_carte_features_{args.year}.html")
    paths = _year_paths(args.year)

    fmap = folium.Map(location=PARIS_CENTER, zoom_start=args.zoom, control_scale=True, tiles="cartodbpositron")

    if args.decoupage_only:
        _add_decoupage_layers(
            fmap,
            show_arrondissements=True,
            show_quartiers=True,
            show_carreaux=True,
        )
        folium.LayerControl(collapsed=False).add_to(fmap)
        output.parent.mkdir(parents=True, exist_ok=True)
        fmap.save(output)
        print(f"Carte générée: {output}")
        return

    bruit = _prepare_points_from_csv(
        paths["bruit"],
        lat_candidates=["latitude", "latitude_right", "latitude_left"],
        lon_candidates=["longitude", "longitude_right", "longitude_left"],
        value_candidates=["Classe", "gridcode", "Indice"],
    )
    _add_heat_layer(fmap, bruit, "Bruit (heatmap foncée)", radius=14, blur=20, min_opacity=0.58, show=True)

    crime = _prepare_points_from_csv(
        paths["crime"],
        lat_candidates=["latitude", "latitude_right", "latitude_left"],
        lon_candidates=["longitude", "longitude_right", "longitude_left"],
        value_candidates=["classe", "Classe", "taux", "valeur"],
        special_value_parser="crime_class",
    )
    _add_heat_layer(fmap, crime, "Crime (heatmap foncée)", radius=16, blur=22, min_opacity=0.58, show=False)

    gares = _prepare_points_from_csv(
        paths["gares"],
        lat_candidates=["latitude_left", "latitude", "latitude_right"],
        lon_candidates=["longitude_left", "longitude", "longitude_right"],
        value_candidates=["Trafic", "nb_correspondances"],
    )
    _add_heat_layer(fmap, gares, "Gares - trafic (heatmap foncée)", radius=14, blur=20, min_opacity=0.55, show=False)
    _add_points_layer(fmap, gares, "Gares (points bleus)", color="#1d4ed8", radius=3, show=False)

    lycees = _prepare_points_from_csv(
        paths["lycees"],
        lat_candidates=["latitude_left", "latitude", "latitude_right"],
        lon_candidates=["longitude_left", "longitude", "longitude_right"],
    )
    _add_points_layer(fmap, lycees, "Lycées (points verts)", color="#15803d", radius=3, show=False)

    _add_carreaux_insee_layers(fmap)

    dpe = _merge_dpe_with_coords(paths["dpe"], paths["carreaux"])
    _add_heat_layer(fmap, dpe, "DPE (heatmap foncée)", radius=15, blur=21, min_opacity=0.58, show=False)

    _add_decoupage_layers(
        fmap,
        show_arrondissements=False,
        show_quartiers=False,
        show_carreaux=False,
    )

    if args.add_zonal_intensity_layers:
        _add_zone_layers(fmap, paths=paths, metric_key=args.zone_metric)

    _add_prix_m2_layers(fmap, paths)

    _add_transaction_points_layers(fmap, paths)

    kebabs_df = _read_csv_if_exists(args.kebabs_csv)
    if kebabs_df is not None:
        kebabs_points = _prepare_points_from_df(
            kebabs_df,
            lat_candidates=["latitude", "Latitude", "lat"],
            lon_candidates=["longitude", "Longitude", "lon", "lng"],
        )
        if "name" in kebabs_df.columns:
            kebabs_points["name"] = kebabs_df["name"]
        if "arrondissement" in kebabs_df.columns:
            kebabs_points["arrondissement"] = kebabs_df["arrondissement"]
        _add_points_layer(
            fmap,
            kebabs_points,
            "Kebabs (points noirs)",
            color="#000000",
            radius=3,
            show=True,
            max_points=5000,
            popup_cols=["name", "arrondissement"],
        )

    if args.prix_csv is not None and args.prix_csv.exists():
        prix = _prepare_points_from_csv(
            args.prix_csv,
            lat_candidates=["latitude", "latitude_right", "latitude_left"],
            lon_candidates=["longitude", "longitude_right", "longitude_left"],
            value_candidates=["prix", "prix_m2", "valeur_fonciere", "Lval"],
        )
        _add_heat_layer(fmap, prix, "Prix (heatmap foncée)", radius=18, blur=24, min_opacity=0.60, show=False)

    folium.LayerControl(collapsed=False).add_to(fmap)

    # --- Toggle legend visibility based on active layer ---
    if hasattr(fmap, '_legend_map') and fmap._legend_map:
        pairs_js = ','.join(
            '"{name}": "{lid}"'.format(name=name.replace('"', '\\"'), lid=lid)
            for name, lid in fmap._legend_map.items()
        )
        # Collect all legend ids so we can hide them all first on any layer toggle
        all_legend_ids_js = ','.join(
            '"{lid}"'.format(lid=lid)
            for lid in fmap._legend_map.values()
        )
        toggle_js = '''
        <script>
        (function waitForMap() {{
            // Robust detection: find L.Map instance on window
            var map = null;
            for (var key in window) {{
                try {{
                    if (window[key] instanceof L.Map) {{
                        map = window[key];
                        break;
                    }}
                }} catch(e) {{}}
            }}
            if (!map) {{ setTimeout(waitForMap, 300); return; }}

            var legendMap = {{{pairs_js}}};
            var allLegendIds = [{all_legend_ids_js}];

            function hideAllLegends() {{
                allLegendIds.forEach(function(lid) {{
                    var el = document.getElementById(lid);
                    if (el) el.style.display = 'none';
                }});
            }}

            // Initially hide all legends (layers start hidden)
            hideAllLegends();

            // Show legends for layers that are initially visible
            map.eachLayer(function(layer) {{
                // skip - initial state is handled by the show param
            }});

            map.on('overlayadd', function(e) {{
                var lid = legendMap[e.name];
                if (lid) {{
                    var el = document.getElementById(lid);
                    if (el) el.style.display = 'block';
                }}
            }});
            map.on('overlayremove', function(e) {{
                var lid = legendMap[e.name];
                if (lid) {{
                    var el = document.getElementById(lid);
                    if (el) el.style.display = 'none';
                }}
            }});
        }})();
        </script>
        '''.format(pairs_js=pairs_js, all_legend_ids_js=all_legend_ids_js)
        fmap.get_root().html.add_child(folium.Element(toggle_js))

    output.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(output)
    print(f"Carte générée: {output}")


if __name__ == "__main__":
    main()

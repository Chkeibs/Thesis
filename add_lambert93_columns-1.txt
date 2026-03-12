import csv
from pyproj import Transformer

INPUT_CSV = "kebabs_paris_with_coords.csv"
OUTPUT_CSV = "kebabs_paris_with_coords_lambert93.csv"


def main() -> None:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("CSV vide: rien a convertir")
        return

    out_rows = []
    for row in rows:
        lat_str = (row.get("latitude") or "").strip()
        lon_str = (row.get("longitude") or "").strip()

        x_l93 = ""
        y_l93 = ""

        if lat_str and lon_str:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                x, y = transformer.transform(lon, lat)
                x_l93 = f"{x:.3f}"
                y_l93 = f"{y:.3f}"
            except ValueError:
                pass

        out_row = dict(row)
        out_row["lambert93_x"] = x_l93
        out_row["lambert93_y"] = y_l93
        out_rows.append(out_row)

    fieldnames = list(rows[0].keys()) + ["lambert93_x", "lambert93_y"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Saved: {OUTPUT_CSV} ({len(out_rows)} lignes)")


if __name__ == "__main__":
    main()

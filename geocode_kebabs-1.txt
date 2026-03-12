import csv
import time
import os
import requests

INPUT_FILE = "kebabs_paris_from_sitemap.csv"
OUTPUT_FILE = "kebabs_paris_with_coords.csv"

CONTACT_EMAIL = os.getenv("NOMINATIM_EMAIL", "").strip()

HEADERS = {
    "User-Agent": f"kebab-geocoder/1.0 ({CONTACT_EMAIL})" if CONTACT_EMAIL else "kebab-geocoder/1.0"
}

def geocode(address):
    nominatim_url = "https://nominatim.openstreetmap.org/search"
    nominatim_params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "email": CONTACT_EMAIL,
        "countrycodes": "fr",
    }

    try:
        r = requests.get(nominatim_url, params=nominatim_params, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data:
                return data[0]["lat"], data[0]["lon"]
        else:
            print(f"⚠️ Nominatim HTTP {r.status_code} for: {address} -> fallback BAN")
    except requests.RequestException:
        print(f"⚠️ Nominatim request error for: {address} -> fallback BAN")

    ban_url = "https://api-adresse.data.gouv.fr/search/"
    ban_params = {
        "q": address,
        "limit": 1,
    }
    try:
        r = requests.get(ban_url, params=ban_params, timeout=30)
        if r.status_code != 200:
            return None, None

        data = r.json()
        features = data.get("features", [])
        if not features:
            return None, None

        lon, lat = features[0]["geometry"]["coordinates"]
        return str(lat), str(lon)
    except requests.RequestException:
        return None, None


def main():
    if not CONTACT_EMAIL:
        print("ℹ️ NOMINATIM_EMAIL non défini: utilisation du fallback BAN si Nominatim refuse.")

    rows = []

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print("Total rows:", len(rows))

    for i, row in enumerate(rows):
        address = row["address"]

        print(f"{i+1}/{len(rows)} -> Geocoding:", address)

        lat, lon = geocode(address)

        row["latitude"] = lat
        row["longitude"] = lon

        time.sleep(1)  # IMPORTANT: respecter l'API

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("✅ Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
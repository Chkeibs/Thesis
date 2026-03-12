import re
import time
import gzip
import csv
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

SITEMAP_URL = "https://www.kebab-frites.com/sitemap.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; kebab-paris-scraper/1.0)",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# Paris = codes postaux 75001..75020 (intra-muros)
PARIS_CP_RE = re.compile(r"\b750(0[1-9]|1\d|20)\b")


def fetch_bytes(session: requests.Session, url: str) -> bytes:
    r = session.get(url, timeout=30, headers=HEADERS, allow_redirects=True)
    r.raise_for_status()
    data = r.content

    # si gzip (magic bytes)
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)

    # enlève BOM UTF-8 si présent
    data = data.lstrip(b"\xef\xbb\xbf")
    return data


def parse_sitemap(data: bytes):
    root = ET.fromstring(data)

    # namespace (souvent "http://www.sitemaps.org/schemas/sitemap/0.9")
    ns = {}
    if root.tag.startswith("{"):
        ns_uri = root.tag.split("}")[0].strip("{")
        ns = {"sm": ns_uri}

    def findall(path_no_ns: str):
        # path_no_ns ex: "url/loc" ou "sitemap/loc"
        if ns:
            parts = path_no_ns.split("/")
            path = ".//" + "/".join("sm:" + p for p in parts)
            return root.findall(path, ns)
        return root.findall(".//" + path_no_ns)

    tag = root.tag.lower()
    locs = []

    if tag.endswith("sitemapindex"):
        for loc in findall("sitemap/loc"):
            if loc.text:
                locs.append(loc.text.strip())
        return "index", locs

    if tag.endswith("urlset"):
        for loc in findall("url/loc"):
            if loc.text:
                locs.append(loc.text.strip())
        return "urlset", locs

    return "unknown", locs


def get_all_urls_from_sitemap(session: requests.Session, url: str):
    data = fetch_bytes(session, url)

    # Si on reçoit du HTML (blocage), ça commence souvent par "<"
    if data.lstrip().startswith(b"<html") or b"<!doctype html" in data[:200].lower():
        preview = data[:300].decode("utf-8", errors="replace")
        raise RuntimeError(f"Le sitemap renvoie du HTML au lieu de XML:\n{preview}")

    kind, locs = parse_sitemap(data)

    if kind == "index":
        out = []
        for child in locs:
            time.sleep(0.2)
            out.extend(get_all_urls_from_sitemap(session, child))
        return out

    return locs


def is_place_page(u: str) -> bool:
    p = urlparse(u).path
    return p.startswith("/kebab/") and p.endswith(".html") and ("/kebab/paris-" not in p)


def extract_place_info(session: requests.Session, url: str):
    r = session.get(url, timeout=30, headers=HEADERS)
    if r.status_code != 200:
        return None

    soup = BeautifulSoup(r.text, "lxml")

    h1 = soup.find("h1")
    name = h1.get_text(" ", strip=True) if h1 else ""

    # On cherche la ligne qui contient le code postal + Paris
    lines = [ln.strip() for ln in soup.get_text("\n").split("\n") if ln.strip()]
    address = None
    cp = None

    for i, ln in enumerate(lines):
        m = PARIS_CP_RE.search(ln)
        if m and "paris" in ln.lower():
            cp = m.group(0)
            # souvent la rue est sur la ligne précédente
            street = lines[i - 1] if i - 1 >= 0 else ""
            if street and cp not in street and "paris" not in street.lower():
                address = f"{street}, {ln}"
            else:
                address = ln
            break

    if not cp:
        return None  # pas Paris intra-muros

    # arrondissement (si présent "Paris 10")
    arr = ""
    m_arr = re.search(r"\bParis\s+(0[1-9]|1\d|20)\b", address or "", flags=re.IGNORECASE)
    if m_arr:
        arr = m_arr.group(1)

    return {
        "name": name,
        "arrondissement": arr,
        "address": address or "",
        "url": url,
    }


def main():
    session = requests.Session()

    print("1) Lecture du sitemap...")
    all_urls = get_all_urls_from_sitemap(session, SITEMAP_URL)
    place_urls = [u for u in all_urls if is_place_page(u)]
    print("   URLs candidates:", len(place_urls))

    results = []
    seen = set()

    print("2) Filtre Paris (75001..75020) en lisant chaque fiche...")
    for i, u in enumerate(place_urls, 1):
        if u in seen:
            continue
        seen.add(u)

        info = extract_place_info(session, u)
        if info:
            results.append(info)

        if i % 200 == 0:
            print(f"   {i}/{len(place_urls)} traitées | Paris trouvés: {len(results)}")

        time.sleep(0.2)

    out = "kebabs_paris_from_sitemap.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "arrondissement", "address", "url"])
        w.writeheader()
        w.writerows(results)

    print(f"✅ Saved: {out} | total Paris = {len(results)}")


if __name__ == "__main__":
    main()
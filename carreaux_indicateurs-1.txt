
import os
import numpy as np
import pandas as pd


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
RESULTATS_DIR = os.path.join(BASE_DIR, "Carreaux", "resultats")

YEARS = range(2018, 2025)

DVF_FIRST_COLS = [
    "id_mutation",
    "date_mutation",
    "longitude",
    "latitude",
    "num_ordre",
]


def safe_pct(num: pd.Series, den: pd.Series) -> pd.Series:
    den_nonzero = den.where(den != 0)
    return (num / den_nonzero) * 100


def build_year(year: int) -> str:
    in_path = os.path.join(RESULTATS_DIR, f"dvf75{year}Carreaux.csv")
    out_path = os.path.join(RESULTATS_DIR, f"dvf75{year}Carreaux_indicateurs.csv")

    df = pd.read_csv(in_path)

    # Indicateurs demandés
    jeunes_lt18 = df["ind_0_3"] + df["ind_4_5"] + df["ind_6_10"] + df["ind_11_17"]
    pct_jeunes_lt18 = safe_pct(jeunes_lt18, df["ind"])
    pct_men_pauvre = safe_pct(df["men_pauv"], df["men"])
    pct_men_proprio = safe_pct(df["men_prop"], df["men"])

    # Densité approximée en individus / km² (carreau 200m = 0.04 km²)
    densite = df["ind"] / 0.04

    # % logements après 1990 sur total logements hors sociaux
    total_logements = df["log_av45"] + df["log_45_70"] + df["log_70_90"] + df["log_ap90"] + df["log_inc"]
    total_logements_sans_soc = total_logements - df["log_soc"]
    pct_log_ap90_sans_soc = safe_pct(df["log_ap90"], total_logements_sans_soc)

    out = pd.DataFrame({
        "id_mutation": df["id_mutation"],
        "date_mutation": df["date_mutation"],
        "longitude": df["longitude"],
        "latitude": df["latitude"],
        "num_ordre": df["num_ordre"],
        "id_car200m": df["idcar_200m"],
        "pct_individus_jeunes_lt18": pct_jeunes_lt18,
        "pct_menages_pauvres": pct_men_pauvre,
        "pct_menages_proprietaires": pct_men_proprio,
        "nb_individus": df["ind"],
        "densite_ind_km2": densite,
        "pct_logements_apres_1990_sans_sociaux": pct_log_ap90_sans_soc,
    })

    out.to_csv(out_path, index=False)
    return out_path


def main() -> None:
    for year in YEARS:
        out_path = build_year(year)
        print(f"{year}: {out_path}")


if __name__ == "__main__":
    main()

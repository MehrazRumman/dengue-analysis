"""Clean the Mendeley monthly division-level dengue dataset into a tidy CSV.

Source: Monthly Division-Level Dengue Cases & Mortality with Climate and
Environmental Indicators in Bangladesh (2020-2025), Mendeley Data,
doi:10.17632/cgwjshkx5k.2
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/mendeley/dataset.xlsx"
OUT = ROOT / "data/processed/monthly_division_2020_2025.csv"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def clean() -> pd.DataFrame:
    df = pd.read_excel(RAW)
    df.columns = [c.strip().lower() for c in df.columns]
    # Division and Year are merged cells in the sheet: only the first row of each block is filled.
    df[["division", "year"]] = df[["division", "year"]].ffill()
    # Nov-Dec 2025 rows are empty placeholders (dataset published Nov 2025).
    df = df.dropna(subset=["month", "infected"])

    df["division"] = df["division"].str.strip()
    df["month"] = df["month"].str.strip()
    df["year"] = df["year"].astype(int)
    df["month_num"] = df["month"].map({m: i + 1 for i, m in enumerate(MONTHS)})
    df["date"] = pd.to_datetime(dict(year=df.year, month=df.month_num, day=1))
    df["cases"] = df.pop("infected").astype(int)
    df["deaths"] = df.pop("death").astype(int)
    df["temperature_c"] = df.pop("temperature").astype(str).str.extract(r"([\d.]+)")[0].astype(float)
    df["pressure_mbar"] = df.pop("pressure").astype(str).str.extract(r"([\d.]+)")[0].astype(float)
    df = df.rename(columns={"class": "alert_class"})

    cols = ["division", "year", "month", "month_num", "date", "cases", "deaths",
            "temperature_c", "humidity", "pressure_mbar", "pollution", "density", "alert_class"]
    return df[cols].sort_values(["division", "date"]).reset_index(drop=True)


if __name__ == "__main__":
    df = clean()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(df)} rows, "
          f"{df.date.min():%b %Y} - {df.date.max():%b %Y}")

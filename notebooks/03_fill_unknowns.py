"""Fill nulls with 'Unknown' in the processed CSVs.

Run after notebook 02 (which writes ../processed/*.csv):  python 03_fill_unknowns.py
Idempotent: safe to run more than once.

- Text columns: blank -> 'Unknown'.
- Numeric / date columns stay null so measures (median, average, sums) keep working.
  Slicer-friendly numeric columns get a text twin '<Column>Label' that shows 'Unknown'.
All files are read as text so numbers are never rewritten (no '1930.0').
"""
from pathlib import Path
import pandas as pd

PROC = Path(__file__).resolve().parent.parent / "processed"
UNKNOWN = "Unknown"


def read(name):
    return pd.read_csv(PROC / name, dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")


def write(df, name):
    df.to_csv(PROC / name, index=False, encoding="utf-8-sig")


def fill(df, cols):
    for c in cols:
        df[c] = df[c].fillna(UNKNOWN)


def label(df, col, new=None, suffix=""):
    """Text twin of a numeric column: the value, or 'Unknown' when null."""
    new = new or col + "Label"
    df[new] = (df[col] + suffix).fillna(UNKNOWN)


# DimArtist
a = read("DimArtist.csv")
fill(a, ["ArtistBio"])
for c in ["BirthYear", "DeathYear"]:
    label(a, c)
label(a, "BirthDecade", suffix="s")
write(a, "DimArtist.csv")

# FactArtwork
f = read("FactArtwork.csv")
fill(f, ["Title", "Medium", "DateText", "CreditLine", "URL"])
for c in ["YearCreated", "YearAcquired", "AgeAtAcquisition"]:
    label(f, c)
write(f, "FactArtwork.csv")

# Every other file already has no nulls; verify rather than assume.
for name in ["DimDepartment", "DimClassification", "DimLocation", "DimDate", "BridgeArtworkArtist"]:
    d = read(name + ".csv")
    assert not d.isna().any().any(), f"unexpected nulls in {name}"

for name, d in [("DimArtist", a), ("FactArtwork", f)]:
    text_nulls = {c: int(n) for c, n in d.isna().sum().items() if n}
    print(f"{name}: {len(d):,} rows; remaining nulls (numeric/date only): {text_nulls}")

"""Split AcquisitionType out of FactArtwork into its own dimension.

Run after notebook 02 and 03_fill_unknowns.py:  python 04_dim_acquisition_type.py
Writes  ../processed/DimAcquisitionType.csv  (AcquisitionTypeKey, AcquisitionType)
and replaces the text column AcquisitionType in FactArtwork.csv with AcquisitionTypeKey.
Idempotent: if FactArtwork.csv already has the key, it only rewrites the dimension file.
"""
from pathlib import Path
import pandas as pd

PROC = Path(__file__).resolve().parent.parent / "processed"

# Order is the display order. Same labels notebook 02 wrote to the fact table.
TYPES = ["Gift / bequest", "Purchase / fund", "Other / unknown"]
dim = pd.DataFrame({"AcquisitionType": TYPES})
dim.insert(0, "AcquisitionTypeKey", range(1, len(dim) + 1))
dim.to_csv(PROC / "DimAcquisitionType.csv", index=False, encoding="utf-8-sig")

fact = pd.read_csv(PROC / "FactArtwork.csv", dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
if "AcquisitionType" in fact.columns:
    key = dict(zip(dim.AcquisitionType, dim.AcquisitionTypeKey.astype(str)))
    unmapped = set(fact.AcquisitionType.unique()) - set(key)
    assert not unmapped, f"AcquisitionType values with no dimension row: {unmapped}"
    pos = list(fact.columns).index("AcquisitionType")
    fact.insert(pos, "AcquisitionTypeKey", fact.AcquisitionType.map(key))
    fact = fact.drop(columns="AcquisitionType")
    fact.to_csv(PROC / "FactArtwork.csv", index=False, encoding="utf-8-sig")
    print("FactArtwork: AcquisitionType replaced by AcquisitionTypeKey")
else:
    print("FactArtwork already uses AcquisitionTypeKey")

counts = fact.AcquisitionTypeKey.value_counts().sort_index()
print(dim.assign(Works=dim.AcquisitionTypeKey.astype(str).map(counts)).to_string(index=False))
print("rows:", len(fact), "| null keys:", int(fact.AcquisitionTypeKey.isna().sum()))

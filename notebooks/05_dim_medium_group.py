"""Split MediumGroup out of FactArtwork into its own dimension.

Run after notebook 02 and 03_fill_unknowns.py:  python 05_dim_medium_group.py
Writes  ../processed/DimMediumGroup.csv  (MediumGroupKey, MediumGroup)
and replaces the text column MediumGroup in FactArtwork.csv with MediumGroupKey.
The free-text Medium column stays in the fact table.
Idempotent: if FactArtwork.csv already has the key, it only rewrites the dimension file.
"""
from pathlib import Path
import pandas as pd

PROC = Path(__file__).resolve().parent.parent / "processed"

# Display order: the rule order from notebook 02, then the catch-alls.
GROUPS = ["Photography", "Painting", "Printmaking", "Books & ephemera", "Drawing",
          "Time-based", "Sculpture / objects", "Other", "Unknown"]
dim = pd.DataFrame({"MediumGroup": GROUPS})
dim.insert(0, "MediumGroupKey", range(1, len(dim) + 1))
dim.to_csv(PROC / "DimMediumGroup.csv", index=False, encoding="utf-8-sig")

fact = pd.read_csv(PROC / "FactArtwork.csv", dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
if "MediumGroup" in fact.columns:
    key = dict(zip(dim.MediumGroup, dim.MediumGroupKey.astype(str)))
    unmapped = set(fact.MediumGroup.dropna().unique()) - set(key)
    assert not unmapped, f"MediumGroup values with no dimension row: {unmapped}"
    pos = list(fact.columns).index("MediumGroup")
    fact.insert(pos, "MediumGroupKey", fact.MediumGroup.map(key))
    fact = fact.drop(columns="MediumGroup")
    fact.to_csv(PROC / "FactArtwork.csv", index=False, encoding="utf-8-sig")
    print("FactArtwork: MediumGroup replaced by MediumGroupKey")
else:
    print("FactArtwork already uses MediumGroupKey")

counts = fact.MediumGroupKey.value_counts().sort_index()
print(dim.assign(Works=dim.MediumGroupKey.astype(str).map(counts)).to_string(index=False))
print("rows:", len(fact), "| null keys:", int(fact.MediumGroupKey.isna().sum()))

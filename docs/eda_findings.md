# MoMA EDA findings (from `notebooks/01_profiling.ipynb`)

## Size
| Table | Rows |
|---|---|
| Artworks.csv | 157,630 (ObjectID unique) |
| Artists.csv | 15,638 (ConstituentID unique) |
| MoMA_OnView.xlsx - Artworks / Artists | 1,142 / 661 |

## Structure
- **Multi-artist works:** 7,916 (5.0%) have 2+ artists (up to 11+). 1,269 works (0.8%) have **no artist** (mostly Design objects).
- **Artist attributes in Artworks.csv are positional** lists like `(American) (Dutch)`. They line up with ConstituentID in 100% of rows. Artists.csv is the cleaner source, so the artist attributes are dropped from the fact table.
- Every artist ID used in Artworks exists in Artists. 1,215 artists have no works in the collection.
- **Bridge table:** 172,916 artwork-artist rows.

## Quality issues and decisions
| Issue | Size | Decision |
|---|---|---|
| Artist Gender blank | 20.8% of artists | `Unknown` |
| Artist Nationality blank | 16.0% of artists | `Unknown` |
| Gender has 7 spellings (only 6 non-binary/other artists) | - | Male / Female / Non-binary & other / Unknown |
| BeginDate = 0 / EndDate = 0 | 3,558 / 10,035 artists | 0 means unknown or living, so set to null |
| Lifespan over 110 years | 2 (both companies, not people) | Keep, noted |
| `Date` free text ("1948-51", "c. 1920", "n.d.") | 61.8% exact year; 97.2% have an extractable year | `YearCreated` = first 4-digit year plus `DateQuality` flag (Exact / Range / Approximate / Unknown) |
| DateAcquired blank | 4.3% (6,749) | Null. Range 1929-11-19 to 2024-10-28, none before founding |
| Acquired before created | 90 works | `AgeAtAcquisition` set to null for these |
| Dimensions: 0 used as unknown | Depth 10,373 zeros; Height 2,451 | 0 -> null |
| Seat Height 100% blank, Circumference 10 values, Weight 0.2%, Length 0.5%, Diameter 0.9% | - | Seat Height and Circumference dropped; others kept (sparse) |
| Height/Width coverage | 81%/81% overall; Mies Archive 21%, Video 3% | Size KPIs only for `HasValidDimensions` |
| Medium | 22,778 distinct values | Rule-based `MediumGroup` (9 groups, 4% "Other") |
| Classification | 39 values | `ClassificationGroup` (reporting level) |
| URL blank | 36.4%, exactly the uncataloged works | Expected. Cataloged = N means no web page |

## Key numbers
- **Cataloged:** 63.6%. **On view:** 1,210 works (0.77%).
- **Departments:** Drawings & Prints 51%, Architecture & Design 21%, Photography 21%, Painting & Sculpture 2.6%.
- **On-view rate by department:** Painting & Sculpture 11.5% vs Drawings & Prints 0.35%.
- **Acquisition peak:** the 1960s (43,741 works), then 2000s and 2010s (about 25k each).
- **Gender of credited artists (known gender only):** 85.4% male, 14.6% female.
- **Nationality:** American is by far the largest (81,659 artist-credits), then French (24,539) and German (10,900).

## What is MoMA_OnView.xlsx?
It is a **strict subset** of the CSV.
- All 1,142 xlsx works are in Artworks.csv, with **identical** gallery locations.
- The CSV `OnView` column has 1,210 works, so **68 on-view works are only in the CSV**.
- Its 661 artists are all in Artists.csv, and it has fewer columns.
- **Decision:** the model uses the CSV `OnView` column (the superset). The xlsx is only used as a validation check.
- Locations: 5 floors plus 1 work on Floor 6 and 1 PS1 location. Some values have a floor but no gallery number, so they are labeled "General / unspecified".

## Star schema (output of notebook 02, in `processed/`)
FactArtwork (1 row per ObjectID) with DimArtist, DimClassification, DimDepartment, DimLocation, DimDate (acquisition date), DimAcquisitionType (added by `notebooks/04_dim_acquisition_type.py`), DimMediumGroup (added by `notebooks/05_dim_medium_group.py`), and BridgeArtworkArtist.

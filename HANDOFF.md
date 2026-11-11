# HANDOFF: MoMA Power BI build

Goal: build a Power BI report on the Maven MoMA collection (artworks + artists). The EDA is done and the cleaning logic is tested in Python. **Next job: build the semantic model in Power BI using the `powerbi-modeling` MCP server, starting from an empty model.**

## Project layout (`d:\Traxccel\Learaning\maven MOMA Project`)
| Path | What it is |
|---|---|
| `raw_data/Artworks.csv` | 157,630 rows x 30 cols, UTF-8 with BOM |
| `raw_data/Artists.csv` | 15,638 rows x 9 cols, UTF-8 with BOM |
| `raw_data/MoMA_OnView.xlsx` | Strict subset of the CSVs (see decisions). Validation only |
| `raw_data/MoMA_data_dictionary.csv` | Field descriptions |
| `notebooks/01_profiling.ipynb` | EDA (executed) |
| `notebooks/02_cleaning_and_model.ipynb` | **Tested reference for every cleaning rule.** Has 13 passing checks. Exports to `processed/` |
| `processed/*.csv` | Python-built star schema (integer keys). Use as a numeric reference only |
| `docs/eda_findings.md` | Written findings |
| `Power BI/moma.pbip` | PBIP project. Report has 1 blank page |
| `Power BI/moma.SemanticModel` | **Empty model, no tables.** Auto date/time is off. Ready to build in |

## Current state
- The semantic model was reset to empty on purpose (old raw-import tables deleted).
- The `powerbi-modeling` MCP server is registered. In the last session its tools showed up in the tool list late, so load them with ToolSearch (`powerbi-modeling`) and confirm before relying on them.
- The model was **never built or run in Power BI Desktop**. Nothing in Power BI has been validated yet.
- Open `Power BI/moma.pbip` in Power BI Desktop before connecting, or connect to the PBIP folder.

## Decisions already made
- **Artist source is `Artists.csv` only.** The artist columns in `Artworks.csv` are positional lists like `(American) (Dutch)`. They are dropped from the fact table.
- **Multi-artist works use a bridge table.** `ConstituentID` is comma-separated. 7,916 works (5%) have 2+ artists. 1,269 works have none.
- **Use the CSV `OnView` column, not the xlsx.** The xlsx has 1,142 works and the CSV has 1,210. The xlsx is a subset with identical locations.
- Cleaning in **Power Query on the raw CSVs**, so the report refreshes without Python.

## Cleaning rules (port from notebook 02)
**Staging (both CSVs):** `Csv.Document` with `Encoding = 65001`, promote headers, strip the BOM (`#(feff)`) from header names, read every column as text, replace nulls with `""`.

**DimArtist** (one row per `ConstituentID`, 15,638 rows)
- ArtistKey, ArtistName, ArtistBio (blank -> null), Nationality (blank -> `Unknown`), Gender, BirthYear, DeathYear (0 -> null).
- Gender: male -> Male, female -> Female, any other non-blank value -> `Non-binary & other`, blank -> `Unknown`.
- NationalityGroup: the 15 most common nationalities (including `Unknown`) stay, the rest become `Other`.
- BirthDecade, LifeStatus (Deceased / Living or death unknown / Unknown), HasWikidata, HasULAN.

**BridgeArtworkArtist:** one row per artwork-artist pair. Split `ConstituentID` on commas, drop blanks, add ArtistPosition. 172,916 rows, no duplicate pairs.

**FactArtwork** (one row per `ObjectID`)
- Drop the artist columns, Seat Height, Circumference and ImageURL. Keep URL.
- Title: blank -> `Untitled`. Classification: blank or `(not assigned)` -> `Unassigned`.
- YearCreated: first 4-digit run in `Date`. DateQuality: Exact / Range / Approximate / Unknown.
- AcquiredDate: parse `DateAcquired` as `yyyy-MM-dd`, blank -> null. YearAcquired. AgeAtAcquisition = acquired year - created year, null if negative (90 works).
- Dimensions and duration: number, with 0 -> null. HasValidDimensions = Height and Width both present. Area_cm2.
- ArtistCount, HasArtist, IsMultiArtist, IsCataloged (`Cataloged = "Y"`).
- LocationKey: trim quotes from `OnView`. Blank -> `Not on view`. IsOnView.
- MediumGroup: keyword rules, first match wins, order Photography -> Painting -> Printmaking -> Books & ephemera -> Drawing -> Time-based -> Sculpture / objects, else `Other`, blank -> `Unknown`. Keywords are in notebook 02. Use whole-word matching for oil, print, ink and pen.
- AcquisitionType from CreditLine: gift/given/bequest/promised -> Gift / bequest; purchase/fund/acquired through -> Purchase / fund; else Other / unknown.

**Dimensions**
- DimDepartment: 8 values. DimClassification: 39 values plus ClassificationGroup mapping (in notebook 02).
- DimLocation: parse `MoMA, Floor N, gallery`. Some values are floor-only (`MoMA, Floor 3`) and one is `MoMA PS1, Third floor`. Add Floor, Gallery, GalleryLabel, FloorSort, plus a `Not on view` row.
- DimDate: daily, 1929-01-01 to 2024-12-31. Year, Quarter, MonthNumber, MonthName (sort by MonthNumber), Decade, Era (sort by EraSort). Mark as the date table.

## Relationships (all single direction, dimension -> fact)
- DimDepartment[Department], DimClassification[Classification], DimLocation[LocationKey], DimDate[Date] each filter FactArtwork.
- FactArtwork[ObjectID] filters BridgeArtworkArtist[ObjectID]. DimArtist[ArtistKey] filters BridgeArtworkArtist[ArtistKey].
- Keep everything single direction. Artist-level measures count on the **bridge**. Artwork counts use the **fact**. Mixing them inflates multi-artist works.
- A natural text key for department, classification and location is fine. The notebook used integer keys.

## Measures to build
Total Artworks, Total Artists (distinct on bridge), Artist Credits, Artworks per Artist, % Cataloged, % On View, % With Artist, % Multi-Artist Works, Works Acquired, Cumulative Works Acquired, Distinct Acquisition Dates, Unknown Acquisition Date count and %, Median Age at Acquisition, % Female (known gender, on the bridge), Nationalities, % Exact Creation Year, % With Valid Dimensions.

## Numbers to check after each refresh
| Check | Expected |
|---|---|
| FactArtwork rows | 157,630 |
| DimArtist rows | 15,638 |
| Artists with at least one work | 14,423 |
| Bridge rows | 172,916 |
| Works with no artist | 1,269 |
| % Cataloged | 63.6% |
| On-view works | 1,210 (0.77%) |
| Unknown acquisition date | 6,749 (4.3%); 150,881 have a date |
| Acquired before created | 90 |
| Distinct acquisition dates | 1,774 |
| Works acquired in the 1960s | 43,741 |
| Gender of credited artists (known only) | 85.4% male, 14.6% female |
| On-view rate by department | Painting & Sculpture 11.5%, Drawings & Prints 0.35% |
| Department counts | Drawings & Prints 80,420; Architecture & Design 33,612; Photography 33,608; Painting & Sculpture 4,055 |

Small differences in MediumGroup and DateQuality counts versus Python are acceptable. Power Query has no regex, so those rules are approximated.

## Caveats and lessons from the last session
- Power Query has **no regex**. Year extraction and the date-quality and medium-group rules need hand-written M, using text functions or character scans.
- Don't write the whole model into one huge script. Build one table at a time and refresh after each, so errors show up early.
- `Text.BeforeDelimiter` / `Text.AfterDelimiter` behavior when the delimiter is missing was unverified, so guard those calls.
- Python prints non-ASCII text (for example `Ferdinandsbrücke`) wrongly in the Windows console, but the CSV data itself is correct UTF-8.
- Acquisition dates are batch-recorded: the top 10 dates hold 30.5% of works (1968-04-11 alone has 12,839). Year-level charts reflect when records were entered, so day-level charts are not useful.

## Suggested order
1. Connect the MCP to the open `moma.pbip` and confirm the model is empty.
2. Add the `RawDataFolder` parameter and the two staging queries.
3. Build DimDepartment, DimClassification, DimLocation, DimDate.
4. Build DimArtist and BridgeArtworkArtist, then check the counts above.
5. Build FactArtwork, then check counts.
6. Create the relationships and mark DimDate as the date table.
7. Add the measures and test them against the numbers above.
8. Only then start report pages: Overview, Acquisitions over time, Artists and diversity, On view (floors), Data quality.

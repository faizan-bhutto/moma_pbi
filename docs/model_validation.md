# MoMA Power BI model: source, EDA and validation

Validated on 2026-11-11 against the open `moma` semantic model in Power BI Desktop. Numbers in the Model column were read from the model with DAX. Numbers in the Source and Expected columns were recomputed from the raw CSVs, not copied from the model.

## 1. Source data

| File | What it is | Rows | Columns | Last modified |
|---|---|---|---|---|
| `raw_data/Artworks.csv` | One row per artwork | 157,630 (`ObjectID` unique) | 30 | 2024-12-10 |
| `raw_data/Artists.csv` | One row per artist | 15,638 (`ConstituentID` unique) | 9 | 2024-12-10 |
| `raw_data/MoMA_OnView.xlsx` | Works on view. A strict subset of the CSVs, used for validation only | 1,142 works, 661 artists | fewer | 2024-12-11 |
| `raw_data/MoMA_data_dictionary.csv` | Field descriptions for both CSVs | 39 fields | 3 | 2024-12-11 |

- **Format:** UTF-8 with a byte-order mark. Quoted fields can contain line breaks, so a plain line count over-states the rows.
- **Origin:** the project files do not record where the data came from. The field set matches MoMA's public collection data. Confirm the origin and licence before citing it.
- **Artist link:** `Artworks.ConstituentID` holds one or more artist IDs separated by commas. `Artists.csv` is the clean source for artist attributes. The artist columns inside `Artworks.csv` are positional text like `(American) (Dutch)` and are not used.

## 2. EDA summary

Full findings are in `docs/eda_findings.md`. The points that shape the model:

| Finding | Size | Handling in the model |
|---|---|---|
| Works with 2+ artists | 7,916 (5.0%), up to 132 artists on one work | Bridge table, one row per work-artist pair |
| Works with no artist | 1,269 (0.8%), mostly Design objects | No bridge rows. `HasArtist` = false |
| Artists with no works | 1,215 | Stay in DimArtist. Excluded from Total Artists |
| Blank artist gender / nationality / bio | 3,257 / 2,496 / 2,200 | Show as `Unknown` |
| Gender has 7 spellings | 6 non-binary or other artists | Grouped as Male, Female, Non-binary & other, Unknown |
| Birth year 0 / death year 0 | 3,558 / 10,035 | 0 means unknown or living, so null |
| `Date` is free text | 61.8% exact year, 97.2% have a year | `YearCreated` plus a `DateQuality` flag |
| `DateAcquired` blank | 6,749 (4.3%). Range 1929-11-19 to 2024-10-28 | Null. Label column shows `Unknown` |
| Acquired before created | 90 works | `AgeAtAcquisition` set to null |
| Height / Width recorded as 0 | 2,451 / 2,328 | 0 means unknown, so null |
| Valid height and width | 124,287 works (78.8%) | `HasValidDimensions` |
| `Medium` | 22,778 distinct values, 9,247 blank | Rule-based `MediumGroup` |
| Classification | 39 values, 689 blank or "(not assigned)" | `ClassificationGroup`, blanks become `Unassigned` |
| `URL` blank | 57,399 (36.4%), the uncataloged works | Expected. Shows `Unknown` |
| Acquisition dates are batch-recorded | Top 10 dates hold 30.5% of works. 1968-04-11 alone has 12,839 | Use year-level charts, not day-level |

## 3. Source vs model

| Item | Source | Model | Match |
|---|---|---|---|
| Artwork rows | 157,630 | FactArtwork 157,630, `ObjectID` all distinct | Yes |
| Artist rows | 15,638 | DimArtist 15,639 | Yes. One extra row, `Unknown / no artist` (key 0), has no bridge rows |
| Artist-work pairs | 172,916 | BridgeArtworkArtist 172,916 | Yes |
| Artists with at least one work | 14,423 | 14,423 | Yes |
| Departments | 8. Works 80,420 / 33,612 / 33,608 / 4,055 / 3,198 / 1,683 / 1,024 / 30 | 8, same works counts | Yes |
| Classifications | 39. 689 blank or "(not assigned)" | 39. 689 works under `Unassigned` | Yes |
| Acquisition type (worked out from `CreditLine`) | Not a source column. Python gives Gift / bequest 95,719, Purchase / fund 43,961, Other / unknown 17,950 | DimAcquisitionType 3 rows, same works counts, no works without a type | Yes |
| Medium group (worked out from `Medium`, 9,247 blank) | Not a source column. Python gives Printmaking 59,227, Photography 34,575, Drawing 28,759, Unknown 9,247, Other 6,295, Painting 6,034, Books & ephemera 5,325, Sculpture / objects 4,998, Time-based 3,170 | DimMediumGroup 9 rows, same works counts, no works without a group. `Unknown` equals the 9,247 blank mediums | Yes |
| On-view works | 1,210 across 73 location values | 1,210 across 74 DimLocation rows (73 plus `Not on view`) | Yes |
| Not on view | 156,420 | 156,420 | Yes |
| Works with an acquisition date | 150,881 | 150,881 related to DimDate | Yes |
| Acquisition date range | 1929-11-19 to 2024-10-28 | DimDate 1929-01-01 to 2024-12-31, 35,064 days | Yes. Covers the full range |
| Distinct acquisition dates | 1,774 | 1,774 | Yes |
| Gender | male 9,940, female 2,435, other 6, blank 3,257 | Male 9,940, Female 2,435, Non-binary & other 6, Unknown 3,258 | Yes. Unknown includes the key 0 row |
| Blank nationality | 2,496 | `Unknown` 2,497 | Yes. Includes the key 0 row |
| Blank bio | 2,200 | `Unknown` 2,201 | Yes. Includes the key 0 row |
| Birth year 0 | 3,558 | Birth year null 3,559 | Yes. Includes the key 0 row |
| Death year 0 | 10,035 | Death year null 10,036 | Yes. Includes the key 0 row |
| Cataloged = Y | 100,231 | 100,231 | Yes |
| Works with no artist | 1,269 | 1,269 | Yes |
| Acquired before created | 90 | 90 | Yes |
| Acquired in the 1960s | 43,741 | 43,741 | Yes |
| Orphan rows | none expected | No fact rows without a department, classification or location. No bridge rows without a work or artist | Yes |

**Columns.** `Artworks.csv` has 30 columns and FactArtwork has 35.
- 11 raw columns are not in the fact table: `Artist`, `ConstituentID` (it feeds the bridge), `ArtistBio`, `Nationality`, `BeginDate`, `EndDate`, `Gender`, `Dimensions` (text), `ImageURL`, `Circumference (cm)` and `Seat Height (cm)`.
- `Department`, `Classification` and `OnView` are replaced by keys.
- Other columns are renamed or typed, for example `DateAcquired` becomes `AcquiredDate` and `Height (cm)` becomes `Height_cm`.
- Derived columns are added: `YearCreated`, `DateQuality`, `ArtistCount`, `AgeAtAcquisition`, `Area_cm2` and the flags.
- Acquisition type is its own dimension. `AcquisitionType` is worked out from `CreditLine` in Python, and the fact table holds only `AcquisitionTypeKey`.
- Medium group is its own dimension. `MediumGroup` is worked out from the free-text `Medium` in Python, and the fact table holds only `MediumGroupKey`. The raw `Medium` text stays in the fact table.
- Three text columns are added to show `Unknown` for null years: `YearCreatedLabel`, `YearAcquiredLabel` and `AgeAtAcquisitionLabel`.

**Model structure.** Eight single-direction relationships, each filtering from the dimension to the table it describes:

| From (filters) | To |
|---|---|
| DimDepartment[DepartmentKey] | FactArtwork |
| DimAcquisitionType[AcquisitionTypeKey] | FactArtwork |
| DimMediumGroup[MediumGroupKey] | FactArtwork |
| DimClassification[ClassificationKey] | FactArtwork |
| DimLocation[LocationKey] | FactArtwork |
| DimDate[Date] | FactArtwork[AcquiredDate] |
| FactArtwork[ObjectID] | BridgeArtworkArtist |
| DimArtist[ArtistKey] | BridgeArtworkArtist |

DimDate is marked as the date table. Artist-level measures count on the bridge. Artwork-level measures count on the fact table. Mixing the two inflates multi-artist works.

**Nulls and `Unknown`.** Text columns show `Unknown` in place of blanks. Numeric and date columns stay null so medians, averages and sums stay correct. The `...Label` columns give a text version for slicers and charts.

## 4. Measures: result vs expected

All 18 measures live in the `_Measures` table (a calculated table with no data and a hidden placeholder column), grouped in display folders. "Expected" is recomputed from the raw files unless noted.

| Measure | Description | Model | Expected | Check |
|---|---|---|---|---|
| Total Artworks | Count of artworks | 157,630 | 157,630 (raw rows) | Pass |
| Total Artists | Distinct artists with at least one work. Counts on the bridge | 14,423 | 14,423 (distinct IDs in Artworks) | Pass |
| Artist Credits | Artist-work pairs. A work with 2 artists counts twice | 172,916 | 172,916 | Pass |
| Artworks per Artist | Artist credits divided by total artists | 11.99 | 11.99 (172,916 / 14,423) | Pass |
| % Cataloged | Share of works marked cataloged | 63.6% | 63.6% (100,231 / 157,630) | Pass |
| % On View | Share of works currently on display | 0.77% | 0.77% (1,210 / 157,630) | Pass |
| % With Artist | Share of works with at least one artist | 99.2% | 99.2% (156,361 / 157,630) | Pass |
| % Multi-Artist Works | Share of works with 2 or more artists, out of all works | 5.0% | 5.0% (7,916 / 157,630) | Pass |
| Works Acquired | Works with a known acquisition date | 150,881 | 150,881 | Pass |
| Cumulative Works Acquired | Running total of Works Acquired up to the latest date in view | 150,881 at 2024 | 150,881 (equals Works Acquired) | Pass |
| Distinct Acquisition Dates | Number of different acquisition dates, blanks excluded | 1,774 | 1,774 | Pass |
| Unknown Acquisition Date | Works with no acquisition date | 6,749 | 6,749 | Pass |
| % Unknown Acquisition Date | Unknown acquisition date as a share of all works | 4.3% | 4.3% | Pass |
| Median Age at Acquisition | Median years from creation to acquisition. Negative ages are ignored | 21 | 21 (recomputed from 146,776 works with a valid age) | Pass |
| % Female | Female share of artist credits where gender is known | 14.6% | 14.6% (23,450 of 160,899) | Pass |
| Nationalities | Distinct artist nationalities, `Unknown` excluded | 131 | 131 (distinct non-blank in Artists.csv) | Pass |
| % Exact Creation Year | Share of works whose date is a single clean year | 61.8% | 61.8% (97,465 works) | Pass |
| % With Valid Dimensions | Share of works with both height and width above 0 | 78.8% | 78.8% (124,287 works) | Pass |

Other checks:
- **Department rates:** on-view rate is 11.5% for Painting & Sculpture and 0.35% for Drawings & Prints, as expected.
- **Year totals:** 19,733 works were acquired in 1968 and 862 in 2024, matching the processed data.
- **Cumulative by year:** 1929 is 9 works and 2024 is 150,881.

## 5. Caveats

- **Extra artist row.** DimArtist has 15,639 rows, one more than the source. The extra row is the `Unknown / no artist` member. It has no bridge rows, so it does not affect any measure.
- **Total Artists vs DimArtist.** Total Artists is 14,423. The other 1,215 artists have no works.
- **Approximate rules.** `MediumGroup` and `DateQuality` use keyword rules, so small differences from a hand count are expected.
- **Median Age.** It uses `AgeAtAcquisition`, which is null for the 90 works acquired before they were created.
- **Acquisition charts.** Dates are batch-recorded, so year-level charts reflect when records were entered.
- **Nationalities measure.** It counts nationalities among all artists in the current filter, not only artists with works.
- **URL column.** It shows `Unknown` for 57,399 works. Do not give it a Web URL data category.
- **Save status.** The model was built in Power BI Desktop through the MCP server. Confirm it is saved to `Power BI/moma.pbip` before relying on this document.

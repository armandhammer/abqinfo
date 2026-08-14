# Contributed Document Review — August 14, 2026

## Outcome

- Files reviewed: 14
- Exact bytes reviewed: 149,772,864 (142.83 MiB)
- New archived and implemented files: 7
- Exact duplicates requiring no new upload or entry: 7
- Pending review: 0
- Fully validated additions: 6
- Added with exact-file provenance requiring human review: 1 (Girard annotated schematic)
- Files over 100 MiB: 0

## R2 Storage

- Before upload: 2,587,875,059 bytes across 218 objects
- Added: 71,181,644 bytes across 7 objects
- Projected and verified after upload: 2,659,056,703 bytes across 225 objects (2.476 GiB)
- ABQInfo project stop: 8 GiB
- Current Cloudflare R2 Standard free storage: 10 GB-month per month, verified from the official pricing page on August 14, 2026

## Added Documents

| Document | Exact bytes | Human size | Pages | Canonical page | Status |
|---|---:|---:|---:|---|---|
| City Council Resolution R-2020-079: Silver Avenue Bike Boulevard Review | 259,026 | 252.96 KiB | 4 | Bicycling / Projects | Validated |
| Albuquerque Vision Zero Action Plan (2021) | 3,922,054 | 3.74 MiB | 52 | Bicycling / Safety & Crash Data | Validated |
| City of Albuquerque Elementary & Middle School Crossing Evaluation (2019) | 13,946,054 | 13.30 MiB | 109 | Maps / Dashboards | Validated |
| East Central Avenue Safety Study (2020) | 8,866,217 | 8.46 MiB | 59 | Roadway Projects / Studies | Validated |
| Girard Streetscape Annotated Schematic Design (2022) | 17,014,412 | 16.23 MiB | 10 | Roadway Projects / Studies | Requires human review |
| I-25 Bicycle Accessibility Study Summary (2020; Updated 2021) | 575,903 | 562.41 KiB | 6 | Bicycling / Projects | Validated |
| Silver Avenue Bike Boulevard Review (2019) | 26,597,978 | 25.37 MiB | 98 | Bicycling / Projects | Validated |

The Girard document is useful and visibly City-produced, and its project lineage is corroborated by maintained City material. Its red annotations identify it as a working design record. Because no authoritative direct URL for this exact annotated copy was recovered, the inventory preserves the provenance warning rather than labeling it fully authoritative.

## Exact Duplicates

| Document | Exact bytes | Human size | Existing inventory record |
|---|---:|---:|---|
| City Council Resolution R-07-268: Bike Boulevards | 86,484 | 84.46 KiB | `src-4cb190564a688d42` |
| 2023–2027 Consolidated Plan and 2023 Action Plan | 20,352,710 | 19.41 MiB | `src-d2647601984f4cbc` |
| Integrated Development Ordinance, Effective May 6, 2026 | 23,832,206 | 22.73 MiB | `src-8e220130c8cbca3d` |
| Albuquerque Regional Housing Needs Assessment (2024) | 4,212,464 | 4.02 MiB | `src-8778e4e2844fdd47` |
| MRCOG Regional Transportation Safety Action Plan (2024) | 26,047,323 | 24.84 MiB | `src-9b3a3aad50ad0c65` |
| NMDOT I-40 West Corridor Study Executive Summary | 1,038,744 | 1,014.40 KiB | `src-e60615e24211cb36` |
| NMDOT Statewide Public Transportation Plan (2025) | 3,021,289 | 2.88 MiB | `src-6825d0105cc90290` |

The contributed R-07-268 file was separately downloaded from public R2 and verified byte-identical to the existing archive by exact size and SHA-256.

## Large-File Review

Two candidates exceed 25,000,000 bytes; only the Silver Avenue review exceeds 25 MiB (26,214,400 bytes). Neither approaches the 100 MiB approval threshold.

### Silver Avenue Bike Boulevard Review

- Exact size: 26,597,978 bytes (25.37 MiB)
- Type: PDF
- Reason for size: 98 map- and image-heavy pages containing full-corridor analysis, photographs, diagrams, crossing alternatives, recommendations, and appendices
- Smaller authoritative version: none found
- Optimization: technically possible only by altering the authoritative source or reducing map and image fidelity; not performed
- Storage effect: included in the verified post-upload total of 2,659,056,703 bytes

### MRCOG Regional Transportation Safety Action Plan

- Exact size: 26,047,323 bytes (24.84 MiB; 26.05 MB in decimal units)
- Type: PDF
- Reason for size: 209-page regional plan with extensive maps, graphics, safety analysis, profiles, and recommendations
- Smaller authoritative version: not needed for this batch because the exact file was already archived and implemented
- Optimization: not proposed; the existing authoritative archive remains unchanged
- Storage effect: no additional R2 storage because the contributed file is an exact duplicate

## Validation

- Every new public R2 object matched its source file by exact byte size and SHA-256.
- Descriptions contain 20–50 words.
- Each new document has one canonical content placement.
- Content-style validation passed with no nested explanatory bullets.
- Discovery-crawler regression passed.
- Clean Hugo build passed: 56 pages, 70 static files.
- Maintained source links for the City Vision Zero release, DMD document collection, Bernalillo County East Central project, and current Girard project were retained. Former official file paths are labeled as former where useful for provenance.

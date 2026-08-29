# R2 archive plan report

Generated from `project-state/retained-source-expansion-15-r2-plan-2026-08-28.json`.

- Current bucket storage: 6170709072 bytes
- Files proposed: 17
- Total size of files in batch: 100000249 bytes (95.37 MiB)
- Storage added: 100000249 bytes (95.37 MiB)
- Projected bucket storage: 6270709321 bytes (5.84 GiB)
- Files larger than 25 MiB: 1
- Files larger than 100000000 bytes: 0
- Remaining nonterminal candidates: 4115
- Exact size of remaining candidates with known size, deduplicated: 1724284775 bytes (1644.41 MiB)
- Remaining candidates without reliable size metadata: 3043
- Complete-project storage lower bound from currently known sizes: 7994994096 bytes (7.45 GiB)
- Complete-project estimate limitation: unknown-size and not-yet-discovered files prevent a defensible final total; the lower bound is not a storage commitment.

| Stable ID | Title | Type | Exact bytes | Human size | Over 25 MiB | R2 key |
|---|---|---:|---:|---:|---:|---|
| src-a3013fed9a879aad | El Camino Real National Historic Trail — Bernalillo County Route Map | PDF | 1657476 | 1.58 MiB | No | `transportation/bicycling/bike-plans/bernco-el-camino-real-trail-route-map-2016.pdf` |
| src-cee60739837f2c92 | Isleta Drain Trail Master Plan — Reference Map | PDF | 1165906 | 1.11 MiB | No | `transportation/bicycling/bike-plans/bernco-isleta-drain-trail-reference-map-2021.pdf` |
| src-054c70be093fec44 | Isleta Drain Trail Master Plan — Aerial Network Map | PDF | 9288784 | 8.86 MiB | No | `transportation/bicycling/bike-plans/bernco-isleta-drain-trail-aerial-map-2021.pdf` |
| src-b2680de9b7aa9d6b | Edith Boulevard and Vineyard Road Improvements — Project Map | PDF | 20990 | 0.02 MiB | No | `transportation/roadway-projects/past/bernco-edith-vineyard-project-map-2021.pdf` |
| src-bb71d6cf149abbde | Atrisco Vista Boulevard Phase A/B Study | PDF | 76771030 | 73.21 MiB | Yes | `transportation/transportation-plans/bernco-atrisco-vista-boulevard-phase-ab-study-2019.pdf` |
| src-7765c50904c04e7a | Alameda Adaptive Signal Project Phase 2 — Location Map | PDF | 412273 | 0.39 MiB | No | `transportation/operations-data/bernco-alameda-adaptive-signal-phase-2-map-2021.pdf` |
| src-47094de943dd35cf | Alameda Boulevard Median Landscape Renovation Phase II — Plans | PDF | 532996 | 0.51 MiB | No | `transportation/roadway-projects/past/bernco-alameda-median-landscape-plans-2021.pdf` |
| src-7287327f90d80686 | Arenal Storm Drain Project — Site Map | PDF | 529188 | 0.5 MiB | No | `public-works/stormwater/bernco-arenal-storm-drain-project-map-2021.pdf` |
| src-15ffafc74755cd91 | Paradise Hills Trail — Conceptual Improvements Map | PDF | 1561130 | 1.49 MiB | No | `transportation/bicycling/projects/past/bernco-paradise-hills-trail-concept-map-2013.pdf` |
| src-183f9856caaf7a57 | Sunset Gardens Road Phase 2 — Project Map | PDF | 288600 | 0.28 MiB | No | `transportation/roadway-projects/past/bernco-sunset-gardens-road-phase-2-map-2021.pdf` |
| src-2df68bc35987ea5c | Sunset Road Improvements — Proposed Storm Drain Map | PDF | 147547 | 0.14 MiB | No | `public-works/stormwater/bernco-sunset-road-proposed-storm-drain-map-2021.pdf` |
| src-a1a4808f971f6584 | Tower Road SW Roadway and Utility Improvements — Project Map | PDF | 356664 | 0.34 MiB | No | `transportation/roadway-projects/past/bernco-tower-road-sw-project-map-2021.pdf` |
| src-61412b57ce54be39 | Vista del Rio Area Storm Drainage Project — Phase Map | PDF | 5201151 | 4.96 MiB | No | `public-works/stormwater/bernco-vista-del-rio-drainage-phase-map-2016.pdf` |
| src-949efe6dcb757173 | Woodward Road Improvements — Project Map | PDF | 385680 | 0.37 MiB | No | `transportation/roadway-projects/past/bernco-woodward-road-project-map-2021.pdf` |
| src-999e00f72cfe2059 | Blake Road and Coors Boulevard Improvements — Phases 1–5 Map | PDF | 314848 | 0.3 MiB | No | `transportation/roadway-projects/past/bernco-blake-coors-phases-1-5-map-2021.pdf` |
| src-0e64d7e28326591c | Blake Road and Coors Boulevard Improvements — Phase 6 Map | PDF | 205529 | 0.2 MiB | No | `transportation/roadway-projects/past/bernco-blake-coors-phase-6-map-2021.pdf` |
| src-79262fb84e00fe05 | Bernalillo County Transportation Projects Update | PDF | 1160457 | 1.11 MiB | No | `transportation/roadway-projects/past/bernco-transportation-projects-update-2015.pdf` |

## Files larger than 25 MiB

- **Atrisco Vista Boulevard Phase A/B Study** — 76771030 bytes (73.21 MiB), PDF. 76,771,030-byte (73.21 MiB) authoritative 132-page PDF; unusually large because it includes full-resolution plan-and-profile sheets, cross-sections, cost estimates, and a preliminary drainage report. A smaller authoritative complete version was not found. Optimization could reduce fidelity, so the original is preserved. Projected R2 storage remains below 8 GB.

## Current R2 Pricing Check

Cloudflare's official R2 pricing page, last updated August 7, 2026 and checked August 28, 2026, lists a monthly Standard-storage free tier of 10 GB-month, 1 million Class A operations, 10 million Class B operations, and free internet egress. Standard storage beyond the allowance is listed at $0.015 per GB-month. The project's stricter 8 GB stop point remains unchanged. Source: <https://developers.cloudflare.com/r2/pricing/>.

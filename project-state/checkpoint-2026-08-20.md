# ABQInfo checkpoint — 2026-08-20

## Completed locally

- Updated the homepage summary to match the current categories.
- Replaced REST-directory primary links with public map viewers for City speed limits, City roadway/camera/signal data, current bikeways, and four Bernalillo County GIS services; retained smaller technical data links.
- Resolved all 30 previously parsed research PDFs to terminal states.
- Archived 18 Central Avenue/ART historical PDFs unchanged, adding 288,242,124 bytes. All public R2 copies passed exact size and SHA-256 comparison. Because exact government download provenance is unresolved for these research-archive files, their inventory status remains `requires human review`.
- Added the 2017 Central Avenue station-area draft collection to Development & Land Use and a curated ART planning/development/public-comment history to ABQ RIDE.
- Reconciled 270 bikeway-plan lineage candidates to six unresolved high-value references by resolving 200 duplicates, excluding 60 extraction fragments or out-of-scope records, and validating four recovered City plans.
- Recovered, archived, and validated the authoritative 1986 Facility Plan for Arroyos and the Amole, Bear Canyon, and Pajarito resource-management plans. The four files add 40,300,282 bytes and their public R2 copies are byte-identical to the City originals.
- Current R2 total: 3,120,691,770 bytes across 263 objects (2.91 GiB).
- Complete validation passed: 5,759 inventory records with zero errors, 39 Markdown files with zero style errors, all 14 crawler regression checks, and a 56-page Hugo build.

## Authoritative inventory state

- Pending review: 4,430
- Downloaded/parsed/placement assigned: 0
- Validated: 385
- Requires human review: 65
- Excluded: 392
- Duplicate: 446
- Superseded: 17
- Exact next item: `lin-10657a569b1bc1fa` — Youth Action Plan

The six unresolved lineage references are Youth Action Plan; Statewide Prioritized Bicycle Network Plan; Bike Gap Closure Program; 2040 Statewide Long-Range Multimodal Transportation Plan; San Antonio Arroyo Corridor Plan; and Recreation Trails Plan.

## Resume instruction

Inspect the exact next record with:

```powershell
$inventory = Get-Content -Raw project-state\master-inventory.json | ConvertFrom-Json
$inventory.candidates | Where-Object id -eq $inventory.next_pending_id | ConvertTo-Json -Depth 8
```

Continue authoritative-source recovery for the six remaining lineage references before moving to the broader pending queue. Preserve user-owned `backups/`. No Git staging, commit, push, pull request, merge, or deployment has been authorized or performed for this working update.

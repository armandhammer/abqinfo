# Council crawl gap review: Downtown Walkability Analysis

## Finding

The 2014 **Downtown Walkability Analysis** was relevant and should have been present on ABQInfo. The original scoped City Council crawl did not discover it as a candidate.

## Why it was missed

1. The Council landing-page crawl captured 43 authored links, but neither the legacy `ABQReport.pdf` URL nor the maintained Planning Department copy was linked directly from that page.
2. The original scoped workflow resolved first-hop pages and saved their outgoing links for review, but it did not enqueue those links for bounded recursive traversal. The Council information architecture places reports behind section and archive/index pages, so a one-hop boundary is insufficient.
3. The exact legacy URL appeared, line-wrapped, inside extracted text from the 2026 Long-Range Transportation System Guide. The workflow extracted PDF text but did not promote official document URLs found in that text into the master inventory.
4. The City Planning Department now maintains a direct index entry for the report on its transportation plans and studies page. That index was outside the user-supplied Council starting page and had not entered the scoped inventory.

This was a discovery-coverage defect, not a relevance judgment, JavaScript problem, access failure, or oversized-file exclusion.

## Repairs

- Added `Find-ExtractedOfficialReferences.ps1` to recover official document URLs from downloaded source text, including URLs split across lines after hyphens or slashes.
- Added `Invoke-ScopedSectionCrawl.ps1` for bounded, same-section, main-content recursive traversal with maximum depth/page controls, exclusions for transient sections, page-by-page state snapshots, and resume support.
- Added a scoped crawl of the City Planning Department's transportation plans and studies index to the durable discovery records.
- Added both PDF identities to the authoritative inventory: the legacy Council copy is marked `superseded`, while the maintained Planning Department copy is implemented on the Transportation Plans page.

## Document verification

- Title: *Albuquerque, New Mexico Downtown Walkability Analysis*
- Author: Jeff Speck / Speck & Associates LLC
- Submitted: September 5, 2014
- Length: 100 pages
- Legacy Council copy: 8,890,105 bytes (8.48 MiB), SHA-256 `b585b78d31e5e074a6c3e526b9f9e6d96c034882d15e5c25874b4f1d217eecd8`
- Maintained Planning copy: 9,752,798 bytes (9.30 MiB), SHA-256 `d486c3bd9d6d5d13772f08a6f05d89004609a54a71e65f556c6b07850d321ac0`
- Size explanation: the report includes aerial photography, maps, and detailed street-redesign diagrams throughout.
- Storage decision: no R2 upload proposed; the maintained authoritative City copy is available directly and both copies are well below the 100 MB concern threshold.

The report proposes targeted downtown street redesigns, signal changes, bicycle facilities, parking reforms, development strategies, railroad crossings, and public-realm improvements. Its content is durable, Albuquerque-specific, and directly relevant to ABQInfo's Transportation Plans collection.

## Additional recovery results

The bounded Council-section pass reached its 201-page checkpoint with 550 normalized, distinct in-section candidates. These are now represented in the master inventory rather than remaining only in a transient crawl artifact. Eleven newly surfaced pages were immediately promoted to `approved for addition` because their durable Albuquerque-specific value was clear:

- Central Avenue Complete Street Plan: 1st Street to Girard
- Girard Boulevard Complete Streets Master Plan
- South Yale Complete Street Master Plan
- City Council Complete Streets project hub
- Amole Mesa Avenue and Messina Drive traffic-calming study
- 118th Street SW improvements
- District 7 traffic and street improvements
- District 7 economic-development and MRA projects
- Laurelwood median rehabilitation and parkway landscape project
- District 3 NeighborWoods project
- Vacant and Abandoned Houses Task Force report

The remaining Council discoveries stay in `pending review` until final URLs, duplicates, relevance, dates, and placements are resolved. Many are district-page navigation, constituent service links, old `resolveuid` aliases, meeting material, or administrative documents; their presence in the inventory does not imply publication on ABQInfo.

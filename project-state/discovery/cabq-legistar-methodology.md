# CABQ Legistar agenda and attachment discovery

The first bounded pass covers January 1, 2020 through September 4, 2026. It queries the official Legistar API for City Council, Special City Council, City Council Study Session, Finance & Government Operations Committee, Land Use, Planning, and Zoning Committee, and Albuquerque Development Commission events.

For this period the API returned 153 City Council events, 81 Finance & Government Operations events, 82 Land Use, Planning, and Zoning events, and eight Council Study Sessions. It returned no Special Council or Development Commission events, and the Study Sessions produced no topical matches. Those zeroes are retained explicitly rather than silently dropping the selected bodies.

For every event in scope, the process reads the structured agenda items, retains matters whose titles match an explicit planning, transportation, redevelopment, land-use, or capital-project vocabulary, enumerates each retained matter's official attachments, and compares attachment URLs with the ABQInfo master inventory. Results are sorted by stable identifiers and dates so repeated runs are reviewable.

This pass is discovery, not automatic publication. A topical title match does not establish lasting public value, and attachment names may be generic. Each new attachment still requires source review, document extraction, deduplication by bytes, editorial placement, and archive validation before it can appear on ABQInfo.

## Queue audit and historical extension

On September 9, 2026, the original 80-item queue was reconciled against the current inventory and the two completed Legistar content batches. The audit groups attachment URLs by legislative matter and classifies each delivery as a substantive attachment, enacted legislation, amendment or redline, draft/final version, executive-communication packet, or generic wrapper. Related versions remain separate provenance records; they are not presumed to be distinct canonical documents.

The same bounded official-API method was then extended from January 1, 2006 through December 31, 2019, using an exclusive end date of January 1, 2020. This historical pass reviewed 635 events, found 1,454 topic-matched matters, and enumerated 3,369 attachment URLs. The selected bodies produced 328 City Council events, five Special City Council events, 38 Study Sessions, 128 Finance and Government Operations Committee events, 136 Land Use, Planning, and Zoning Committee events, and no Albuquerque Development Commission events. Study Sessions again produced no title matches under the recorded topic expression.

The transportation-focused historical queue ranks official plans, studies, reports, enacted legislation, major corridor and mode-specific matters, and substantive attachments. Zoning appeals and generic references to plans are excluded from the focused queue. For each selected attachment, all related Legistar delivery versions remain recorded so later review can compare hashes and normalized extracted or rendered content with both sibling versions and existing City-source copies. One canonical original should be retained, with wrapper and enactment relationships documented rather than archived as duplicate documents.

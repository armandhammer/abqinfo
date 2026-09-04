# CABQ Legistar agenda and attachment discovery

The first bounded pass covers January 1, 2020 through September 4, 2026. It queries the official Legistar API for City Council, Special City Council, City Council Study Session, Finance & Government Operations Committee, Land Use, Planning, and Zoning Committee, and Albuquerque Development Commission events.

For this period the API returned 153 City Council events, 81 Finance & Government Operations events, 82 Land Use, Planning, and Zoning events, and eight Council Study Sessions. It returned no Special Council or Development Commission events, and the Study Sessions produced no topical matches. Those zeroes are retained explicitly rather than silently dropping the selected bodies.

For every event in scope, the process reads the structured agenda items, retains matters whose titles match an explicit planning, transportation, redevelopment, land-use, or capital-project vocabulary, enumerates each retained matter's official attachments, and compares attachment URLs with the ABQInfo master inventory. Results are sorted by stable identifiers and dates so repeated runs are reviewable.

This pass is discovery, not automatic publication. A topical title match does not establish lasting public value, and attachment names may be generic. Each new attachment still requires source review, document extraction, deduplication by bytes, editorial placement, and archive validation before it can appear on ABQInfo.

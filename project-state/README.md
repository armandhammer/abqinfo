# ABQ Info project state

`master-inventory.json` is the authoritative resumable state for the full-site expansion. Do not process a discovered source outside this inventory.

Run from the repository root:

```powershell
./scripts/project/Import-MasterInventory.ps1
./scripts/project/Get-R2Inventory.ps1
./scripts/project/Test-MasterInventory.ps1
./scripts/project/Find-InventoryDuplicates.ps1
./scripts/project/Invoke-ProjectValidation.ps1
```

Use `Import-MasterInventory.ps1 -Rebuild` only when deliberately reconstructing state from repository content, legacy audit files, staged downloads, and curated overrides. Normal candidate transitions must use `Update-Candidate.ps1` so completed work is preserved.

Resume work from the `next_pending_id` recorded at the top of `master-inventory.json`. Update a candidate immediately after every completed state transition. Terminal statuses are `validated`, `excluded`, `duplicate`, `superseded`, `blocked`, and `requires human review`.

## Archival policy for important source documents

ABQInfo is both a discovery tool and a preservation archive. When a government landing page links to a high-quality, important document, do not treat the landing-page link alone as complete implementation.

For qualifying plans, standards, studies, reports, maps, appendices, legislation, project records, and comparable durable materials:

1. Retain a link to the current authoritative government landing page so users can find the source of truth and check for newer editions.
2. Record and evaluate the linked document as its own inventory candidate, including its direct file URL, exact byte size, file type, date/version, checksum, parent/referring page, and provenance.
3. Preserve the original authoritative file in R2 when its informational value, comprehensiveness, uniqueness, historical importance, or risk of disappearance justifies archiving.
4. Link both the preserved R2 copy and the live government source from the appropriate ABQInfo page. Clearly label the archived document by title and date/version; do not imply that it is necessarily the latest edition.
5. Before upload, recheck the live source for a newer version, refresh the R2 storage inventory, calculate projected storage, and apply the project's file-size and approval controls. Never modify an authoritative source merely to avoid a storage threshold without approval.
6. Treat an R2 HTTP 200 as preservation availability, not authoritative provenance validation. Preserve the government source URL and documented discovery path.

This dual-link archival review applies across the site, not only to PDFs or transportation material. A candidate marked implemented or validated should still be flagged for archival follow-up when an important linked artifact has not yet been independently inventoried and evaluated.

## Internet Archive recovery policy

When an official City or other government page refers to a high-value document whose authoritative file URL is broken, do not silently discard the reference or treat the missing file as irrelevant.

1. Add the item to `internet-archive-recovery-queue.json`, recording the exact broken official URL, referring page or document, title, agency, value assessment, date checked, and current recovery status.
2. Give the user the exact broken URL so they can check the Internet Archive. This is a targeted recovery channel for valuable missing material, not a substitute for crawling current authoritative sources.
3. If a copy is recovered, record the Internet Archive capture URL and capture date, download and hash the original file, retain the broken official URL as provenance, and process the document through the normal inventory, R2, placement, and validation controls.
4. A recovered file may be archived in R2, but R2 availability alone does not resolve provenance. The inventory must distinguish the broken official URL, the Internet Archive recovery source, the preserved R2 copy, and any current live government landing page.
5. Keep unsuccessful or uncertain recovery attempts in the queue with a reason and a retry or human-review status. Do not reintroduce user-approved exclusions.

Surface pending high-value recovery candidates during checkpoints so the user can investigate them without interrupting ordinary deterministic crawling.

## Item-specific contact policy

When an authoritative source provides a contact specifically for a current project, active study, open public process, or ongoing program, include that contact with the corresponding ABQInfo item when it would help users ask questions, submit comments, or participate.

Apply these controls:

1. Confirm from the surrounding source text that the person, email address, phone number, or submission channel is explicitly associated with the individual item—not merely a generic department, agency, website, or City contact shown elsewhere on the page.
2. Preserve enough context to explain the contact's purpose, such as `Questions or comments about this project`, rather than listing an unexplained address.
3. Check that the item is current or that the contact channel remains relevant before publishing it. Do not add contacts from completed, superseded, or old projects when the responsible person or mailbox is likely stale.
4. Record the contact's authoritative source and verification date in the candidate notes. If currency or item-specific scope is ambiguous, omit it from the public page or mark it `requires human review`.
5. Recheck item-specific contacts during future page maintenance because they may become obsolete sooner than the underlying project record or archived document.

These contacts will be relatively uncommon and should be treated as useful item metadata, not as a reason to copy general contact directories into ABQInfo.

## Official outbound-link discovery policy

Government sites often publish substantive material through separately hosted official services such as ArcGIS Hub, ArcGIS Online, StoryMaps, project microsites, document hosts, and data portals. Do not silently discard a link merely because its hostname differs from the referring government page.

Crawler design must separate **candidate capture** from **recursive crawl permission**:

1. Record potentially relevant outbound links found in the substantive content of an authoritative government page before applying the recursive-crawl host allowlist.
2. Preserve the referring government URL, anchor text, surrounding context, discovery path, and verification date so official provenance can be evaluated.
3. Classify recognized publishing platforms and resolve their item, group, organization, collection, dataset, application, download, and metadata relationships where appropriate.
4. Apply relevance and quality review before recursively expanding an external service. Excluding social media, advertising, generic navigation, or unrelated third-party material remains appropriate, but the exclusion must be reasoned rather than caused solely by a hostname mismatch.
5. From a user-supplied child page, traverse relevant breadcrumbs, parent folders, section roots, and sibling indexes. Generic parent titles must not block their substantive child links from discovery.
6. Include map, GIS, data, dashboard, application, and project terminology in relevant discovery patterns when those resource types are within ABQInfo scope.

Known-source regression tests must confirm that an official external resource can be recovered from the original government starting point without using the external URL or title as a seed.

## Deferred and last-resort sources

Some official systems are useful for targeted gap recovery but are too incomplete, noisy, or weakly scoped for routine crawling. Record them in `source-priorities.json` and query them only after the primary City, County, MRCOG/MRMPO, and NMDOT page, document, sitemap, catalog, and linked-source pathways have been exhausted for the subject being researched.

The City OnBase Public Records Search is a last-resort source. Limit searches to record classes with a clear ABQInfo connection—principally GAATC, GARTC, any similarly relevant transportation or planning board identified later, and substantive APD annual reports, strategic plans, or other records that fit the site's scope. Do not enumerate unrelated boards, commissions, inspections, proclamations, or administrative record classes merely because the search system exposes them.

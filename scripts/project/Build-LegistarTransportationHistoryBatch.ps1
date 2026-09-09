[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/legistar-transportation-history-batch-decisions-2026-09-09.json',
  [string]$PlanPath = 'project-state/discovery/legistar-transportation-history-r2-archive-plan-2026-09-09.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plans = 'content/transportation/transportation-plans.md'
$studies = 'content/transportation/roadway-projects/studies.md'
$transit = 'content/transportation/transit/abq-ride.md'
$safety = 'content/transportation/safety-crash-data.md'
$operations = 'content/transportation/operations-data.md'
$facilities = 'content/public-works/city-facilities.md'

$items = @(
  [ordered]@{id='src-ef594ed2984d3100';title='Rio Grande Boulevard Complete Street Concept Plan — Adopted Edition';date='2018-02';key='transportation/roadway-projects/studies/cabq-rio-grande-boulevard-complete-street-concept-plan-adopted-2018.pdf';page=$studies;locations=@($studies,$plans);description='Preserves the adopted Rio Grande Boulevard concept plan, combining corridor and intersection analysis, multimodal design alternatives, public involvement, preferred improvements, implementation priorities, and appendices for the segment from Central Avenue through the I-40 area.';note='Official R-18-52 Exhibit A; reviewed as a complete 146-page February 2018 adopted edition distinct from the 154-page February 2017 unadopted City copy (src-3226456d7e9bd345).'}
  [ordered]@{id='src-7bd4ffd09c8d274d';title='Route 66 Action Plan';date='2014-11';key='transportation/transportation-plans/cabq-route-66-action-plan-2014.pdf';page=$plans;locations=@($plans,$studies);description='Sets a corridor-wide revitalization strategy for Albuquerque''s 15 miles of historic Route 66, documenting existing conditions, public priorities, land use, transportation, streetscape, branding, development opportunities, design recommendations, implementation actions, responsible agencies, and funding options.';note='Official R-14-115 final action-plan attachment; all 170 pages, including implementation and design appendices, were extracted and visually reviewed.'}
  [ordered]@{id='src-7b3147e8e7b5baff';title='Albuquerque Rapid Transit Amended Design and Finance Plan Response';date='2016-11';key='transportation/transit/art/cabq-art-amended-design-finance-plan-response-2016.pdf';page=$transit;locations=@($transit);description='Records the City''s response to Council questions about the amended ART design and finance plan, including lane configurations, property and business access, pedestrian and bicycle accommodations, parking, funding, construction, and project oversight.';note='Official EC-16-226 narrative response; 11 scanned pages visually reviewed and retained with its separate maps-and-figures volume.'}
  [ordered]@{id='src-457a45c7d198ddc0';title='Albuquerque Rapid Transit Amended Design and Finance Plan — Maps and Figures';date='2016-11';key='transportation/transit/art/cabq-art-amended-design-finance-maps-2016.pdf';page=$transit;locations=@($transit);description='Supplies the corridor maps and engineering figures accompanying the City''s amended ART response, showing Central Avenue segment designs, travel lanes, medians, stations, parking, right-of-way constraints, intersections, and property access.';note='Official EC-16-226 visual companion to src-7b3147e8e7b5baff; all 16 pages visually reviewed.'}
  [ordered]@{id='src-a693edbb88d8436a';title='Albuquerque Rapid Transit Design Reconfiguration Conditions';date='2016-03';key='transportation/transit/art/cabq-art-design-reconfiguration-conditions-2016.pdf';page=$transit;locations=@($transit);description='Preserves Attachment A to Council Resolution R-16-24, specifying required ART design changes for corridor segments, lane widths and speeds, pedestrian and bicycle accommodations, business and property access, parking, and coordination with NMDOT.';note='Official R-16-24 Attachment A; the document is a three-page set of design conditions, not a Small Starts grant application.'}
  [ordered]@{id='src-31b1f5469a32b3a3';title='Transit to the Future: Short Range Transit Plan for 2006–2011';date='2006-04';key='transportation/transit/history/cabq-short-range-transit-plan-2006-2011.doc';page=$transit;locations=@($transit,$plans);description='Presents ABQ RIDE''s five-year plan for service and capital investment, documenting agency history, routes, ridership, finances, goals, demographic and travel data, system alternatives, public involvement, recommended improvements, implementation, marketing, and evaluation.';note='Official EC-06-157 substantive attachment; the original 99-page legacy DOC was rendered read-only to PDF and every page was visually reviewed. Its one-page transmittal wrapper is src-edfb9c4916757236.'}
  [ordered]@{id='src-bf38ed4520fe9dba';title='Short Range Transit Planning Status and WebHoshin Transition';date='2008-07';key='transportation/transit/history/cabq-short-range-transit-planning-status-2008.doc';page=$transit;locations=@($transit);description='Explains ABQ RIDE''s 2008 decision to replace separately printed annual short- and long-range plans with continuous WebHoshin performance planning, while recording the department''s federal planning obligations and relationship to the 2006–2011 plan.';note='Official EC-08-320 substantive status attachment; three rendered pages reviewed. Its separate one-page routing cover is src-3e831cad3f723a0f.'}
  [ordered]@{id='src-fc716c440ae9896a';title='Transit 10-Year Capital Needs Assessment Status';date='2008-07';key='transportation/transit/history/cabq-transit-capital-needs-assessment-status-2008.doc';page=$transit;locations=@($transit);description='Summarizes ABQ RIDE''s ten-year capital-needs work for fleet replacement, maintenance and operating facilities, passenger amenities, and transit technology through 2030, and describes its integration into the department''s WebHoshin planning process.';note='Official EC-08-317 substantive status attachment; two rendered pages reviewed. Its separate one-page routing cover is src-22d81331e3c000ab.'}
  [ordered]@{id='src-5dd938f55d949f8e';title='Park-and-Ride Transit Center Strategic Planning Status';date='2008-07';key='transportation/transit/history/cabq-park-ride-strategic-planning-status-2008.doc';page=$transit;locations=@($transit);description='Documents ABQ RIDE''s park-and-ride planning process and the regional studies, transit plans, development patterns, commuter demand, funding, and candidate locations that were to inform a coordinated strategic plan for future transit centers.';note='Official EC-08-324 substantive status attachment; two rendered pages reviewed. Its separate one-page routing cover is src-34d02c6c6b6b709b.'}
  [ordered]@{id='src-4946e3c5af08a1f1';title='Coors and Montaño Park-and-Ride Progress Report';date='2008-07';key='transportation/transit/history/cabq-coors-montano-park-ride-progress-2008.doc';page=$transit;locations=@($transit);description='Records the temporary Cottonwood-area park-and-ride, planned Northwest Transit Center opening, 790 Blue Line service, 2007 bond funding, and the City''s search for a permanent Coors-and-Montaño-area transit facility site.';note='Official EC-08-324 supporting report; two rendered pages reviewed. The EC-08-317 delivery src-4b6696981eb8dd1b has identical rendered text and is treated as a misfiled duplicate.'}
  [ordered]@{id='src-9ac92f40d3bc70ba';title='Double Eagle II Aerospace Technology Park Transportation Distribution Status';date='2008-02';key='transportation/transportation-plans/cabq-double-eagle-technology-park-transportation-status-2008.pdf';page=$plans;locations=@($plans,$facilities);description='Maps and summarizes the transportation and utility infrastructure serving the Double Eagle II Aerospace Technology Park, including roadway distribution, pedestrian and bicycle trail connections, transit facilities, and related development status.';note='Official EC-07-1 three-slide substantive attachment; visually reviewed. Its separate one-page transmittal wrapper is src-bea4cfb87b529c0e.'}
  [ordered]@{id='src-5407455e271a4dca';title='Rio Grande Boulevard and Candelaria Road Crash Rate Report';date='2013-12';key='transportation/bicycling/safety-crash-data/cabq-rio-grande-candelaria-crash-rate-2013.pdf';page=$safety;locations=@($safety,$studies);description='Compares reported crash rates at Rio Grande Boulevard and Candelaria Road with other Albuquerque intersections using NMDOT data, traffic volumes, statewide average rates, and collision-type tables assembled for Council''s intersection-safety review.';note='Official R-13-163 crash-rate attachment; all three pages extracted and visually reviewed with the companion severity-index report.'}
  [ordered]@{id='src-4d22afa226e99835';title='Rio Grande Boulevard and Candelaria Road Severity Index Report';date='2013-12';key='transportation/bicycling/safety-crash-data/cabq-rio-grande-candelaria-severity-index-2013.pdf';page=$safety;locations=@($safety,$studies);description='Compares crash severity at Rio Grande Boulevard and Candelaria Road with selected Albuquerque intersections, contrasting 2004–2006 and 2007–2011 injury and severity-index data to support Council''s intersection-safety review.';note='Official R-13-163 severity-index attachment; all four pages extracted and visually reviewed with the companion crash-rate report.'}
  [ordered]@{id='src-9a64aa40900368f8';title='Double Eagle II Airport Master Plan — Original Adopted Edition';date='2019-09';key='transportation/transportation-plans/cabq-double-eagle-ii-airport-master-plan-original-2019.pdf';page=$plans;locations=@($plans,$facilities);description='Preserves the original adopted 2019 airport master plan before the 2024 amendment, covering aviation forecasts, facility requirements, development alternatives, environmental considerations, land-use compatibility, recommended improvements, funding, and phased implementation.';note='Official R-19-169 187-page adopted attachment; visually compared with the 197-page 2019 plan amended in 2024 (src-2cf447cc8b453482), which remains the current canonical edition.'}
  [ordered]@{id='src-2098b91e085169e7';title='Street-Maintenance Pavement-Rating Program Status Packet';date='2012-10';key='transportation/operations-data/cabq-pavement-rating-program-status-2012.pdf';page=$operations;locations=@($operations);description='Documents Council''s receipt of a City update on developing a pavement-rating program for street maintenance, including the planned condition-assessment approach, program purpose, cover analysis, and administrative routing record.';note='Official EC-12-169 four-page scanned status packet; visually reviewed and retitled to avoid presenting it as a completed citywide pavement-condition report.'}
)

$terminal = @(
  [ordered]@{id='src-50619bd0c13df037';status='duplicate';reason='Legistar delivery of the Cutler Avenue Report has the same 27-page normalized substantive text as canonical City copy src-82a238700e5c6270; byte differences do not represent a distinct document.';relationship='Duplicate Legistar delivery wrapper/version of src-82a238700e5c6270.'}
  [ordered]@{id='src-5c710c309ed14029';status='duplicate';reason='Legistar delivery of the Downtown Neighborhood Area Traffic Study has the same 27-page normalized substantive text as canonical City copy src-ce3c9f54fa83aba9; byte differences do not represent a distinct document.';relationship='Duplicate Legistar delivery wrapper/version of src-ce3c9f54fa83aba9.'}
  [ordered]@{id='src-4b6696981eb8dd1b';status='duplicate';reason='Rendered text is identical to the Coors and Montaño Park-and-Ride Progress Report delivered under the correct EC-08-324 matter as src-4946e3c5af08a1f1.';relationship='Misfiled duplicate delivery of src-4946e3c5af08a1f1.'}
  [ordered]@{id='src-bea4cfb87b529c0e';status='excluded';reason='One-page transmittal wrapper; substantive three-slide transportation-status attachment retained as src-9ac92f40d3bc70ba.';relationship='Administrative wrapper for src-9ac92f40d3bc70ba.'}
  [ordered]@{id='src-22d81331e3c000ab';status='excluded';reason='One-page transmittal wrapper; substantive capital-needs status attachment retained as src-fc716c440ae9896a.';relationship='Administrative wrapper for src-fc716c440ae9896a.'}
  [ordered]@{id='src-34d02c6c6b6b709b';status='excluded';reason='One-page transmittal wrapper; substantive park-and-ride status attachments retained as src-5dd938f55d949f8e and src-4946e3c5af08a1f1.';relationship='Administrative wrapper for the EC-08-324 companion records.'}
  [ordered]@{id='src-3e831cad3f723a0f';status='excluded';reason='One-page transmittal wrapper; substantive transit-planning status attachment retained as src-bf38ed4520fe9dba.';relationship='Administrative wrapper for src-bf38ed4520fe9dba.'}
  [ordered]@{id='src-edfb9c4916757236';status='excluded';reason='One-page transmittal wrapper; the complete 99-page 2006–2011 Short Range Transit Plan is retained as src-31b1f5469a32b3a3.';relationship='Administrative wrapper for src-31b1f5469a32b3a3.'}
  [ordered]@{id='src-ef3b07f7e90fe8a7';status='excluded';reason='Two-page closeout memorandum records termination of the light-rail DEIS and financial-plan work but does not contain either proposed plan; retained only as provenance in the batch decision record.';relationship='Closeout wrapper; companion cover analysis is src-2349e15f4ccb31e6.'}
  [ordered]@{id='src-2349e15f4ccb31e6';status='excluded';reason='One-page cover analysis for a terminated light-rail DEIS and financial-plan assignment; no substantive DEIS or financial plan is attached.';relationship='Companion closeout wrapper to src-ef3b07f7e90fe8a7.'}
  [ordered]@{id='src-89b196e2a8b47300';status='duplicate';reason='Malformed attachment URL produced a 404; the corrected official attachment is downloaded and retained as src-a693edbb88d8436a.';relationship='Malformed-URL provenance record for src-a693edbb88d8436a.'}
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
foreach ($item in $items) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1) { throw "Expected one candidate for '$($item.id)'." }
  $candidate = $candidate[0]
  if ($candidate.status -notin @('downloaded','parsed','description drafted','placement assigned')) { throw "Candidate '$($item.id)' is not ready: $($candidate.status)." }
  $candidate.status = 'placement assigned'
  $candidate.title = $item.title
  $candidate.date = $item.date
  $candidate.r2_key = $item.key
  $candidate.r2_url = "https://files.abqinfo.com/$($item.key)"
  $candidate.proposed_canonical_page = $item.page
  $candidate.description = $item.description
  $candidate.description_word_count = @($item.description -split '\s+' | Where-Object { $_ }).Count
  $candidate.implementation_location = $item.page
  $candidate.implementation_locations = @($item.locations)
  $candidate.cross_listing_approved = $item.locations.Count -gt 1
  $candidate.provenance_status = 'official CABQ Legistar matter and direct attachment reviewed'
  $candidate.validation_status = 'source, exact size, SHA-256, extracted content or rendered pages, edition relationship, and description reviewed; R2 upload pending approval'
  $candidate.exclusion_reason = $null
  $candidate.processing_notes = @($candidate.processing_notes | Where-Object { $_ }) + $item.note | Sort-Object -Unique
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}
foreach ($item in $terminal) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1) { throw "Expected one terminal candidate for '$($item.id)'." }
  $candidate = $candidate[0]
  $candidate.status = $item.status
  $candidate.r2_key = $null
  $candidate.r2_url = $null
  $candidate.proposed_canonical_page = $null
  $candidate.implementation_location = $null
  $candidate.implementation_locations = @()
  $candidate.cross_listing_approved = $false
  $candidate.validation_status = "terminal $($item.status) relationship recorded after content comparison"
  $candidate.exclusion_reason = $item.reason
  $candidate.processing_notes = @($candidate.processing_notes | Where-Object { $_ }) + $item.relationship | Sort-Object -Unique
  $candidate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$inventory.next_pending_id = $null
$json = $inventory | ConvertTo-Json -Depth 12
$fullPath = [IO.Path]::GetFullPath($InventoryPath)
$tempPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($tempPath, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $tempPath -Destination $fullPath -Force

$r2 = Get-Content -Raw -Encoding UTF8 -LiteralPath 'project-state/r2-inventory.json' | ConvertFrom-Json
$bytes = [int64](@($items | ForEach-Object { (@($inventory.candidates | Where-Object id -eq $_.id)[0].size_bytes) } | Measure-Object -Sum).Sum)
$planItems = @($items | ForEach-Object {
  $candidate = @($inventory.candidates | Where-Object id -eq $_.id)[0]
  [ordered]@{id=$_.id;source_url=$candidate.source_url;direct_file_url=$candidate.direct_file_url;parent_url=$candidate.parent_url;agency=$candidate.agency;title=$_.title;date=$_.date;file_type=$candidate.file_type;local_path=$candidate.local_path;size_bytes=[int64]$candidate.size_bytes;checksum_sha256=$candidate.checksum_sha256;r2_key=$_.key;proposed_canonical_page=$_.page;implementation_locations=@($_.locations);description=$_.description;provenance_status=$candidate.provenance_status;processing_notes=$_.note;size_warning_over_25mb=([int64]$candidate.size_bytes -gt 25MB);large_file_assessment=$(if ([int64]$candidate.size_bytes -gt 25MB) { 'Reviewed substantive original remains below the 100,000,000-byte object limit; no smaller official edition preserves the same reviewed historical record.' } else { $null });already_present=$false}
})
[ordered]@{schema_version=1;created_at=(Get-Date).ToUniversalTime().ToString('o');batch_id='legistar-transportation-history-2026-09-09';current_r2_bytes=[int64]$r2.total_bytes;maximum_object_bytes=100000000;maximum_projected_r2_bytes=10000000000;batch_bytes=$bytes;added_bytes=$bytes;projected_r2_bytes=([int64]$r2.total_bytes+$bytes);items=$planItems} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $PlanPath -Encoding utf8
[ordered]@{schema_version=1;created_at=(Get-Date).ToUniversalTime().ToString('o');batch_id='legistar-transportation-history-2026-09-09';visible_additions=22;canonical_records=$items.Count;decisions=@($planItems | ForEach-Object { [ordered]@{id=$_.id;title=$_.title;date=$_.date;r2_key=$_.r2_key;canonical_page=$_.proposed_canonical_page;implementation_locations=$_.implementation_locations;description=$_.description;decision='approved for staged addition; upload pending user approval';provenance_status=$_.provenance_status;processing_notes=$_.processing_notes} });terminal_relationships=$terminal} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionPath -Encoding utf8
[pscustomobject]@{Items=$items.Count;VisibleAdditions=22;TerminalRelationships=$terminal.Count;BatchBytes=$bytes;PlanPath=$PlanPath;DecisionPath=$DecisionPath}|ConvertTo-Json -Compress

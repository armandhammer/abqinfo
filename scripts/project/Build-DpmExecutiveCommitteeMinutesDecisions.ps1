[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/dpm-executive-committee-minutes-decisions-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$page = 'content/development-land-use/development-process.md'
$base = 'https://documents.cabq.gov/planning/development-process-manual/'
$precedent = 'Applies the established DPM Executive Committee precedent: src-087842cdf31bbd1c (September 24, 2014) was validated because it recorded substantive adopted manual changes, while src-030f7d2a680a31d4 (November 19, 2014) was excluded as routine procedural minutes.'

# Minutes that record substantive adopted Development Process Manual decisions.
$approved = @(
  [ordered]@{id='src-c8a6a02c203d0cd2';date='2014-07-16';title='Development Process Manual Executive Committee Minutes, July 16, 2014';description='Establishes the committee''s internal rules of procedure, adopting a six-member quorum, majority and unanimous voting thresholds, Open Meetings compliance, and a requirement that the Development Process Manual be amended to reflect recorded voting results.';adopted='Internal rules of procedure, quorum, voting thresholds, Open Meetings policy; DPM to be amended to reflect voting results.'}
  [ordered]@{id='src-ea48e98a01589ffb';date='2014-12-17';title='Development Process Manual Executive Committee Minutes, December 17, 2014';description='Records adoption of the Development Process Manual preface and update procedure, removing references to two dissolved subcommittees, consolidating that authority in the Executive Committee, and approving related language changes by motion.';adopted='Adopted the DPM Preface and update procedure with changes.'}
  [ordered]@{id='src-73f9afbcaae5d8d2';date='2015-12-16';title='Development Process Manual Executive Committee Minutes, December 16, 2015';description='Records unanimous approval of revisions to Chapter 25, Water System Design, and defers the proposed new Chapter 28 on landscape and irrigation improvements to the January 2016 committee meeting.';adopted='Approved revisions to Chapter 25 unanimously.'}
  [ordered]@{id='src-ca86eefe82a821c3';date='2016-09-07';title='Development Process Manual Executive Committee Minutes, September 7, 2016';description='Records approval of the new Chapter 28, amended so the green-space initiative applies to medians only, together with approval of Chapter 22 sections one through seven governing drainage and erosion control.';adopted='Approved new Chapter 28 as amended; approved Chapter 22 sections 1 through 7.'}
  [ordered]@{id='src-21dc013c982971a3';date='2016-10-19';title='Development Process Manual Executive Committee Minutes, October 19, 2016';description='Records approval of Chapter 22 sections eight and nine on drainage and erosion control, and defers sections ten and eleven to the November 2016 Executive Committee meeting.';adopted='Approved Chapter 22 sections 8 and 9.'}
  [ordered]@{id='src-ea47d347422e2570';date='2017-01-18';title='Development Process Manual Executive Committee Minutes, January 18, 2017';description='Records approval of Chapter 22 section twelve, continues section eleven, and defers section thirteen and Chapter 18 to the February 2017 Executive Committee meeting for further review.';adopted='Approved Chapter 22 section 12.'}
  [ordered]@{id='src-bbaad13a047c342c';date='2017-02-01';title='Development Process Manual Executive Committee Minutes, February 1, 2017';description='Records approval of Chapter 22 section eleven and continues Chapter 22 section thirteen and Chapter 18 to the March 2017 Executive Committee meeting for additional discussion.';adopted='Approved Chapter 22 section 11.'}
  [ordered]@{id='src-573093423a1bbd50';date='2017-03-01';title='Development Process Manual Executive Committee Minutes, March 1, 2017';description='Records approval of Chapter 22 section thirteen as amended, Chapter 22 sections fourteen through seventeen, and Chapter 18, completing a substantial block of City drainage and erosion-control standards.';adopted='Approved Chapter 22 section 13 as amended, sections 14 through 17, and Chapter 18.'}
  [ordered]@{id='src-14ba4769fc9b04aa';date='2017-04-19';title='Development Process Manual Executive Committee Minutes, April 19, 2017';description='Records unanimous approval of Chapter 2 as amended and continues Chapter 23 sections 3.4, 3.9.5, and 3.1 to the May 2017 Executive Committee meeting for further consideration.';adopted='Approved Chapter 2 as amended, unanimously.'}
  [ordered]@{id='src-c134c414b9f229c1';date='2017-05-03';title='Development Process Manual Executive Committee Minutes, May 3, 2017';description='Records approval of Chapter 23 sections 3.9.5 and 3.12 as amended, while continuing or deferring Chapter 26, Chapter 27, and Chapter 23 sections 3.4 and 3.6 to later meetings.';adopted='Approved Chapter 23 sections 3.9.5 and 3.12 as amended.'}
  [ordered]@{id='src-79f0672eaab3eca0';date='2017-05-17';title='Development Process Manual Executive Committee Minutes, May 17, 2017';description='Records approval of Chapter 23 section 3.4 as presented and continues Chapter 26, Chapter 27, and Chapter 23 section 3.6 to June and July 2017 Executive Committee meetings.';adopted='Approved Chapter 23 section 3.4 as presented.'}
  [ordered]@{id='src-5340531bfdbbe7fb';date='2017-06-21';title='Development Process Manual Executive Committee Minutes, June 21, 2017';description='Records approval of Chapter 26 on surveys and monumentation and of Chapter 23 sections 3.6 and 3.9, subject to illustration changes, while continuing section 3.7 and the Chapter 7 building-permit process.';adopted='Approved Chapter 26; approved Chapter 23 sections 3.6 and 3.9.'}
  [ordered]@{id='src-fd0a98e661a8db31';date='2017-09-06';title='Development Process Manual Executive Committee Minutes, September 6, 2017';description='Records approval of Chapter 23 section 3.7 on public transit and of the Chapter 7 building-permit process as a new section 2.5, while continuing Chapter 27 drafting standards to a later meeting.';adopted='Approved Chapter 23 section 3.7 Public Transit; approved Chapter 7 building permit process as new Section 2.5.'}
  [ordered]@{id='src-adfd6742a595ccf6';date='2017-10-04';title='Development Process Manual Executive Committee Minutes, October 4, 2017';description='Records approval as amended of Chapter 23 section 3.8 on on-street parking and section 3.5 on pedestrian facilities, while continuing Chapter 27 drafting standards and network-connectivity provisions.';adopted='Approved Chapter 23 section 3.8 On-street Parking and section 3.5 Pedestrian Facilities, both as amended.'}
  [ordered]@{id='src-808550f86ef1cf0e';date='2017-11-15';title='Development Process Manual Executive Committee Minutes, November 15, 2017';description='Records approval of Chapter 23 section 3.3, Pavement Standards, and defers Chapter 27 drafting standards and Chapter 23 section 3.1 network connectivity to December 2017 Executive Committee meetings.';adopted='Approved Chapter 23 section 3.3 Pavement Standards.'}
  [ordered]@{id='src-c2f91d09003c2cbe';date='2018-02-07';title='Development Process Manual Executive Committee Minutes, February 7, 2018';description='Records approval of Chapter 23 section 3.1, Network Connectivity, as published with amended graphics, and defers intersection design, turn-lane and median design, and Chapter 27 drafting standards.';adopted='Approved Chapter 23 section 3.1 Network Connectivity as published, graphics amended.'}
  [ordered]@{id='src-74c9ef9734483c29';date='2018-02-21';title='Development Process Manual Executive Committee Minutes, February 21, 2018';description='Records approval of Chapter 23 section 3.9.6, Intersection Design, as discussed, and defers section 3.9.7 on turn-lane and median design to the March 2018 Executive Committee meeting.';adopted='Approved Chapter 23 section 3.9.6 Intersection Design.'}
  [ordered]@{id='src-58104015e9620a4d';date='2018-03-07';title='Development Process Manual Executive Committee Minutes, March 7, 2018';description='Records approval of Chapter 27 drafting standards as proposed Chapter 4 construction plan standards and of subdivision-compliance provisions, with staff directed to draft new field-change and change-order language.';adopted='Approved Chapter 27 Drafting Standards as proposed Chapter 4; approved proposed Chapter 2 Section 2.2 Subdivision Compliance.'}
)

# Minutes recording only procedural business, deferrals, continuances, or status updates.
$excluded = @(
  [ordered]@{id='src-bb1e08fed8c049a7';date='2014-08-20';reason='Procedural minutes recording that prior votes were null and void pending re-address, plus posting notice and minutes review; no adopted Development Process Manual change.'}
  [ordered]@{id='src-4360b7ad1acbabdb';date='2015-01-21';reason='Routine minutes; the record states no action items were on the agenda and no Development Process Manual change was adopted.'}
  [ordered]@{id='src-7dd4dca158dd74d0';date='2015-03-18';reason='Routine minutes; the record states no action items were on the agenda and no Development Process Manual change was adopted.'}
  [ordered]@{id='src-ff0cce054f5417f8';date='2015-04-15';reason='Routine minutes; the record states no action items were on the agenda and no Development Process Manual change was adopted. Retained as the canonical April 15, 2015 copy over duplicate src-2448a4409efca23b.'}
  [ordered]@{id='src-14f45e5400b067bc';date='2015-05-20';reason='Routine minutes; the record states no action items were on the agenda and no Development Process Manual change was adopted.'}
  [ordered]@{id='src-d763272eeccf1740';date='2015-06-17';reason='Routine minutes; the record states no action items were on the agenda and no Development Process Manual change was adopted.'}
  [ordered]@{id='src-51c281bcea861ad9';date='2015-10-21';reason='Discussion and deferral only; the committee provided comments on the proposed Chapter 28 and deferred a decision without adopting any manual change.'}
  [ordered]@{id='src-f34377f7d362089c';date='2016-01-20';reason='Deferral only; the proposed new Chapter 28 was deferred to the next regular meeting and no manual change was adopted.'}
  [ordered]@{id='src-a729bb09514a9eb3';date='2016-06-15';reason='Procedural business only; a Chapter 26 subcommittee was appointed and Chapter 22 sections and Chapter 28 were continued or deferred without adopted manual changes.'}
  [ordered]@{id='src-a1823b506c80a5e1';date='2016-07-20';reason='Procedural business only; subcommittee appointments for Chapters 24 and 25 were approved and substantive items deferred, without an adopted Development Process Manual change.'}
  [ordered]@{id='src-7cd7534bc544a4cb';date='2016-08-17';reason='Deferrals only; Chapter 28 and Chapter 22 sections one through seven were deferred to the September 2016 meeting without adopted manual changes.'}
  [ordered]@{id='src-3916288248bba241';date='2016-09-21';reason='Deferral only; Chapter 22 sections eight, nine, and eleven were deferred to the October 2016 meeting without adopted manual changes.'}
  [ordered]@{id='src-f2022d135f87e307';date='2016-11-16';reason='Status update only; the record summarizes an ABCWUA report on planned Chapters 24 and 25 subcommittee work without adopting a manual change.'}
  [ordered]@{id='src-df2ad3ce6a0795b8';date='2016-12-07';reason='Deferrals only; Chapter 22 sections eleven, twelve, and thirteen were deferred to the January 2017 meeting without adopted manual changes.'}
  [ordered]@{id='src-f6392e3d79ac62a5';date='2017-04-05';reason='Deferrals and continuances only; Chapter 27, Chapter 2, and Chapter 23 sections were carried to later meetings without adopted manual changes.'}
  [ordered]@{id='src-4055919dde906ce1';date='2017-07-19';reason='Continuances only; Chapter 27, Chapter 23 section 3.7, and the Chapter 7 building-permit item were continued to August 2017 without adopted manual changes.'}
  [ordered]@{id='src-81b04c1358323136';date='2017-09-20';reason='Continuances only; Chapter 27 and Chapter 23 sections 3.1, 3.8, and 3.5 were continued to October 2017 without adopted manual changes.'}
  [ordered]@{id='src-fc539ddea39cd340';date='2017-10-18';reason='Scheduling and continuances only; Chapter 27 consideration was moved between meetings and other items continued, without adopted manual changes.'}
  [ordered]@{id='src-65575cfa5553d19a';date='2017-11-01';reason='Continuances only; Chapter 27 drafting standards and Chapter 23 section 3.3 were continued to the November 15, 2017 meeting without adopted manual changes.'}
)

$duplicates = @(
  [ordered]@{id='src-2448a4409efca23b';canonical='src-ff0cce054f5417f8';reason='Same April 15, 2015 Development Process Manual Executive Committee minutes published twice under different filenames. Normalized extracted text is 99.76 percent identical, differing only in PDF whitespace and hyphenation artifacts. Retain the descriptively named copy consistent with the rest of the series.'}
)

$superseded = @(
  [ordered]@{id='src-bfd859ce7e947d29';canonical='src-e6c9a8cffdca81f1';reason='Pre-adoption October 6, 2015 working copy of Development Process Manual Chapter 28. The adopted DPM-Chapter28-Adopted.pdf is already archived and validated as src-e6c9a8cffdca81f1.'}
  [ordered]@{id='src-65023909d5eda20e';canonical='src-e6c9a8cffdca81f1';reason='October 9, 2015 final-draft copy of Development Process Manual Chapter 28, superseded by the adopted version already archived and validated as src-e6c9a8cffdca81f1.'}
)

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$index = @{}
foreach ($candidate in @($inventory.candidates)) { $index[[string]$candidate.id] = $candidate }
$now = (Get-Date).ToUniversalTime().ToString('o')

function Add-Note($Candidate, [string]$Note) {
  $Candidate.processing_notes = @(@($Candidate.processing_notes | Where-Object { $_ }) + $Note | Sort-Object -Unique)
}

foreach ($item in $approved) {
  $c = $index[$item.id]
  if (-not $c) { throw "Missing candidate $($item.id)." }
  $c.status = 'approved for addition'
  $c.title = $item.title
  $c.date = $item.date
  $c.agency = 'City of Albuquerque'
  $c.description = $item.description
  $c.description_word_count = @($item.description -split '\s+' | Where-Object { $_ }).Count
  $c.proposed_canonical_page = $page
  $c.provenance_status = 'official City Planning document-library file verified at its authoritative URL'
  $c.validation_status = 'approved for addition: authoritative source HTTP 200, exact size and SHA-256 recorded, extracted minutes text reviewed for adopted actions'
  Add-Note $c "Adopted actions recorded: $($item.adopted)"
  Add-Note $c $precedent
  Add-Note $c 'Reviewed in the 2026-09-11 DPM Executive Committee minutes triage; approved for later addition. No site content change was made.'
  $c.updated_at = $now
}

foreach ($item in $excluded) {
  $c = $index[$item.id]
  if (-not $c) { throw "Missing candidate $($item.id)." }
  $c.status = 'excluded'
  $c.date = $item.date
  $c.exclusion_reason = $item.reason
  $c.validation_status = 'reviewed: excluded as routine committee minutes'
  Add-Note $c $precedent
  Add-Note $c 'Reviewed in the 2026-09-11 DPM Executive Committee minutes triage; extracted action-items section contains no adopted Development Process Manual change.'
  $c.updated_at = $now
}

foreach ($item in $duplicates) {
  $c = $index[$item.id]
  if (-not $c) { throw "Missing candidate $($item.id)." }
  $c.status = 'duplicate'
  $c.exclusion_reason = $item.reason
  $c.validation_status = 'resolved as duplicate by normalized extracted-text comparison'
  $c.cited_successors = @($item.canonical)
  Add-Note $c 'Reviewed in the 2026-09-11 DPM Executive Committee minutes triage.'
  $c.updated_at = $now
  $canon = $index[$item.canonical]
  if ($canon) {
    $canon.cited_predecessors = @(@($canon.cited_predecessors | Where-Object { $_ }) + $item.id | Sort-Object -Unique)
    Add-Note $canon "Canonical copy retained over duplicate $($item.id)."
  }
}

foreach ($item in $superseded) {
  $c = $index[$item.id]
  if (-not $c) { throw "Missing candidate $($item.id)." }
  $c.status = 'superseded'
  $c.exclusion_reason = $item.reason
  $c.validation_status = 'resolved as superseded by the adopted chapter already archived'
  $c.cited_successors = @($item.canonical)
  Add-Note $c 'Reviewed in the 2026-09-11 DPM chapter triage.'
  $c.updated_at = $now
}

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = $now
$open = @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned')
$next = @($inventory.candidates | Where-Object { $_.status -in $open } | Sort-Object id | Select-Object -First 1)
$inventory.next_pending_id = if ($next.Count) { $next[0].id } else { $null }

$json = $inventory | ConvertTo-Json -Depth 12
$full = [IO.Path]::GetFullPath($InventoryPath)
$temporary = "$full.tmp-$PID"
[IO.File]::WriteAllText($temporary, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $full -Force

$decision = [ordered]@{
  batch_id = 'dpm-executive-committee-minutes-2026-09-11'
  generated_at = $now
  source_library = $base
  target_page = $page
  method = 'Downloaded every candidate with the repository Download-Candidate.ps1, recorded exact size and SHA-256, extracted text with Extract-CandidatePdfBatch.ps1, parsed the ACTION ITEMS section of each set of minutes, and classified by whether the committee adopted a Development Process Manual change.'
  precedent = $precedent
  counts = [ordered]@{approved_for_addition=$approved.Count;excluded=$excluded.Count;duplicate=$duplicates.Count;superseded=$superseded.Count}
  approved_for_addition = @($approved | ForEach-Object {
    $c = $index[$_.id]
    [ordered]@{id=$_.id;title=$_.title;date=$_.date;authoritative_url=[string]$c.direct_file_url;size_bytes=$c.size_bytes;checksum_sha256=$c.checksum_sha256;adopted_actions=$_.adopted;description=$_.description;proposed_canonical_page=$page;link_check='HTTP 200'}
  })
  excluded = @($excluded | ForEach-Object { $c=$index[$_.id]; [ordered]@{id=$_.id;date=$_.date;authoritative_url=[string]$c.direct_file_url;reason=$_.reason} })
  duplicate = @($duplicates | ForEach-Object { $c=$index[$_.id]; [ordered]@{id=$_.id;canonical_id=$_.canonical;authoritative_url=[string]$c.direct_file_url;reason=$_.reason} })
  superseded = @($superseded | ForEach-Object { $c=$index[$_.id]; [ordered]@{id=$_.id;canonical_id=$_.canonical;authoritative_url=[string]$c.direct_file_url;reason=$_.reason} })
  safeguards = @('no site content change','no R2 upload','no commit, merge, or deploy')
}
$decision | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $DecisionPath -Encoding utf8

[pscustomobject]@{approved=$approved.Count;excluded=$excluded.Count;duplicate=$duplicates.Count;superseded=$superseded.Count;decision_path=$DecisionPath;next_pending_id=$inventory.next_pending_id} | ConvertTo-Json -Compress

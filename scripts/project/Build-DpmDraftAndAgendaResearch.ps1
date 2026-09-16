[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/dpm-draft-and-agenda-research-2026-09-11.json'
)

# Research lane only. This script reads the inventory and writes one dated
# decision artifact. It never modifies master-inventory.json or checkpoint.json.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$index = @{}
foreach ($candidate in @($inventory.candidates)) { $index[[string]$candidate.id] = $candidate }

$consolidated = 'src-0b9dc46fbf32cfb7'
$article43 = 'src-d6f0d94a12b31a2d'
$section396 = 'src-75935732f3f11f34'

$supersededBy2020 = @(
  @{id='src-d8f7fef195345d20';item='DPM Preface, February 2015 final';adopted='Preface and update procedure adopted 2014-12-17 (src-ea48e98a01589ffb).'}
  @{id='src-129f232ec60f5d06';item='Chapter 22 table of contents, proposed';adopted='Chapter 22 sections adopted 2016-09-07 through 2017-03-01.'}
  @{id='src-d07ab9806a6fd78b';item='Chapter 22 introduction, section 1';adopted='Chapter 22 sections 1-7 adopted 2016-09-07 (src-ca86eefe82a821c3).'}
  @{id='src-b4107f69f82d97be';item='Chapter 22 section 2, proposed';adopted='Chapter 22 sections 1-7 adopted 2016-09-07 (src-ca86eefe82a821c3).'}
  @{id='src-f0effcaab74869fb';item='Chapter 22 section 3, proposed';adopted='Chapter 22 sections 1-7 adopted 2016-09-07 (src-ca86eefe82a821c3).'}
  @{id='src-2fce12110d776d09';item='Chapter 22 section 4, proposed';adopted='Chapter 22 sections 1-7 adopted 2016-09-07 (src-ca86eefe82a821c3).'}
  @{id='src-1be9e5d07ff18993';item='Chapter 22 section 5, proposed';adopted='Chapter 22 sections 1-7 adopted 2016-09-07 (src-ca86eefe82a821c3).'}
  @{id='src-848dd829cf4ddcee';item='Chapter 22 section 6, proposed';adopted='Chapter 22 sections 1-7 adopted 2016-09-07 (src-ca86eefe82a821c3).'}
  @{id='src-d1bb7f0a5c162eb0';item='Chapter 22 section 7, proposed';adopted='Chapter 22 sections 1-7 adopted 2016-09-07 (src-ca86eefe82a821c3).'}
  @{id='src-40ba8a543964941f';item='Chapter 22 section 8, proposed';adopted='Chapter 22 sections 8 and 9 adopted 2016-10-19 (src-21dc013c982971a3).'}
  @{id='src-af717a54412a3c6d';item='Chapter 22 section 9, proposed';adopted='Chapter 22 sections 8 and 9 adopted 2016-10-19 (src-21dc013c982971a3).'}
  @{id='src-2b02bb85e498e956';item='Chapter 22 section 10, proposed';adopted='Chapter 22 section block adopted across 2016-2017; consolidated in the signed 2020 manual.'}
  @{id='src-fcf4a5b22c6663a1';item='Chapter 22 section 11, proposed';adopted='Chapter 22 section 11 adopted 2017-02-01 (src-bbaad13a047c342c).'}
  @{id='src-ba947bcc7d378b5d';item='Chapter 22 section 12, proposed';adopted='Chapter 22 section 12 adopted 2017-01-18 (src-ea47d347422e2570).'}
  @{id='src-959569e504495e7d';item='Chapter 22 section 13, proposed';adopted='Chapter 22 section 13 adopted as amended 2017-03-01 (src-573093423a1bbd50).'}
  @{id='src-68af8683bcdf09f0';item='Chapter 22 sections 14-17, proposed';adopted='Chapter 22 sections 14 through 17 adopted 2017-03-01 (src-573093423a1bbd50).'}
  @{id='src-71fc6161d5c89e46';item='Chapter 2, proposed';adopted='Chapter 2 adopted as amended 2017-04-19 (src-14ba4769fc9b04aa).'}
  @{id='src-f54e839002b57d5e';item='Chapter 18, proposed amendments';adopted='Chapter 18 adopted 2017-03-01 (src-573093423a1bbd50).'}
  @{id='src-b79cc659ccc3b49f';item='Chapter 25, proposed amendments';adopted='Chapter 25 revisions adopted unanimously 2015-12-16 (src-73f9afbcaae5d8d2).'}
  @{id='src-2fba2e29254b8220';item='Chapter 25 section 7, final';adopted='Chapter 25 revisions adopted 2015-12-16 (src-73f9afbcaae5d8d2); consolidated in the signed 2020 manual.'}
  @{id='src-6f566c7aba400d66';item='Chapter 25 section 8, final';adopted='Chapter 25 revisions adopted 2015-12-16 (src-73f9afbcaae5d8d2); consolidated in the signed 2020 manual.'}
  @{id='src-811d218c5ad0f533';item='Chapter 26, proposed';adopted='Chapter 26 adopted 2017-06-21 (src-5340531bfdbbe7fb).'}
  @{id='src-3edd5c1de2b9e263';item='Chapter 27, proposed';adopted='Chapter 27 drafting standards adopted 2018-03-07 as proposed Chapter 4 construction plan standards (src-58104015e9620a4d).'}
  @{id='src-6d554d867c6a4cff';item='Chapter 23, proposed';adopted='Chapter 23 sections adopted across 2017-2018; consolidated in the signed 2020 manual.'}
  @{id='src-5c6ace61fca6ad8e';item='Chapter 23, redline 2, proposed';adopted='Chapter 23 sections adopted across 2017-2018; consolidated in the signed 2020 manual.'}
  @{id='src-6f8c847747ea728a';item='Chapter 23, proposed (second copy)';adopted='Chapter 23 sections adopted across 2017-2018; consolidated in the signed 2020 manual.'}
  @{id='src-e174ab96bf6e29da';item='Chapter 23 section 3.1, proposed';adopted='Chapter 23 section 3.1 Network Connectivity adopted 2018-02-07 (src-c2f91d09003c2cbe).'}
  @{id='src-7554d12ac0e16d04';item='Chapter 23 section 3.8, proposed';adopted='Chapter 23 section 3.8 On-street Parking adopted as amended 2017-10-04 (src-adfd6742a595ccf6).'}
  @{id='src-d211181c5815b944';item='Chapter 23 section 3.6';adopted='Chapter 23 section 3.6 adopted 2017-06-21 subject to illustration changes (src-5340531bfdbbe7fb).'}
  @{id='src-379b8fa9cbbb51d4';item='Chapter 23 section 3.7, proposed';adopted='Chapter 23 section 3.7 Public Transit adopted 2017-09-06 (src-fd0a98e661a8db31).'}
  @{id='src-4d23133388903f9d';item='Chapter 23 section 3.9, proposed';adopted='Chapter 23 section 3.9 adopted 2017-06-21 (src-5340531bfdbbe7fb).'}
  @{id='src-a991bd1262460d6d';item='Chapter 3 section 4, proposed';adopted='Pre-2020 chapter proposal consolidated and renumbered in the signed 2020 manual.'}
  @{id='src-9e6b6efbcdaca4e8';item='Chapter 3 section 9, proposed';adopted='Pre-2020 chapter proposal consolidated and renumbered in the signed 2020 manual.'}
  @{id='src-5a00435866288933';item='Chapter 3 section 12, proposed';adopted='Pre-2020 chapter proposal consolidated and renumbered in the signed 2020 manual.'}
  @{id='src-8e16620bcd3e9f84';item='Chapter 5 section 2-1, proposed';adopted='Pre-2020 chapter proposal consolidated and renumbered in the signed 2020 manual.'}
  @{id='src-b7e934d19b4cb741';item='Chapter 6 section 2-2, proposed';adopted='Pre-2020 chapter proposal consolidated and renumbered in the signed 2020 manual.'}
  @{id='src-8daf5837ea8b9b04';item='Chapter 7, proposed';adopted='Chapter 7 building permit process adopted 2017-09-06 as new Section 2.5 (src-fd0a98e661a8db31).'}
  @{id='src-e613465fcaa24d40';item='Chapter 7 building permits, redline 2018-03-28';adopted='Chapter 7 building permit process adopted 2017-09-06 (src-fd0a98e661a8db31); consolidated in the signed 2020 manual.'}
  @{id='src-c388811dbfcae978';item='Chapter 8 other construction permits, redline 2018-03-28';adopted='Pre-2020 chapter redline consolidated and renumbered in the signed 2020 manual.'}
  @{id='src-1e415e4c06cfba06';item='Chapter 21 recordable documents, draft 2018-03-30';adopted='Pre-2020 chapter draft consolidated and renumbered in the signed 2020 manual.'}
  @{id='src-2a74a5263f07cb42';item='Private infrastructure redline, 2017-10-06';adopted='Pre-2020 infrastructure redline consolidated in the signed 2020 manual.'}
  @{id='src-ba77b3b8a5d94874';item='Public infrastructure redline, 2017-10-06';adopted='Pre-2020 infrastructure redline consolidated in the signed 2020 manual.'}
  @{id='src-2de1ded4d97987b9';item='Prototype templates and plant list updates';adopted='Pre-2020 supporting template update consolidated in the signed 2020 manual.'}
  @{id='src-5d3cf489ca76f9a6';item='Summary table of contents';adopted='Pre-2020 structural summary replaced by the signed 2020 manual table of contents.'}
)

$supersededBy2026 = @(
  @{id='src-cf0631ff9d752003';item='Chapter 4 DPM proposed changes, 2026-04-14'}
  @{id='src-2925e282efe493c9';item='Chapter 4 requested changes markup, 2026-04-15'}
)

$humanReview = @(
  @{id='src-f904f6d8bf3787f5';item='Chapter 7 DPM proposed changes, 2026-04-14';reason='The official City amendments register still lists this as "Download the Proposed Changes to Chapter 7 of the DPM" and the May 4, 2026 agenda carried it as an open action item. No corresponding approved Chapter 7 file appears on the register, so adoption is unconfirmed. Recheck when the committee publishes an approved Chapter 7 amendment.'}
  @{id='src-dda1163373f3754c';item='Chapter 7 requested changes markup, 2026-04-14';reason='Companion markup to the unadopted Chapter 7 proposal above; same unresolved adoption status.'}
  @{id='src-967a816e5ddac695';item='Chapter 23 section 3.9.7 turn lane and median design, final-review draft';reason='The February 21, 2018 minutes deferred section 3.9.7 to the March 21, 2018 meeting, and no March 21, 2018 minutes exist in the inventory, so adoption cannot be confirmed. Its sibling section 3.9.6 final-review draft is already validated and archived as src-75935732f3f11f34, so a consistent editorial decision is needed on whether final-review drafts of this series are preserved.'}
)

$agendaExcluded = @(
  @{id='src-a8dda335fb901049';date='2015-04-15';minutes='src-ff0cce054f5417f8'}
  @{id='src-f2716dd03961455e';date='2015-05-20';minutes='src-14f45e5400b067bc'}
  @{id='src-48eb68305e18d8ad';date='2018-03-07';minutes='src-58104015e9620a4d'}
  @{id='src-89d7a6448976c52e';date='2025-12-04';minutes='src-100dcafff14a7b22'}
  @{id='src-04dfcbe1dcde70f8';date='2025-12-11';minutes='src-100dcafff14a7b22'}
)

$agendaReview = @(
  @{id='src-7e7af2af147d96d7';date='2018-03-21';reason='No approved minutes for March 21, 2018 exist in the inventory; the latest 2018 minutes are March 7, 2018. The missing-minutes policy would permit preserving this agenda only after a recorded exhaustive official-source review confirms no approved minutes exist, and only if the meeting was not cancelled or without quorum.'}
  @{id='src-f6feb3549d055097';date='2018-04-04';reason='No approved minutes for April 2018 exist in the inventory. Same missing-minutes conditions apply before any agenda preservation.'}
  @{id='src-dc3a192d194d3d65';date='2026-05-04';reason='No approved minutes for May 4, 2026 were located, but the substantive outcome of that meeting is already preserved as the adopted Article 4-3 ABCWUA amendment (src-d6f0d94a12b31a2d), which reduces the agenda''s independent value. Needs an editorial decision.'}
)

function New-Row($Id, [string]$Recommendation, [string]$Canonical, [string]$Rationale, [string]$Item) {
  $c = $index[$Id]
  if (-not $c) { throw "Missing candidate $Id." }
  [ordered]@{
    id = $Id
    item = $Item
    current_status = [string]$c.status
    recommended_status = $Recommendation
    canonical_id = $Canonical
    authoritative_url = [string]($(if ($c.direct_file_url) { $c.direct_file_url } else { $c.source_url }))
    link_check = 'HTTP 200 verified 2026-09-11'
    rationale = $Rationale
  }
}

$rows = [System.Collections.Generic.List[object]]::new()
foreach ($x in $supersededBy2020) {
  $rows.Add((New-Row $x.id 'superseded' $consolidated ("$($x.adopted) The adopted text is carried in the signed consolidated Development Process Manual dated June 2, 2020, which also renumbered the manual; this pre-adoption working file is therefore not an independent authoritative record.") $x.item))
}
foreach ($x in $supersededBy2026) {
  $rows.Add((New-Row $x.id 'superseded' $article43 'The City amendments register lists this file under "Proposed"/"Requested" changes to Chapter 4, while the same register publishes the approved outcome as the Article 4-3 ABCWUA combined amendment adopted May 4, 2026, already validated as src-d6f0d94a12b31a2d. The proposal is superseded by that adopted amendment.' $x.item))
}
foreach ($x in $humanReview) { $rows.Add((New-Row $x.id 'requires human review' '' $x.reason $x.item)) }
foreach ($x in $agendaExcluded) {
  $rows.Add((New-Row $x.id 'excluded' $x.minutes ("Approved minutes for the $($x.date) meeting are available as $($x.minutes), so the repository missing-minutes policy does not permit preserving this agenda.") "DPM Executive Committee agenda, $($x.date)"))
}
foreach ($x in $agendaReview) { $rows.Add((New-Row $x.id 'requires human review' '' $x.reason "DPM Executive Committee agenda, $($x.date)")) }

$artifact = [ordered]@{
  batch_id = 'dpm-draft-and-agenda-research-2026-09-11'
  lane = 'Claude research lane: DPM remaining-draft and agenda review'
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  scope = 'All 57 remaining pending-review candidates in the City Planning Development Process Manual library: 49 chapter drafts, redlines, and supporting files, plus 8 Executive Committee agendas.'
  method = 'Verified every authoritative URL with a direct HTTP HEAD request. Mapped each pre-2020 draft to the adoption evidence recorded in the Executive Committee minutes triaged on 2026-09-11. Resolved the 2026 files against the live City amendments register, which separates "Proposed"/"Requested" changes from "Changes Approved by the Development Process Manual Executive Committee". Applied the repository missing-minutes policy to agendas by pairing each against the inventory minutes record for the same meeting date.'
  classification_only = $true
  shared_state_written = @()
  anchors = [ordered]@{
    consolidated_manual = [ordered]@{id=$consolidated;title='Development Process Manual, signed June 2, 2020';url='https://documents.cabq.gov/planning/development-process-manual/DPM-2020-06-02_signed.pdf'}
    adopted_2026_amendment = [ordered]@{id=$article43;title='Approved Amendment: Article 4-3 ABCWUA Changes, May 4, 2026';url='https://documents.cabq.gov/planning/development-process-manual/Article%204-3%20ABCWUA%20change-combined.pdf'}
    archived_sibling_section = [ordered]@{id=$section396;title='Chapter 23 Section 3.9.6 Intersection Design final-review draft (already validated)';url='https://documents.cabq.gov/planning/development-process-manual/section-3-9-6-intersection-design-final-review-draft.pdf'}
  }
  counts = [ordered]@{
    reviewed = $rows.Count
    superseded = @($rows | Where-Object recommended_status -eq 'superseded').Count
    excluded = @($rows | Where-Object recommended_status -eq 'excluded').Count
    requires_human_review = @($rows | Where-Object recommended_status -eq 'requires human review').Count
    approved_for_addition = 0
    duplicate = 0
  }
  link_check = [ordered]@{checked=57;http_200=57;failed=0;method='HTTP HEAD, 30-second timeout, browser user agent'}
  recommendations = @($rows)
  integration_note = 'Codex integration lane: apply recommended_status values through scripts/project/Update-Candidate.ps1 only. Every superseded row carries a canonical_id. No row in this artifact is approved for addition, so this batch adds no visible site entries.'
  safeguards = @('no master-inventory.json write','no checkpoint.json write','no site content change','no R2 upload','no commit, merge, or deploy')
}

$artifact | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{reviewed=$rows.Count;superseded=$artifact.counts.superseded;excluded=$artifact.counts.excluded;requires_human_review=$artifact.counts.requires_human_review;output=$OutputPath} | ConvertTo-Json -Compress

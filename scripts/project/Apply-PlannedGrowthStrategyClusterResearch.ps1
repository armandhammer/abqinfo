[CmdletBinding()]
param(
  [string]$ResearchPath = 'project-state/discovery/planned-growth-strategy-cluster-research-2026-09-11.json',
  [string]$UndiscoveredPath = 'project-state/discovery/undiscovered-documents-research-2026-09-14.json',
  [string]$DecisionPath = 'project-state/discovery/planned-growth-strategy-decision-2026-09-19.json',
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ById($rows, [string]$id) { @($rows | Where-Object { ($_.PSObject.Properties['id'] -and $_.id -eq $id) -or ($_.PSObject.Properties['candidate_id'] -and $_.candidate_id -eq $id) })[0] }

$research = Get-Content -Raw -Encoding UTF8 -LiteralPath $ResearchPath | ConvertFrom-Json
$undiscovered = Get-Content -Raw -Encoding UTF8 -LiteralPath $UndiscoveredPath | ConvertFrom-Json
$approved = @($research.approved_for_addition)
$duplicates = @($research.duplicate)
$human = @($research.requires_human_review)
$excluded = @($research.excluded)

# The original PGS research predates discovery integration.  These two exact
# siblings were subsequently registered from that same research, so they are
# part of this family rather than new independent work.
foreach ($id in @('src-bc069f52331eb293','src-cd72192082580abe')) {
  $filename = if ($id -eq 'src-bc069f52331eb293') { 'Part2-4.pdf' } else { 'Part2-6.pdf' }
  $row = @($undiscovered.add_to_inventory | Where-Object { $_.filename -eq $filename })[0]
  if (-not $row) { throw "Missing subsequently registered PGS chapter $id." }
  $chapter = if ($id -eq 'src-bc069f52331eb293') { '4.0' } else { '6.0' }
  $approved += [pscustomobject]@{ id=$id; authoritative_url=$row.authoritative_url; recommended_status='approved for addition'; title=$row.title; description=$row.description; size_bytes=$row.size_bytes; checksum_sha256=$row.checksum_sha256; pages=if($id -eq 'src-bc069f52331eb293'){12}else{16}; chapter=$chapter; printed_pages=if($id -eq 'src-bc069f52331eb293'){'157-168'}else{'211-218'}; proposed_canonical_page='content/development-land-use/zoning-ido.md'; cross_listings=$row.cross_listings; evidence=$row.evidence; package_id='pgs-part2-preferred-alternative' }
}

# Two formerly-held records are now supported by the reconciled package map.
$part1held = ById @($research.split_package_reconciliation.pgs_part_1.chapter_manifest) 'src-0bd664780961f148'
$part2held = ById @($research.split_package_reconciliation.pgs_part_2_preferred_alternative.chapter_manifest) 'src-0e133db868401e77'
if (-not $part1held -or -not $part2held) { throw 'PGS held-record reconciliation evidence is missing.' }
$duplicates += [pscustomobject]@{ id='src-0bd664780961f148'; authoritative_url='https://www.cabq.gov/council/documents/pgs/Part1-6.pdf/view'; recommended_status='duplicate'; size_bytes=$part1held.size_bytes; checksum_sha256=$part1held.checksum_sha256; canonical_id='src-9aeb5f621800da58'; basis='A chapter extract of complete Part 1: normalized token coverage in Part1.pdf is 1.0000 and seven chapter page counts equal its 286 pages.' }
$part2base = ById @($approved) 'src-08b6b68b53336462'
$approved += [pscustomobject]@{ id='src-0e133db868401e77'; authoritative_url='https://www.cabq.gov/council/documents/pgs/Part2-10.pdf/view'; recommended_status='approved for addition'; title='Planned Growth Strategy, Part 2 (Preferred Alternative) — Chapter 10.0: Growth Strategy Techniques Used in Other Locations'; description="Chapter 10.0 of the City and County growth study compares growth-management techniques used in other locations as one of the obtainable chapters establishing and implementing Albuquerque's Preferred Alternative."; size_bytes=$part2held.size_bytes; checksum_sha256=$part2held.checksum_sha256; pages=$part2held.pdf_pages; chapter='10.0'; printed_pages='281-342'; proposed_canonical_page='content/development-land-use/zoning-ido.md'; cross_listings=$part2base.cross_listings; evidence='63 pages, mapped from the Part 2 table of contents; previously held only pending package reconciliation, now discharged by the saved family research.'; package_id='pgs-part2-preferred-alternative' }

if ($approved.Count -ne 12 -or $duplicates.Count -ne 7 -or $human.Count -ne 3 -or $excluded.Count -ne 1) { throw "Unexpected PGS disposition counts: approved=$($approved.Count), duplicate=$($duplicates.Count), human=$($human.Count), excluded=$($excluded.Count)." }

$qualityPart1 = [ordered]@{reviewed_document_content=$true;visual_inspection_completed=$true;standalone_public_value='high';information_density='substantial';series_relationship='serial';publication_form='consolidated_master';page_count=286;extracted_word_count=0;rationale="The complete first volume is the authoritative readable record of the strategy's findings, alternatives, infrastructure costs, policy review, and economic analysis; it retains the whole document rather than seven contextless extracts.";aggregation_rationale='Part 1 is one 286-page original whose seven chapter files have complete measured textual coverage within it. The complete City original preserves the intended sequence and eliminates fragmentary standalone presentation.'}
$qualityPart2 = [ordered]@{reviewed_document_content=$true;visual_inspection_completed=$true;standalone_public_value='medium';information_density='substantial';series_relationship='serial';publication_form='standalone';page_count=0;extracted_word_count=0;rationale='Each obtainable chapter is a substantive, sequenced component of the City and County preferred-alternative study and remains useful only with an explicit family note identifying the unavailable summary chapter.';aggregation_rationale='The City serves Part 2 only as separate chapter files, not a combined original. Keeping the obtainable City originals in their documented order avoids inventing a derivative volume while making the permanent Chapter 3.0 gap visible.';standalone_exception='No combined Part 2 original exists and the City source permanently lacks Chapter 3.0. Each chapter must therefore remain an original delivery with an explicit multipart-family relationship and missing-chapter notice.'}

foreach ($row in $approved) {
  $template = if ($row.id -eq 'src-9aeb5f621800da58') { $qualityPart1 } else { $qualityPart2 }
  $quality = [ordered]@{}
  foreach ($key in $template.Keys) { $quality[$key] = $template[$key] }
  if ($row.id -ne 'src-9aeb5f621800da58') { $quality.page_count=[int]$row.pages }
  if ($row.id -eq 'src-9aeb5f621800da58') { $quality.page_count=286 }
  $note = "Planned Growth Strategy family decision 2026-09-19: $($row.evidence) Exact City source, size, SHA-256, and package relationship retained; inventory-only pending separately authorized R2 archival and public-byte verification."
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $row.id -InventoryPath $InventoryPath -Set @{status='approved for addition';source_url=[string]$row.authoritative_url;direct_file_url=([string]$row.authoritative_url -replace '/view$','');agency='City of Albuquerque';title=[string]$row.title;description=[string]$row.description;size_bytes=[int64]$row.size_bytes;checksum_sha256=[string]$row.checksum_sha256;proposed_canonical_page=[string]$row.proposed_canonical_page;implementation_location=$null;implementation_locations=@();cross_listing_approved=$false;validation_status='saved family research, visual/content review, and quality assessment retained; inventory-only, R2 archival and public-byte verification not run';provenance_status='authoritative City source, exact-file measurements, and family relationship retained';processing_notes=@($note);exclusion_reason=$null} | Out-Null
  $row | Add-Member -NotePropertyName quality_assessment -NotePropertyValue ([pscustomobject]$quality)
}
foreach ($row in $duplicates) {
  $note = "Planned Growth Strategy family decision 2026-09-19: duplicate component of canonical $($row.canonical_id). $($row.basis)"
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $row.id -InventoryPath $InventoryPath -Set @{status='duplicate';source_url=[string]$row.authoritative_url;direct_file_url=([string]$row.authoritative_url -replace '/view$','');agency='City of Albuquerque';size_bytes=[int64]$row.size_bytes;checksum_sha256=[string]$row.checksum_sha256;proposed_canonical_page=$null;implementation_location=$null;implementation_locations=@();cross_listing_approved=$false;validation_status='terminal family decision: duplicate component of complete Part 1';provenance_status='authoritative City source and measured component-to-canonical relationship retained';processing_notes=@($note);exclusion_reason=$note} | Out-Null
}
foreach ($row in $human) {
  $note = "Planned Growth Strategy family decision 2026-09-19: $($row.why_not_decided_here) $($row.question_for_human)"
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $row.id -InventoryPath $InventoryPath -Set @{status='requires human review';source_url=[string]$row.authoritative_url;direct_file_url=([string]$row.authoritative_url -replace '/view$','');agency='City of Albuquerque';title=[string]$row.draft_title;size_bytes=[int64]$row.size_bytes;checksum_sha256=[string]$row.checksum_sha256;proposed_canonical_page=$null;implementation_location=$null;implementation_locations=@();cross_listing_approved=$false;validation_status='requires human review: enacted ordinance not located';provenance_status='authoritative City bill copy, exact-file measurements, and enactment uncertainty retained';processing_notes=@($note);exclusion_reason=$null} | Out-Null
}

& "$PSScriptRoot/Update-MasterInventoryAggregates.ps1" -InventoryPath $InventoryPath | Out-Null
$decision=[ordered]@{schema_version=1;artifact_type='ordinary_queue_family_decision';recorded_at='2026-09-19';queue_selection=[ordered]@{generated_next_pending_id='src-05ec421cb265b29a';method='Sorted pending-review order was filtered against CURRENT.md, checkpoint blockers, and durable completed/gated artifacts: skip MS4, Prescription Trails, code-enforcement, LGCC, Capital Spending, completed NMDOT, Municipal Development procurement and standard forms, theory-of-change, and archive-gated items. The first remaining pending ID was src-08b6b68b53336462.';selected_candidate='src-08b6b68b53336462'};family=[ordered]@{name='Planned Growth Strategy';directory='https://www.cabq.gov/council/documents/pgs';scope_candidate_ids=@($approved.id+$duplicates.id+$human.id+$excluded.id|Sort-Object);definition='Complete Part 1, its seven delivery chapters, the separately delivered Part 2 Preferred Alternative chapters, three related enactment-bill records, and the collection landing page.'};source_provenance=[ordered]@{research_artifacts=@($ResearchPath,$UndiscoveredPath);part_1='Complete 286-page original; seven chapter extracts each have 1.0000 normalized token coverage within the canonical.';part_2='No combined original. Ten numbered chapters are obtainable through eleven files because Chapter 1.0 is split; Chapter 3.0, pages 131-156, is unavailable from the City.';filename_trap='Part2.pdf is a different City and County unification study and is not in scope.'};dispositions=[ordered]@{approved_for_addition=@($approved);duplicate=@($duplicates);requires_human_review=@($human);excluded=@($excluded)};quality_assessments=@($approved|ForEach-Object{[ordered]@{id=$_.id;quality_assessment=$_.quality_assessment}});family_relationships=[ordered]@{part_1_canonical='src-9aeb5f621800da58';part_1_duplicate_components=@($duplicates.id|Sort-Object);part_2_obtainable_files=@($approved|Where-Object id -ne 'src-9aeb5f621800da58'|ForEach-Object id);part_2_missing_chapter=[ordered]@{chapter='3.0';title='Preferred Alternative Summary';printed_pages='131-156';source_result='HTTP 404; absent from City listing and inventory'}};external_gates=@('No R2 mutation or public content action occurred. All approved originals remain inventory-only pending separately authorized R2 archival and public-byte verification. Any future Part 2 public presentation must visibly identify missing Chapter 3.0 and must not synthesize a combined PDF.');ordinary_queue_handoff=[ordered]@{next_actionable_candidate='src-090b501b1579de50';family='Municipal Development online-form / related form sequence requires family scoping before any decision.';method="The next pending-review ID after applying this PGS family's completed and human-review dispositions, while retaining all existing external gates."};safeguards_observed=[ordered]@{r2_mutation=$false;public_content_changed=$false;pdf_built=$false;merge_or_deploy=$false}}
[IO.File]::WriteAllText([IO.Path]::GetFullPath($DecisionPath),($decision|ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false))
Write-Output ($decision|ConvertTo-Json -Depth 5)

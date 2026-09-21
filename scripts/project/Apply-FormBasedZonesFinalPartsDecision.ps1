[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/form-based-zones-final-parts-family-decision-2026-09-20.json',
  [string]$QueuePath = 'project-state/discovery/ordinary-queue-next-position-2026-09-20-post-form-based-zones.json',
  [string]$CurrentPath = 'project-state/CURRENT.md',
  [string]$CheckpointPath = 'project-state/checkpoint.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8Json($Value, [string]$Path) {
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($Path), ($Value | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
}

$ids = @('src-77df51d4334f3749', 'src-bdb71a8eaf8a29fa')
$inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json -DateKind String
$partA = @($inventory.candidates | Where-Object id -eq $ids[0])
$partC = @($inventory.candidates | Where-Object id -eq $ids[1])
$partB = @($inventory.candidates | Where-Object id -eq 'src-05176d26d35effd3')
if ($partA.Count -ne 1 -or $partC.Count -ne 1 -or $partB.Count -ne 1) { throw 'Expected final Form Based Zones Parts A, B, and C exactly once.' }
if ($partA[0].status -notin @('pending review', 'requires human review') -or $partC[0].status -notin @('pending review', 'requires human review')) { throw 'The two scoped final-part records must be pending review or already held for human review.' }
if ($partB[0].status -ne 'requires human review') { throw 'Final Part B must retain its existing enactment-review hold.' }

$familyNote = 'Family decision 2026-09-20: final April 2, 2009 Part A is a 59-page component of the three-part Section 14-16-3-22 Form Based Zones delivery. It is complementary to final Parts B and C, not a complete code or independently publishable record. The final package and its enactment status remain unresolved; hold with Part B for bounded human review. No archive or public-content action.'
$notesA = @($partA[0].processing_notes | Select-Object -Unique)
if ($notesA -notcontains $familyNote) { $notesA += $familyNote }
$setA = @{
  status = 'requires human review'
  title = 'Form Based Zones, Section 14-16-3-22, Part A (Final)'
  date = '2009-04-02'
  validation_status = 'requires human review: final three-part historical zoning-code package is incomplete in isolation and the associated Form Based Zones enactment has not been established.'
  processing_notes = $notesA
}
& "$PSScriptRoot/Update-Candidate.ps1" -Id $ids[0] -Set $setA -InventoryPath $InventoryPath | Out-Null

$inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json -DateKind String
$partC = @($inventory.candidates | Where-Object id -eq $ids[1])
$familyNote = 'Family decision 2026-09-20: final April 2, 2009 Part C is a 28-page component of the three-part Section 14-16-3-22 Form Based Zones delivery. It is complementary to final Parts A and B, not a complete code or independently publishable record. The final package and its enactment status remain unresolved; hold with Part B for bounded human review. No archive or public-content action.'
$notesC = @($partC[0].processing_notes | Select-Object -Unique)
if ($notesC -notcontains $familyNote) { $notesC += $familyNote }
$setC = @{
  status = 'requires human review'
  title = 'Form Based Zones, Section 14-16-3-22, Part C (Final)'
  date = '2009-04-02'
  validation_status = 'requires human review: final three-part historical zoning-code package is incomplete in isolation and the associated Form Based Zones enactment has not been established.'
  processing_notes = $notesC
}
& "$PSScriptRoot/Update-Candidate.ps1" -Id $ids[1] -Set $setC -InventoryPath $InventoryPath | Out-Null

$inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json -DateKind String
$finalParts = @($inventory.candidates | Where-Object { $_.id -in @($ids + 'src-05176d26d35effd3') } | Sort-Object id)
$quality = @(
  [ordered]@{ id = $ids[0]; pages = 59; size_bytes = 1276278; information_density = 'High: substantive general regulations and section organization, but only one lettered component.'; visual_inspection = 'Saved research verified the City PDF container and opening page; no new render was needed for this inventory-only decision.'; document_quality = 'Authoritative City-hosted final PDF, exact checksum saved, and a substantial stable legal-text component.'; standalone_public_value = 'Insufficient alone because Part A omits the final zones and components material in Parts B and C.'; series_component_relationship = 'Part A of a three-part final delivery with Parts B and C.'; intended_publication_form = 'Only a complete, enacted-status-resolved historical three-part package, if future archival and editorial gates are authorized.'; rationale = 'A standalone listing would incorrectly imply an intelligible complete form-based zoning code.' },
  [ordered]@{ id = $ids[1]; pages = 28; size_bytes = 718729; information_density = 'High: substantive building-type, street-design, and parking standards, but only one lettered component.'; visual_inspection = 'Saved research verified the City PDF container and opening page; no new render was needed for this inventory-only decision.'; document_quality = 'Authoritative City-hosted final PDF, exact checksum saved, and a substantial stable legal-text component.'; standalone_public_value = 'Insufficient alone because Part C omits the final general regulations and zones in Parts A and B.'; series_component_relationship = 'Part C of a three-part final delivery with Parts A and B.'; intended_publication_form = 'Only a complete, enacted-status-resolved historical three-part package, if future archival and editorial gates are authorized.'; rationale = 'A standalone listing would misrepresent a partial zoning-code delivery as a self-contained record.' }
)
$decision = [ordered]@{
  schema_version = 1
  artifact_type = 'ordinary_queue_family_decision'
  recorded_at = '2026-09-20'
  selection_artifact = 'project-state/discovery/ordinary-queue-next-position-2026-09-20-post-public-service-guides.json'
  saved_evidence = @('project-state/discovery/undiscovered-documents-research-2026-09-14.json', 'project-state/discovery/form-based-code-cluster-research-2026-09-11.json')
  family = [ordered]@{
    name = 'Form Based Zones final parts'
    scope_candidate_ids = $ids
    related_final_part_b = 'src-05176d26d35effd3'
    issuing_body = 'City of Albuquerque; the files are City-hosted zoning-code deliveries associated with City Council Form Based Zones proposals.'
    exact_context = 'The April 2, 2009 final (G3b) delivery of former Zoning Code Section 14-16-3-22 Form Based Zones, replacing the February 27, 2009 G3a revision. G3b is three lettered parts: A, B, and C. The 2017 Integrated Development Ordinance replaced Chapter 14 Article 16, so this is obsolete pre-IDO material.'
    complete_canonical_record = 'No combined final City document was found. The City collection listing exposes final Part B, while saved server research located final Parts A and C. The related bills O-07-116 and O-08-58 have blank enactment numbers; no enacted ordinance or stronger codified record was established in the bounded saved research.'
  }
  dispositions = @(
    [ordered]@{ id = $ids[0]; status = 'requires human review'; title = 'Form Based Zones, Section 14-16-3-22, Part A (Final)'; date = '2009-04-02'; issuing_body = 'City of Albuquerque'; role = 'Final Part A, general regulations and section organization'; disposition = 'Hold as a complementary partial component; do not retain or publish independently.'; proposed_future_placement = 'If the entire three-part final package is later shown enacted and archived/verified, Zoning and IDO under a clearly historical pre-IDO heading; no cross-listing justified.' },
    [ordered]@{ id = $ids[1]; status = 'requires human review'; title = 'Form Based Zones, Section 14-16-3-22, Part C (Final)'; date = '2009-04-02'; issuing_body = 'City of Albuquerque'; role = 'Final Part C, components including building types, street design, and parking'; disposition = 'Hold as a complementary partial component; do not retain or publish independently.'; proposed_future_placement = 'If the entire three-part final package is later shown enacted and archived/verified, Zoning and IDO under a clearly historical pre-IDO heading; no cross-listing justified.' }
  )
  quality_assessments = $quality
  relationship_findings = [ordered]@{
    truly_final_components = $true
    complementary_not_duplicate = $true
    partial_delivery = $true
    independently_publishable = $false
    pre_ido_obsolete = $true
    part_b_state = 'src-05176d26d35effd3 remains requires human review; it is the final Part B and completes neither Part A nor Part C alone.'
    predecessor_successors = 'Part A succeeds src-4ce0f7387bab68d1 and Part C succeeds src-a94103538515dadb. The final generation is not byte-identical to its predecessors and has documented substantive growth/revision.'
  }
  unresolved_question = 'Locate an enacted ordinance or otherwise establish the disposition of the Form Based Zones proposals before deciding whether the complete final G3b package has enduring historic-record value. Do not infer adoption from a filename marked final.'
  archive_publication_gate = 'No R2 mutation, Hugo content change, PR, merge, deployment, or public placement occurred. Any future package requires separate authorization, preservation of all three original final parts, exact public-byte verification, and an editorial decision that labels it as historic pre-IDO material.'
  ordinary_queue_handoff = [ordered]@{ next_actionable_candidate = 'src-e0624ecba79f3f17'; family = 'UNM 2040 strategic framework'; instruction = 'This is the sole remaining filtered ordinary residual. Do not begin research in this task.' }
  safeguards_observed = [ordered]@{ source_refetch = $false; r2_mutation = $false; hugo_content_changed = $false; pull_request_created = $false; merge_or_deploy = $false }
}
Write-Utf8Json $decision $DecisionPath

$queue = [ordered]@{
  schema_version = 1
  artifact_type = 'ordinary_queue_filtered_position'
  recorded_at = '2026-09-20'
  supersedes = 'project-state/discovery/ordinary-queue-next-position-2026-09-20-post-public-service-guides.json'
  method = 'Queried the current master-inventory pending-review rows after applying the Form Based Zones final-parts decision, then retained the durable completed-family and external-gate filter from the superseded queue artifact and CURRENT.md. No UNM source fetch or research occurred.'
  sources = [ordered]@{ source_inventory = $InventoryPath; source_current = $CurrentPath; source_checkpoint = $CheckpointPath; prior_queue = 'project-state/discovery/ordinary-queue-next-position-2026-09-20-post-public-service-guides.json'; completed_family = $DecisionPath }
  counts = [ordered]@{ pending_review_current = $inventory.counts.'pending review'; completed_or_gated_pending_covered = ($inventory.counts.'pending review' - 1); filtered_pending_review = 1; next_cluster_count = 1; residual_clusters = 1 }
  residual_clusters = @([ordered]@{ family = 'UNM 2040 strategic framework'; count = 1; first_candidate_id = 'src-e0624ecba79f3f17'; candidate_ids = @('src-e0624ecba79f3f17'); basis = 'Retained-source audit summary identifies this as the only remaining pending candidate outside durable completed and externally gated scopes; no decision has been made.' })
  next_actionable_cluster = [ordered]@{ family = 'UNM 2040 strategic framework'; count = 1; first_candidate_id = 'src-e0624ecba79f3f17'; candidate_ids = @('src-e0624ecba79f3f17'); selection_rule = 'Only residual pending candidate after applying durable completed-family, requires-human-review, and external-gate dispositions.'; next_instruction = 'Review only when separately tasked; do not fetch or research it as part of this queue-position handoff.' }
  safeguards_observed = [ordered]@{ next_family_research_started = $false; source_downloads_for_next_family = $false; r2_mutation = $false; hugo_content_changed = $false; pull_request_created = $false; merge_or_deploy = $false }
}
Write-Utf8Json $queue $QueuePath

$current = Get-Content -Raw -Encoding UTF8 $CurrentPath
$old = 'The post-public-service-guides filtered queue is recorded in `project-state/discovery/ordinary-queue-next-position-2026-09-20-post-public-service-guides.json`. Three pending records remain outside durable completed/gated scopes; the next genuinely actionable residual family is the two Form Based Zones final parts beginning `src-77df51d4334f3749`. Do not begin researching it without a new task instruction. The one-record UNM 2040 strategic framework remains later in the filtered queue.'
$new = 'The Form Based Zones final-parts family is resolved in `project-state/discovery/form-based-zones-final-parts-family-decision-2026-09-20.json`: the April 2, 2009 final Part A and Part C PDFs are genuine complementary components of former Zoning Code Section 14-16-3-22, but not complete independently publishable records. Both are requires human review with final Part B because no combined final document or enacted ordinance was established; this is obsolete pre-IDO material. No R2 or public-content action occurred. The recomputed filtered queue is recorded in `project-state/discovery/ordinary-queue-next-position-2026-09-20-post-form-based-zones.json`; its only ordinary residual is the one-record UNM 2040 strategic framework. Do not begin it without a new task instruction.'
if ($current.Contains($old)) {
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($CurrentPath), $current.Replace($old, $new), [Text.UTF8Encoding]::new($false))
} elseif (-not $current.Contains($new)) {
  throw 'CURRENT.md queue paragraph did not match either the expected prior or completed handoff.'
}

$checkpoint = Get-Content -Raw -Encoding UTF8 $CheckpointPath | ConvertFrom-Json -DateKind String
$checkpoint.recorded_at = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$checkpoint.completed_item_range = 'Resolved the two-record Form Based Zones final-parts family: the April 2, 2009 Part A and Part C PDFs are genuine final, high-density components of former Zoning Code Section 14-16-3-22, but they are complementary partial deliveries with final Part B and no established enactment. Both now require human review; no R2, Hugo, PR, merge, or deployment action occurred. Recomputed the filtered ordinary queue: the sole remaining ordinary residual is the UNM 2040 strategic framework, src-e0624ecba79f3f17.'
$checkpoint.total_candidates = @($inventory.candidates).Count
$checkpoint.counts_by_status = $inventory.counts
$checkpoint.remaining_nonterminal = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') }).Count
$checkpoint.next_pending_id = $inventory.next_pending_id
$checkpoint.resume_command = 'Next ordinary handoff: review the one-record UNM 2040 strategic framework, src-e0624ecba79f3f17, only when separately tasked. Keep the separately gated 2014 MS4 body-and-attachments package and all durable completed families excluded; do not reopen the Form Based Zones final parts absent enactment-status evidence.'
Write-Utf8Json $checkpoint $CheckpointPath

Write-Output "PASS: resolved $($ids -join ', ') and wrote $DecisionPath plus $QueuePath"

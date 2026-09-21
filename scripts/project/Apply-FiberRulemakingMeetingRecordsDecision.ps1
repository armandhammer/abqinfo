[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$CheckpointPath = 'project-state/checkpoint.json',
  [string]$DecisionPath = 'project-state/discovery/fiber-rulemaking-meeting-records-decision-2026-09-19.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$transcriptId = 'src-09592fba403c1e2f'
$chatId = 'src-2883388452797b58'
$rulesId = 'src-b8b28358abc9a2de'
$correspondenceId = 'src-05b68a5758490499'
$transcriptUrl = 'https://www.cabq.gov/municipaldevelopment/documents/shawns-meeting-notes_otter_ai.pdf'
$chatUrl = 'https://www.cabq.gov/municipaldevelopment/documents/chat-from-public-meeting-on-fiber-optic-hearing.pdf'
$rulesUrl = 'https://www.cabq.gov/municipaldevelopment/documents/regulations-governing-public-right-of-way-excavation-and-barricading-for-fiber-infrastructure-purposes-final-fiber-rules-6-27-25.pdf'
$correspondenceUrl = 'https://www.cabq.gov/municipaldevelopment/documents/regulations-governing-fiber-6-5-25-hearing-correspondence-pdf-email-complaints.pdf'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$byId = @{}
foreach ($candidate in $inventory.candidates) { $byId[$candidate.id] = $candidate }
foreach ($id in @($transcriptId, $chatId, $rulesId, $correspondenceId)) {
  if (-not $byId.ContainsKey($id)) { throw "Missing expected fiber-rulemaking record $id." }
}
if ($byId[$correspondenceId].status -ne 'requires human review') { throw 'The protected correspondence record no longer has its required human-review status.' }

function Add-Note([object]$Candidate, [string]$Note) {
  $notes = @($Candidate.processing_notes)
  if ($notes -notcontains $Note) { $notes += $Note }
  return $notes
}

$transcriptReason = 'Unreviewed Otter.ai-generated transcript and summary of the June 5, 2025 fiber-rulemaking hearing. The City hosts the file, but its own heading identifies Shawn''s Meeting Notes, it is timestamped and materially garbled, and it carries no City adoption, certification, or review indication. It must not be presented as official minutes or as a reliable account of the hearing.'
$chatReason = 'Meeting-chat exhaust from the June 5, 2025 fiber-rulemaking hearing. It includes participant names, contact information, third-party Fireflies.ai boilerplate, audio complaints, and uncurated comments. The adopted regulations are the durable official record; the separately retained correspondence file remains under its existing privacy-sensitive human-review gate.'
$rulesNote = "Fiber rulemaking meeting-records decision 2026-09-19: retained as the authoritative final four-page City regulations following the June 5 hearing; full-GET evidence records 124,053 bytes and SHA-256 068cc29a12e49e546a56d83f247ba2ecb7f05b80e3f4a03d4e0b2077891eb687."
$transcriptNote = "Fiber rulemaking meeting-records decision 2026-09-19: full-GET evidence records a 29-page, 126,927-byte PDF and SHA-256 dc0a42ea83998ce66b0e1add2a5c52048f12d3d6a41d4431dcbc48fc4908206b. It is an unreviewed Otter.ai transcript/summary, not approved minutes."
$chatNote = "Fiber rulemaking meeting-records decision 2026-09-19: full-GET evidence records a three-page, 119,054-byte PDF and SHA-256 7fd4846bd508a3e466576a11574c172e22a21fce504e8547b9d012a88306bade. It is an uncurated Zoom chat log, not a suitable standalone publication record."

& "$PSScriptRoot/Update-Candidate.ps1" -Id $rulesId -InventoryPath $InventoryPath -Set @{
  status = 'approved for addition'
  source_url = "$rulesUrl/view"
  direct_file_url = $rulesUrl
  agency = 'City of Albuquerque'
  title = 'Regulations Governing Public Right of Way Excavation and Barricading for Fiber Infrastructure Purposes'
  date = '2025'
  file_type = 'PDF'
  size_bytes = [int64]124053
  checksum_sha256 = '068cc29a12e49e546a56d83f247ba2ecb7f05b80e3f4a03d4e0b2077891eb687'
  provenance_status = 'official City Plone document-library item; final regulations text, full-GET byte evidence, and hearing-context relationship retained'
  proposed_canonical_page = 'content/development-land-use/development-process.md'
  description = 'The City''s final rules for fiber installation in the public right of way set licensing, notice, construction, coordination, restoration, complaint-response, and enforcement requirements after the June 2025 rulemaking hearing.'
  implementation_location = $null
  implementation_locations = @()
  cross_listing_approved = $true
  validation_status = 'inventory-only family decision: approved pending separately authorized R2 archival, public-byte verification, and future editorial implementation'
  exclusion_reason = $null
  processing_notes = (Add-Note $byId[$rulesId] $rulesNote)
} | Out-Null

& "$PSScriptRoot/Update-Candidate.ps1" -Id $transcriptId -InventoryPath $InventoryPath -Set @{
  status = 'excluded'; source_url = "$transcriptUrl/view"; direct_file_url = $transcriptUrl; agency = 'City of Albuquerque'; title = "Shawn's Meeting Notes (Otter.ai transcript), June 5, 2025"; date = '2025-06-05'; file_type = 'PDF'; size_bytes = [int64]126927; checksum_sha256 = 'dc0a42ea83998ce66b0e1add2a5c52048f12d3d6a41d4431dcbc48fc4908206b'; provenance_status = 'official City Plone document-library item; original delivery and unreviewed Otter.ai derivative relationship retained'; proposed_canonical_page = $null; description = $null; implementation_location = $null; implementation_locations = @(); cross_listing_approved = $false; validation_status = 'terminal family decision: excluded unreviewed automated transcript; not official minutes'; exclusion_reason = $transcriptReason; processing_notes = (Add-Note $byId[$transcriptId] $transcriptNote)
} | Out-Null

& "$PSScriptRoot/Update-Candidate.ps1" -Id $chatId -InventoryPath $InventoryPath -Set @{
  status = 'excluded'; source_url = "$chatUrl/view"; direct_file_url = $chatUrl; agency = 'City of Albuquerque'; title = 'Chat Log from the June 5, 2025 Fiber Rulemaking Hearing'; date = '2025-06-05'; file_type = 'PDF'; size_bytes = [int64]119054; checksum_sha256 = '7fd4846bd508a3e466576a11574c172e22a21fce504e8547b9d012a88306bade'; provenance_status = 'official City Plone document-library item; original delivery and meeting-exhaust relationship retained'; proposed_canonical_page = $null; description = $null; implementation_location = $null; implementation_locations = @(); cross_listing_approved = $false; validation_status = 'terminal family decision: excluded meeting-chat exhaust; privacy-sensitive correspondence remains human review'; exclusion_reason = $chatReason; processing_notes = (Add-Note $byId[$chatId] $chatNote)
} | Out-Null

& "$PSScriptRoot/Update-MasterInventoryAggregates.ps1" -InventoryPath $InventoryPath | Out-Null

$decision = [ordered]@{
  schema_version = 1
  artifact_type = 'ordinary_queue_family_decision'
  recorded_at = '2026-09-19'
  queue_selection = [ordered]@{ generated_next_pending_id = 'src-05ec421cb265b29a'; selected_candidate = $transcriptId; method = 'CURRENT.md and checkpoint.json identify this as the next genuinely actionable ordinary candidate after completed and externally gated families are skipped. Existing saved research was reused rather than repeated.' }
  family = [ordered]@{ name = 'June 5, 2025 fiber-rulemaking hearing records'; definition = 'The smallest coherent City document-library unit for the public hearing: final regulations, Otter transcript, Zoom chat log, and the separately held correspondence/complaints file. This scope excludes the broader Municipal Development library, separate broadband-program materials, and unrelated excavation forms.'; scope_candidate_ids = @($correspondenceId, $chatId, $transcriptId, $rulesId | Sort-Object) }
  source_provenance = [ordered]@{
    event = 'June 5, 2025 public hearing on proposed regulations governing public right-of-way excavation and barricading for fiber infrastructure purposes.'
    authoritative_city_items = @($transcriptUrl, $chatUrl, $rulesUrl, $correspondenceUrl)
    city_listing_context = 'The direct City item page calls the target “fiber optic public hearing notes from Shawn 6.5.25” and describes it as notes taken by Shawn Maden; it is not filed in a dedicated minutes collection.'
    transcript_finding = 'The 29-page target begins “Shawn''s Meeting Notes,” includes an Otter-style timestamped transcript, and records Shahab Biazar opening the hearing. Its text contains obvious transcription errors and no attestation, approval, or certification.'
    chat_finding = 'The three-page chat log begins with Fireflies.ai notetaker help text and includes participant names, comments, and email/contact information. It calls chat comments admissible, but it is still uncurated meeting exhaust rather than a stand-alone historical record.'
    final_rules_finding = 'The four-page final regulations are headed CITY OF ALBUQUERQUE and state their title, authority, scope, requirements, enforcement, and the applicable right-of-way construction controls. They are the authoritative durable output of this rulemaking context.'
    correspondence_gate = 'The 79,030,032-byte correspondence/complaints PDF remains requires-human-review under project-state/discovery/permits-forms-regulations-cluster-research-2026-09-12.json because it mixes the public rulemaking record with named residents'' complaints and contact-sensitive material. Its status is intentionally not changed here.'
    reused_research_artifacts = @('project-state/discovery/permits-forms-regulations-cluster-research-2026-09-12.json', 'project-state/discovery/municipaldevelopment-flat-remainder-cluster-research-2026-09-13.json', 'project-state/discovery/cabq-dmd-document-library-crawl.json')
  }
  dispositions = [ordered]@{
    approved_for_addition = @([ordered]@{ id = $rulesId; title = 'Regulations Governing Public Right of Way Excavation and Barricading for Fiber Infrastructure Purposes'; disposition = 'approved for addition'; reason = 'Official four-page final City regulations with clear authority, scope, enforceable requirements, and independent public value.' })
    excluded = @([ordered]@{ id = $transcriptId; title = "Shawn's Meeting Notes (Otter.ai transcript), June 5, 2025"; disposition = 'excluded'; reason = $transcriptReason }, [ordered]@{ id = $chatId; title = 'Chat Log from the June 5, 2025 Fiber Rulemaking Hearing'; disposition = 'excluded'; reason = $chatReason })
    duplicate = @()
    superseded = @()
    requires_human_review = @([ordered]@{ id = $correspondenceId; title = 'Fiber Infrastructure Rulemaking: Public Hearing Correspondence and Complaints, June 2025'; disposition = 'requires human review retained'; reason = 'Existing privacy-sensitive public-record disposition retained without reopening it.' })
  }
  family_relationships = [ordered]@{ final_regulations = $rulesId; related_meeting_exhaust = @($transcriptId, $chatId); privacy_gated_comment_record = $correspondenceId; relationship = 'The regulations are a stronger authoritative outcome, but no formal supersession relationship is asserted for the transcript or chat; they are excluded because they are unreviewed/uncurated derivatives with misleading-publication and privacy concerns.' }
  quality_assessments = @([ordered]@{ id = $rulesId; visual_inspection = 'Four-page born-digital City regulations; title, section hierarchy, and substantive provisions are legible and complete.'; measured_content = '4 pages; 124,053 bytes; SHA-256 068cc29a12e49e546a56d83f247ba2ecb7f05b80e3f4a03d4e0b2077891eb687; substantive rules cover authority/scope, signage, notices, timing, coordination, restoration, complaints, and enforcement.'; standalone_public_value = 'High: authoritative City rules governing fiber work in the public right of way.'; information_density = 'High for a four-page regulation; each section sets material operative requirements.'; series_component_relationship = 'Final regulatory output related to, but not a duplicate of, the June 5 hearing records.'; intended_publication_form = 'One separately labelled regulations record after authorized R2 archival and exact public-byte verification.'; rationale = 'The official final regulations can be understood independently and are materially stronger than unreviewed hearing exhaust.' })
  placement_review = [ordered]@{ canonical_page = 'content/development-land-use/development-process.md'; approved_records = @($rulesId); cross_listing = [ordered]@{ page = 'content/transportation/roadway-projects/_index.md'; decision = 'useful future cross-listing'; rationale = 'The rules regulate construction work in City street rights of way.' } }
  unresolved_issues_or_external_gates = @('No R2 mutation, public-content edit, synthetic PDF, merge, or deployment is authorized or proposed. The approved regulations remain inventory-only pending separately authorized R2 archival, exact public-byte verification, and future editorial implementation.', "Do not reopen $correspondenceId without a human privacy/public-record publication decision.")
  ordinary_queue_handoff = [ordered]@{ next_actionable_candidate = 'src-09a0152fb526fcba'; family = 'Council O-24-13 amendment-sheet family; scope the related legislative record and amendment deliveries before deciding the isolated June 17, 2024 amendment.'; method = 'Next nonterminal ordinary candidate in deterministic ID order after this completed family while retaining all CURRENT.md/checkpoint skip rules and existing requires-human-review/external gates. Saved council-amendments research exists but must be scoped before integration.' }
  safeguards_observed = [ordered]@{ r2_mutation = $false; public_content_changed = $false; pdf_built = $false; merge_or_deploy = $false }
}
[IO.File]::WriteAllText([IO.Path]::GetFullPath($DecisionPath), ($decision | ConvertTo-Json -Depth 14), [Text.UTF8Encoding]::new($false))

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$checkpoint = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$checkpoint.recorded_at = (Get-Date).ToUniversalTime().ToString('o')
$checkpoint.completed_item_range = 'Completed the four-record June 5, 2025 fiber-rulemaking hearing family: final City regulations approved inventory-only; Otter transcript and Zoom chat log excluded; privacy-sensitive correspondence remains requires human review. Durable artifact: project-state/discovery/fiber-rulemaking-meeting-records-decision-2026-09-19.json. No R2, public-content, synthetic-PDF, merge, or deployment action occurred.'
$checkpoint.total_candidates = @($inventory.candidates).Count
$checkpoint.counts_by_status = $inventory.counts
$checkpoint.remaining_nonterminal = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') }).Count
$checkpoint.next_pending_id = $inventory.next_pending_id
$checkpoint.resume_command = 'Skip the externally gated MS4 package, Prescription Trails, code-enforcement Notices and Orders, LGCC agenda family, completed NMDOT families, completed Municipal Development procurement family, the two separately R2-gated standard forms, and the privacy-sensitive fiber correspondence record. The next genuinely actionable ordinary candidate is src-09a0152fb526fcba (June 17, 2024 O-24-13 Council amendment); scope its amendment/document family before deciding it.'
[IO.File]::WriteAllText([IO.Path]::GetFullPath($CheckpointPath), ($checkpoint | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))

$decision | ConvertTo-Json -Depth 5

[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$CheckpointPath = 'project-state/checkpoint.json',
  [string]$DecisionPath = 'project-state/discovery/mra-appeal-form-family-decision-2026-09-19.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$candidateId = 'src-090b501b1579de50'
$legacyId = 'src-cb776cdbd1f3ec08'
$onlineUrl = 'https://documents.cabq.gov/planning/online-forms/MRA-Appeal-Form.pdf'
$legacyUrl = 'https://documents.cabq.gov/planning/UDD/MRA/MRA-Appeal-Form.pdf'
$size = [int64]42712
$sha256 = 'f87a15739db517f2dbeb4f2c1ee85d2e973f5566af1a9178420ade6cf219bee2'
$reason = 'This is a revised-May-2015 Metropolitan Redevelopment Agency appeal application form. It is a transactional administrative form for a live appeal process, not a substantive public plan, study, enacted record, or historical source for the site taxonomy.'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$candidate = @($inventory.candidates | Where-Object id -eq $candidateId)
$legacy = @($inventory.candidates | Where-Object id -eq $legacyId)
if ($candidate.Count -ne 1 -or $legacy.Count -ne 1) { throw 'Expected exactly the pending and legacy MRA Appeal Form records.' }
$candidate = $candidate[0]
$legacy = $legacy[0]
if ($legacy.status -ne 'excluded' -or $legacy.size_bytes -ne $size -or $legacy.checksum_sha256 -ne $sha256) { throw 'Legacy MRA Appeal Form evidence drifted.' }

$note = "MRA Appeal Form family decision 2026-09-19: full GET evidence for $onlineUrl is a one-page PDF (42,712 bytes; SHA-256 $sha256) revised May 2015. It is the exact byte-identical City delivery alias of excluded $legacyId at $legacyUrl; both URLs serve the same transactional appeal form."
$notes = @($candidate.processing_notes)
if ($notes -notcontains $note) { $notes += $note }
& "$PSScriptRoot/Update-Candidate.ps1" -Id $candidateId -InventoryPath $InventoryPath -Set @{
  status = 'excluded'
  source_url = $onlineUrl
  direct_file_url = $onlineUrl
  agency = 'City of Albuquerque'
  size_bytes = $size
  checksum_sha256 = $sha256
  proposed_canonical_page = $null
  implementation_location = $null
  implementation_locations = @()
  cross_listing_approved = $false
  validation_status = 'terminal family decision: excluded transactional form; exact City alias relationship verified'
  provenance_status = 'authoritative City source, full-GET metadata, and exact delivery-alias relationship retained'
  processing_notes = $notes
  exclusion_reason = $reason
} | Out-Null
& "$PSScriptRoot/Update-MasterInventoryAggregates.ps1" -InventoryPath $InventoryPath | Out-Null

$decision = [ordered]@{
  schema_version = 1
  artifact_type = 'ordinary_queue_family_decision'
  recorded_at = '2026-09-19'
  queue_selection = [ordered]@{
    generated_next_pending_id = 'src-05ec421cb265b29a'
    selected_candidate = $candidateId
    method = 'CURRENT.md and checkpoint.json identify src-090b501b1579de50 as the next genuinely actionable ordinary candidate after completed and externally gated families are skipped.'
  }
  family = [ordered]@{
    name = 'MRA Appeal Form delivery-alias family'
    definition = 'The two City-hosted URLs in inventory that deliver the same May 2015 Metropolitan Redevelopment Agency appeal application form. This scope excludes the broader online-forms directory, MRA plans and maps, and unrelated Municipal Development documents.'
    scope_candidate_ids = @($candidateId, $legacyId)
  }
  source_provenance = [ordered]@{
    authoritative_urls = @($onlineUrl, $legacyUrl)
    online_forms_parent_url = 'https://documents.cabq.gov/planning/online-forms/'
    legacy_mra_parent_url = 'https://documents.cabq.gov/planning/UDD/MRA/'
    online_forms_verification = "Full GET recorded 2026-09-13: PDF signature 25504446, $size bytes, SHA-256 $sha256. City PDF text identifies a one-page MRA / Albuquerque Development Commission appeal form, requires an RFP/matter description, standing basis, notice of decision, and `$500 fee, and says Revised: May 2015."
    legacy_verification = "Existing excluded record $legacyId retains the same $size-byte size and SHA-256 $sha256, with a staged City-source copy and 2026-09-11 reconciliation decision."
    alias_evidence = 'Exact size and SHA-256 match across the two City delivery paths; they are delivery aliases, not separate versions or substantive companions.'
    relevant_city_context = 'The current City MRA hub describes MRA redevelopment and ADC proposal review, while this form is a transaction-specific appeal intake sheet rather than durable MRA program material.'
    reused_research_artifacts = @('project-state/discovery/council-projects-planning-forms-cluster-research-2026-09-13.json', 'project-state/discovery/downloaded-candidate-reconciliation-decisions-2026-09-11.json')
  }
  dispositions = [ordered]@{
    excluded = @(
      [ordered]@{ id = $candidateId; title = 'MRA-Appeal-Form.pdf'; authoritative_url = $onlineUrl; disposition = 'excluded'; reason = $reason; related_record = $legacyId },
      [ordered]@{ id = $legacyId; title = 'MRA-Appeal-Form.pdf'; authoritative_url = $legacyUrl; disposition = 'excluded'; reason = 'Previously terminally excluded on the same transactional-form grounds; retained as the historical City delivery alias, not as a canonical publication record.'; related_record = $candidateId }
    )
    approved_for_addition = @()
    duplicate = @()
    superseded = @()
    requires_human_review = @()
  }
  family_relationships = [ordered]@{
    delivery_aliases = @($candidateId, $legacyId)
    publication_canonical = $null
    rationale = 'Neither alias is an appropriate public archive canonical because the shared object is a blank, live-process transaction form. The alias relationship is retained as provenance and duplicate-delivery evidence only.'
  }
  quality_assessments = @()
  placement_review = [ordered]@{
    approved_records = @()
    canonical_page = $null
    cross_listing = [ordered]@{ decision = 'not applicable'; rationale = 'No record is approved for addition.' }
  }
  unresolved_issues_or_external_gates = @('No unresolved classification issue remains for this two-record family. Existing external archive and public-content gates remain unchanged; no archive or publication action is proposed because both records are excluded.')
  ordinary_queue_handoff = [ordered]@{
    next_actionable_candidate = 'src-09592fba403c1e2f'
    family = 'Municipal Development document-library record: shawns meeting notes otter ai.pdf; scope its immediate coherent family before deciding it.'
    method = 'Next pending-review ID in deterministic order after this family decision, after retaining all CURRENT.md/checkpoint skip rules and completed or externally gated families.'
  }
  safeguards_observed = [ordered]@{ r2_mutation = $false; public_content_changed = $false; pdf_built = $false; merge_or_deploy = $false }
}
[IO.File]::WriteAllText([IO.Path]::GetFullPath($DecisionPath), ($decision | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json -DateKind String
$checkpoint = Get-Content -Raw -Encoding UTF8 -LiteralPath $CheckpointPath | ConvertFrom-Json -DateKind String
$checkpoint.recorded_at = (Get-Date).ToUniversalTime().ToString('o')
$checkpoint.completed_item_range = 'Completed the two-record MRA Appeal Form delivery-alias family: both City aliases are excluded transactional administrative forms. Durable artifact: project-state/discovery/mra-appeal-form-family-decision-2026-09-19.json. No R2, public-content, synthetic-PDF, merge, or deployment action occurred.'
$checkpoint.total_candidates = @($inventory.candidates).Count
$checkpoint.counts_by_status = $inventory.counts
$checkpoint.remaining_nonterminal = @($inventory.candidates | Where-Object { $_.status -in @('pending review','approved for addition','downloading','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed') }).Count
$checkpoint.next_pending_id = $inventory.next_pending_id
$checkpoint.resume_command = 'Skip the externally gated MS4 package, Prescription Trails, code-enforcement Notices and Orders, LGCC agenda family, completed NMDOT families, completed Municipal Development procurement family, and the two separately R2-gated standard forms. The next genuinely actionable ordinary candidate is src-09592fba403c1e2f (shawns meeting notes otter ai.pdf); scope its immediate coherent Municipal Development document-library family before deciding it.'
[IO.File]::WriteAllText([IO.Path]::GetFullPath($CheckpointPath), ($checkpoint | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))

$decision | ConvertTo-Json -Depth 5

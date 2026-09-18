[CmdletBinding()]
param(
  [string]$MasterPath = 'project-state/master-inventory.json',
  [string]$GatePath = 'project-state/discovery/2014-ms4-family-package-gate-2026-09-18.json',
  [string]$CandidateMappingPath = 'project-state/discovery/undiscovered-documents-candidate-integration-2026-09-17.json',
  [string]$ResearchPath = 'project-state/discovery/undiscovered-documents-research-2026-09-14.json',
  [string]$OutputPath = 'project-state/discovery/2014-ms4-package-decision-2026-09-18.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-Json([string]$Path) { Get-Content -Raw -Encoding UTF8 -LiteralPath $Path | ConvertFrom-Json -DateKind String }
function Write-Json([object]$Value, [string]$Path) {
  $text = ($Value | ConvertTo-Json -Depth 30) + "`r`n"
  [IO.File]::WriteAllText([IO.Path]::GetFullPath($Path), $text, [Text.UTF8Encoding]::new($false))
}

$master = Read-Json $MasterPath
$gate = Read-Json $GatePath
$mapping = Read-Json $CandidateMappingPath
$research = Read-Json $ResearchPath
$ids = @($gate.scope.candidate_ids)
if ($ids.Count -ne 28 -or @($ids | Sort-Object -Unique).Count -ne 28) { throw 'MS4 gate must contain exactly 28 unique candidate IDs.' }
if ([int]$gate.scope.composition.main_body_count -ne 1 -or [int]$gate.scope.composition.attachment_count -ne 27) { throw 'MS4 gate composition must be one main body plus 27 attachments.' }

$masterById = @{}
foreach ($record in @($master.candidates)) { $masterById[[string]$record.id] = $record }
$mappingById = @{}
foreach ($record in @($mapping.records)) { $mappingById[[string]$record.candidate_id] = $record }
$researchByRef = @{}
foreach ($record in @($research.add_to_inventory)) { $researchByRef[[string]$record.local_ref] = $record }

$components = @()
foreach ($id in $ids) {
  if (-not $masterById.ContainsKey($id) -or -not $mappingById.ContainsKey($id)) { throw "Missing saved MS4 evidence for $id." }
  $candidate = $masterById[$id]
  $saved = $mappingById[$id]
  $researchRecord = $researchByRef[[string]$saved.local_ref]
  if ($null -eq $researchRecord) { throw "Missing source research for $($saved.local_ref)." }
  $sensitivity = if ($id -eq 'src-e1ba11c182777207') {
    'Before any archive/publication action, visually inspect for named facility contacts, telephone numbers, and email addresses; do not expose a compilation containing unresolved personal-contact detail.'
  } elseif ($id -eq 'src-77e4073db8101308') {
    'Before any archive/publication action, visually inspect the field log for complainant-identifying detail; retain only through the package workflow, not as a standalone record.'
  } else { $null }
  $components += [pscustomobject][ordered]@{
    local_ref = $saved.local_ref
    candidate_id = $id
    role = if ($id -eq $gate.scope.composition.main_body_candidate_id) { 'main_body' } else { 'attachment' }
    title = $candidate.title
    authoritative_source_url = $saved.source_url
    size_bytes = [int64]$saved.size_bytes
    checksum_sha256 = $saved.checksum_sha256
    master_status = $candidate.status
    description = $researchRecord.description
    evidence = $researchRecord.evidence
    prearchive_sensitivity_review = $sensitivity
  }
}
$totalBytes = [int64](@($components | Measure-Object -Property size_bytes -Sum).Sum)
if ($totalBytes -ne [int64]$gate.scope.total_verified_source_bytes) { throw "MS4 byte total $totalBytes differs from gate total $($gate.scope.total_verified_source_bytes)." }

$artifact = [pscustomobject][ordered]@{
  schema_version = 1
  artifact_type = 'ms4_2014_package_research_decision'
  recorded_at = (Get-Date).ToUniversalTime().ToString('o')
  family = '2014 MS4 Annual Report'
  source_artifacts = [pscustomobject][ordered]@{
    package_gate = $GatePath
    candidate_mapping = $CandidateMappingPath
    saved_research = $ResearchPath
    master_inventory = $MasterPath
  }
  established_facts = [pscustomobject][ordered]@{
    authoritative_publisher = 'City of Albuquerque'
    reporting_context = '2014 annual report to EPA under NPDES permit NMS000101, due April 1, 2015.'
    component_count = 28
    composition = 'One report main body plus 27 attachments; the cover letter/certification statement is one of those attachments.'
    verified_source_total_bytes = $totalBytes
    exact_source_hashes_saved_in = $CandidateMappingPath
    all_components_currently_remain = 'pending review'
  }
  package_quality_assessment = [pscustomobject][ordered]@{
    visual_inspection = 'Saved research includes rendered inspection where needed; a fresh visual review is still required before any public archival compilation is generated.'
    measured_content = 'The main body is 703,823 bytes and expressly relies on 27 attachments. The full official package totals 54,354,234 bytes; attachments contain independently substantive monitoring, control, enforcement, mapping, and certification evidence.'
    standalone_public_value = 'The main body alone is incomplete, while individual attachments would be a long and misleading fragment list. The annual report package has substantial public value as one federal stormwater-compliance record.'
    series_component_relationship = 'All 28 City-hosted originals are components of one dated annual-report submission. They must be retained as individual provenance-bearing originals even if later presented through one package-level resource.'
    intended_publication_form = 'One curated 2014 MS4 Annual Report package-level archive resource on the Stormwater and Drainage page, only after every selected original is archived and publicly byte-verified. Do not create 28 standalone site entries.'
    rationale = 'A provenance-preserving compilation or package landing resource would improve browsing without implying that the main body alone is complete. It must identify the main body and every attachment in source order.'
  }
  decision = [pscustomobject][ordered]@{
    state = 'research_complete_archive_and_publication_externally_gated'
    local_inventory_action = 'No master-record status change in this decision. Preserve all 28 candidates as pending review until an authorized archive plan and sensitivity check are complete.'
    future_archive_action = 'If explicitly authorized, retrieve each official original, reverify exact source bytes and SHA-256 against the saved mapping, archive originals non-overwriting, verify public downloads, then generate and validate the package-level presentation resource.'
    future_content_action = 'After archival verification, add one contextual annual-report entry to content/public-works/stormwater-drainage.md with an archive link, the City source directory/context, and a component inventory; do not list sparse attachments separately.'
    unresolved_prearchive_review = @(
      'Industrial/high-risk facility call list: check named facility contacts, telephone numbers, and email addresses.',
      '311 complaint map and field log: check for complainant-identifying detail.'
    )
    prohibited_now = @('No R2 upload, overwrite, rename, deletion, or metadata mutation.','No PDF compilation generation.','No site-content change or deployment.')
  }
  components = $components
}
Write-Json $artifact $OutputPath
$artifact | ConvertTo-Json -Compress -Depth 30

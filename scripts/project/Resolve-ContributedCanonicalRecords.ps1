[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/contributed-document-decisions-2026-08-14.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [string]$CatalogPath = 'project-state/contributed-document-review-2026-08-14.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json

function Get-One([string]$Id) {
  $record = @($inventory.candidates | Where-Object id -eq $Id)
  if ($record.Count -ne 1) { throw "Expected one record for '$Id'; found $($record.Count)." }
  return $record[0]
}

function Copy-Provenance([string]$FromId, [string]$ToId) {
  $from = Get-One $FromId
  $to = Get-One $ToId
  foreach ($field in @(
    'source_url','direct_file_url','r2_url','r2_key','r2_etag','r2_last_modified',
    'agency','title','date','file_type','size_bytes','checksum_sha256','parent_url',
    'referring_urls','discovery_path','discovery_method','crawl_depth',
    'cited_predecessors','cited_successors','provenance_status',
    'proposed_canonical_page','description','description_word_count','processing_notes',
    'local_path'
  )) {
    $to.$field = $from.$field
  }
  $to.status = 'validated'
  $to.validation_status = 'passed: authoritative lineage documented, original R2 object verified byte-identical, description and single-page placement validated, full Hugo validation passed'
  $to.exclusion_reason = $null
  $to.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  $from.status = 'duplicate'
  $from.validation_status = 'duplicate provenance record retained; canonical implemented record fully validated'
  $from.exclusion_reason = "Duplicate discovery record for implemented candidate $ToId."
  $from.updated_at = $to.updated_at
}

Copy-Provenance 'src-1231cfe4a3029341' 'src-6349e5f02f95ba83'
Copy-Provenance 'src-6b6788fdbc69b3ca' 'src-1ab4b8188d3eeda8'

foreach ($id in @(
  'src-bf834f9e01200726',
  'src-1a2f6ca6cba245d2',
  'src-444e6a6bc9b21bb9',
  'src-7bbe0a9dbd29fb97'
)) {
  $record = Get-One $id
  $record.status = 'validated'
  $record.validation_status = 'passed: authoritative lineage documented, original R2 object verified byte-identical, description and single-page placement validated, full Hugo validation passed'
  $record.exclusion_reason = $null
  $record.updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$girard = Get-One 'src-0a69860a80fbe98a'
$girard.status = 'requires human review'
$girard.validation_status = 'passed: original R2 object verified byte-identical, description and single-page placement validated, full Hugo validation passed; exact annotated-file provenance remains unresolved'
$girard.exclusion_reason = $null
$girard.updated_at = (Get-Date).ToUniversalTime().ToString('o')

$counts = [ordered]@{}
foreach ($status in $inventory.allowed_statuses) { $counts[$status] = @($inventory.candidates | Where-Object status -eq $status).Count }
$inventory.counts = [pscustomobject]$counts
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$inventory | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $InventoryPath -Encoding utf8

if (Test-Path -LiteralPath $DecisionPath) {
  $decisions = Get-Content -Raw -LiteralPath $DecisionPath | ConvertFrom-Json
  $canonicalByDecisionId = @{
    'src-1231cfe4a3029341' = 'src-6349e5f02f95ba83'
    'src-6b6788fdbc69b3ca' = 'src-1ab4b8188d3eeda8'
  }
  foreach ($addition in $decisions.additions) {
    $canonicalId = if ($canonicalByDecisionId.ContainsKey([string]$addition.id)) { $canonicalByDecisionId[[string]$addition.id] } else { [string]$addition.id }
    $terminal = if ($canonicalId -eq 'src-0a69860a80fbe98a') { 'requires human review' } else { 'validated' }
    $addition | Add-Member -NotePropertyName canonical_inventory_id -NotePropertyValue $canonicalId -Force
    $addition | Add-Member -NotePropertyName terminal_status -NotePropertyValue $terminal -Force
    $addition | Add-Member -NotePropertyName public_validation -NotePropertyValue 'byte-identical to original by exact size and SHA-256' -Force
  }
  if (Test-Path -LiteralPath $R2InventoryPath) {
    $r2 = Get-Content -Raw -LiteralPath $R2InventoryPath | ConvertFrom-Json
    $decisions | Add-Member -NotePropertyName post_upload_r2_objects -NotePropertyValue ([int]$r2.object_count) -Force
    $decisions | Add-Member -NotePropertyName post_upload_r2_bytes -NotePropertyValue ([int64]$r2.total_bytes) -Force
  }
  $decisions.exact_next_action = 'No document-review work remains in this batch. Review the pull request; the Girard annotated schematic remains explicitly marked requires human review for exact-file provenance.'
  $decisions | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $DecisionPath -Encoding utf8

  if (Test-Path -LiteralPath $CatalogPath) {
    $catalog = Get-Content -Raw -LiteralPath $CatalogPath | ConvertFrom-Json
    foreach ($item in $catalog.items) {
      $addition = @($decisions.additions | Where-Object filename -eq $item.filename)
      $duplicate = @($decisions.duplicates | Where-Object filename -eq $item.filename)
      if ($addition.Count -eq 1) {
        $item.review_status = [string]$addition[0].terminal_status
        $item.decision = [string]$addition[0].decision
        $item.matching_inventory_id = [string]$addition[0].canonical_inventory_id
        $item.proposed_canonical_page = [string]$addition[0].proposed_canonical_page
        $item.official_source_url = [string]$addition[0].source_url
        $item.r2_url = [string]$addition[0].r2_url
        $item.implementation_location = [string]$addition[0].proposed_canonical_page
      } elseif ($duplicate.Count -eq 1) {
        $item.review_status = 'duplicate'
        $item.decision = 'Exact SHA-256 duplicate; no new upload or site entry required.'
        $item.matching_inventory_id = [string]$duplicate[0].matching_inventory_id
      }
    }
    $catalog.pending_review = @($catalog.items | Where-Object review_status -eq 'pending review').Count
    $catalog.exact_inventory_duplicates = @($catalog.items | Where-Object review_status -eq 'duplicate').Count
    $catalog.generated_at = (Get-Date).ToUniversalTime().ToString('o')
    $catalog | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $CatalogPath -Encoding utf8
  }
}

$ids = @('src-6349e5f02f95ba83','src-1ab4b8188d3eeda8','src-bf834f9e01200726','src-1a2f6ca6cba245d2','src-0a69860a80fbe98a','src-444e6a6bc9b21bb9','src-7bbe0a9dbd29fb97')
$inventory.candidates | Where-Object id -in $ids | Select-Object id,status,title,implementation_location,validation_status

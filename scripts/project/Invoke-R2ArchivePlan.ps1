[CmdletBinding(SupportsShouldProcess)]
param(
  [Parameter(Mandatory)][string]$PlanPath,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Raw -LiteralPath $PlanPath | ConvertFrom-Json
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$currentR2Bytes = [int64]$plan.current_r2_bytes
$plannedBytes = if ($plan.PSObject.Properties['added_bytes']) { [int64]$plan.added_bytes } else { [int64](@($plan.items | Measure-Object -Property size_bytes -Sum).Sum) }
$projectedBytes = $currentR2Bytes + $plannedBytes

if ($projectedBytes -gt [int64]$plan.maximum_projected_r2_bytes) {
  throw "Archive plan would project R2 storage to $projectedBytes bytes, above the plan limit of $($plan.maximum_projected_r2_bytes) bytes."
}

foreach ($item in @($plan.items)) {
  $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
  if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for $($item.id); found $($candidate.Count)." }
  $file = Get-Item -LiteralPath $candidate[0].local_path
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne [int64]$item.size_bytes) { throw "Size mismatch for $($item.id)." }
  if ($hash -ne [string]$item.checksum_sha256) { throw "SHA-256 mismatch for $($item.id)." }
  if ($file.Length -gt [int64]$plan.maximum_object_bytes) { throw "Object $($item.id) exceeds the plan's per-object limit." }

  $publicUrl = "https://files.abqinfo.com/$($item.r2_key)"
  $set = @{
    status = 'placement assigned'
    r2_key = [string]$item.r2_key
    r2_url = $publicUrl
    source_url = [string]$item.source_url
    direct_file_url = [string]$item.direct_file_url
    agency = [string]$item.agency
    title = [string]$item.title
    date = [string]$item.date
    file_type = [string]$item.file_type
    size_bytes = [int64]$item.size_bytes
    checksum_sha256 = [string]$item.checksum_sha256
    parent_url = [string]$item.parent_url
    proposed_canonical_page = [string]$item.proposed_canonical_page
    description = [string]$item.description
    provenance_status = [string]$item.provenance_status
    validation_status = 'local size and SHA-256 passed; R2 upload pending'
    processing_notes = @($item.processing_notes)
  }
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $item.id -Set $set -InventoryPath $InventoryPath | Out-Null

  if ($PSCmdlet.ShouldProcess($publicUrl, "Upload and verify $($file.Name)")) {
    $currentInventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
    $currentCandidate = @($currentInventory.candidates | Where-Object id -eq $item.id)[0]
    if ($currentCandidate.r2_etag) {
      & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $file.FullName -PublicUrl $publicUrl | Out-Null
      & "$PSScriptRoot/Update-Candidate.ps1" -Id $item.id -Set @{
        validation_status = 'local size and SHA-256 passed; existing R2 object verified by public byte-identical download'
        processing_notes = @($item.processing_notes) + @('Original authoritative file uploaded without modification; public R2 download matched exact size and SHA-256.')
      } -InventoryPath $InventoryPath | Out-Null
    } else {
      $uploadOutput = @(& "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $file.FullName -ObjectKey $item.r2_key -MaxObjectBytes ([int64]$plan.maximum_object_bytes) -MaxProjectedStorageBytes ([int64]$plan.maximum_projected_r2_bytes))
      $upload = @($uploadOutput | Where-Object { $_.PSObject.Properties.Name -contains 'R2Metadata' } | Select-Object -Last 1)
      if ($upload.Count -ne 1) { throw "Uploader did not return R2 metadata for $($item.id)." }
      $metadata = $upload[0].R2Metadata | ConvertFrom-Json
      & "$PSScriptRoot/Update-Candidate.ps1" -Id $item.id -Set @{
        r2_etag = ([string]$metadata.ETag).Trim('"')
        r2_last_modified = [string]$metadata.LastModified
        validation_status = 'local size and SHA-256 passed; R2 upload verified by HEAD'
        processing_notes = @($item.processing_notes) + @('Original authoritative file uploaded without modification; R2 object verified by HEAD.')
      } -InventoryPath $InventoryPath | Out-Null
    }
  }

  $inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
  [pscustomobject]@{
    id = $item.id
    title = $item.title
    bytes = $item.size_bytes
    r2_url = $publicUrl
    status = (@($inventory.candidates | Where-Object id -eq $item.id))[0].status
  }
}

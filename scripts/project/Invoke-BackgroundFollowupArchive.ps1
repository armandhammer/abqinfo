[CmdletBinding()]
param([string]$Folder = 'project-state/discovery/background-followup-2026-09-26')

. "$PSScriptRoot/Assert-TaskGovernance.ps1"
Assert-TaskGovernance -ToolPath $PSCommandPath -Parameters $PSBoundParameters




Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$folder = $Folder
$writerLock = [IO.File]::Open('tmp/background-followup-upload.lock', [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
try {
$plan = Get-Content -Raw -Encoding UTF8 "$folder/archive-plan.json" | ConvertFrom-Json
$authority = Get-Content -Raw -Encoding UTF8 $plan.authorization_artifact | ConvertFrom-Json
$policy = Get-Content -Raw -Encoding UTF8 project-state/r2-storage-policy.json | ConvertFrom-Json
if ($plan.maximum_object_bytes -ne 150000000 -or $plan.maximum_storage_bytes -ne $policy.maximum_projected_r2_bytes -or $authority.maximum_object_bytes -ne $plan.maximum_object_bytes -or $authority.maximum_storage_bytes -ne $plan.maximum_storage_bytes) { throw 'Archive plan/authority limits do not match the authorized policy' }
$baseline = Get-Content -Raw -Encoding UTF8 $plan.baseline | ConvertFrom-Json
$receiptPath = "$folder/archive-receipts.json"
$receipts = if (Test-Path -LiteralPath $receiptPath) { @(Get-Content -Raw -Encoding UTF8 $receiptPath | ConvertFrom-Json) } else { @() }
function Save-Receipts {
  ConvertTo-Json -InputObject @($script:receipts) -Depth 25 | Set-Content -LiteralPath "$receiptPath.tmp" -Encoding utf8
  Move-Item -LiteralPath "$receiptPath.tmp" -Destination $receiptPath -Force
}
function Guard-Live {
  & "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath "$folder/r2-current-preflight.json" | Out-Null
  $live = Get-Content -Raw -Encoding UTF8 "$folder/r2-current-preflight.json" | ConvertFrom-Json
  $objects = @{}; foreach ($o in $live.objects) { if ($objects.ContainsKey($o.key)) { throw 'Case-insensitive key collision' }; $objects[$o.key] = $o }
  foreach ($o in $baseline.objects) {
    if (-not $objects.ContainsKey($o.key) -or $objects[$o.key].key -cne $o.key -or $objects[$o.key].size_bytes -ne $o.size_bytes -or $objects[$o.key].etag -cne $o.etag) { throw 'Baseline R2 drift' }
  }
  $baselineKeys = @($baseline.objects.key)
  foreach ($o in $live.objects) {
    if ($o.key -cnotin $baselineKeys) {
      $intent = @($script:receipts | Where-Object key -CEQ $o.key)
      if ($intent.Count -ne 1 -or $intent[0].size_bytes -ne $o.size_bytes) { throw 'Unexplained R2 object' }
      if ($intent[0].PSObject.Properties['etag'] -and $intent[0].etag -cne $o.etag) { throw 'Uploaded-object ETag drift' }
    }
  }
  if ($live.total_bytes -gt $plan.maximum_storage_bytes) { throw 'Storage ceiling exceeded' }
  return $live
}
foreach ($item in $plan.items) {
  $live = Guard-Live
  $file = Get-Item -LiteralPath $item.source_path
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($file.Length -ne $item.size_bytes -or $hash -cne $item.sha256 -or $file.Length -gt $plan.maximum_object_bytes) { throw 'Source identity/size changed' }
  $row = (& "$PSScriptRoot/Get-Candidate.ps1" -Id $item.id)
  # The reviewed decision and source hash are durable prerequisites; no status is advanced before full public GET.
  $inventory = Get-Content -Raw -Encoding UTF8 project-state/master-inventory.json | ConvertFrom-Json
  $candidate = @($inventory.candidates | Where-Object id -EQ $item.id)[0]
  if ($candidate.scope_assessment.final_scope_decision -ne 'passes_both_gates' -or -not $candidate.quality_assessment.visual_inspection_completed) { throw 'Eligibility gate incomplete' }
  if ($candidate.id -notin $authority.allowed_ids -or $candidate.size_bytes -ne $item.size_bytes -or $candidate.checksum_sha256 -cne $hash) { throw 'Inventory identity/population differs from the authorized source intent' }
  $entry = @($receipts | Where-Object id -EQ $item.id)
  $present = @($live.objects | Where-Object key -CEQ $item.r2_key)
  if ($entry.Count -eq 0) {
    if ($present.Count) { throw 'Key present without task intent' }
    if (@($live.objects | Where-Object size_bytes -EQ $item.size_bytes).Count) { throw 'Same-size object requires negative full GET comparison' }
    if ($live.total_bytes + $item.size_bytes -gt $plan.maximum_storage_bytes) { throw 'Projected storage exceeds ceiling' }
    $entry = [pscustomobject]@{id=$item.id;key=$item.r2_key;size_bytes=[int64]$item.size_bytes;checksum_sha256=$hash;state='intent_saved_before_PUT';key_was_absent=$true;intent_at=(Get-Date).ToUniversalTime().ToString('o')}
    $receipts += @($entry); Save-Receipts
    $pdfPath = [IO.Path]::ChangeExtension($file.FullName, '.pdf')
    Copy-Item -LiteralPath $file.FullName -Destination $pdfPath -Force
    $upload = @(& "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $pdfPath -ObjectKey $item.r2_key -MaxObjectBytes $plan.maximum_object_bytes -MaxProjectedStorageBytes $plan.maximum_storage_bytes)
    $result = @($upload | Where-Object { $_.PSObject.Properties['R2Metadata'] })[-1]
    $meta = ($result.R2Metadata -join "`n") | ConvertFrom-Json
    $entry | Add-Member -NotePropertyName etag -NotePropertyValue ([string]$meta.ETag).Trim('"')
    $entry.state = 'uploaded_pending_full_public_verification'; Save-Receipts
  } else {
    $entry = $entry[0]
    if ($present.Count -ne 1) { throw 'Saved intent requires recovery investigation; do not repeat PUT' }
    if ($entry.state -eq 'inventory_reconciled' -and $candidate.status -eq 'placement assigned' -and $candidate.r2_key -ceq $item.r2_key -and $candidate.r2_etag -ceq $entry.etag -and $entry.public_verification.byte_identical -and $entry.public_verification.checksum_sha256 -ceq $hash -and $entry.public_verification.size_bytes -eq $item.size_bytes) {
      Write-Output "Previously verified archive reconciled without repeated PUT/GET: $($item.id)"
      continue
    }
  }
  $verification = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $file.FullName -PublicUrl "https://files.abqinfo.com/$($item.r2_key)"
  $entry | Add-Member -NotePropertyName public_verification -NotePropertyValue $verification -Force
  $entry.state = 'exact_public_GET_verified'; Save-Receipts
  & "$PSScriptRoot/Update-Candidate.ps1" -Id $item.id -Set @{
    status='placement assigned';r2_key=$item.r2_key;r2_url=$verification.public_url;r2_etag=$entry.etag
    validation_status='Exact original official-source size/SHA-256 and full public GET verified; background archive complete'
    processing_notes=@($candidate.processing_notes)+@('2026-09-26 background follow-up: unchanged original archived under current authorization and full public GET matched exact size/SHA-256. Receipt: '+$receiptPath)
  } | Out-Null
  $entry.state='inventory_reconciled'; Save-Receipts
  Write-Output "Archived and full-GET verified $($item.id): $($item.size_bytes) bytes"
}
$final=Guard-Live
Copy-Item -LiteralPath "$folder/r2-current-preflight.json" -Destination "$folder/r2-final.json" -Force
Copy-Item -LiteralPath "$folder/r2-final.json" -Destination project-state/r2-inventory.json -Force
} finally { $writerLock.Dispose() }

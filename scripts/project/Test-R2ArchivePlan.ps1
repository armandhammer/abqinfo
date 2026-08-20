[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$PlanPath,
  [Parameter(Mandatory)][string]$OutputPath,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$plan = Get-Content -Raw -LiteralPath $PlanPath | ConvertFrom-Json
$results = @()

foreach ($item in @($plan.items)) {
  $publicUrl = "https://files.abqinfo.com/$($item.r2_key)"
  try {
    $inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
    $candidate = @($inventory.candidates | Where-Object id -eq $item.id)
    if ($candidate.Count -ne 1 -or -not $candidate[0].local_path) {
      throw "Could not resolve local source path for '$($item.id)'."
    }
    $test = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $candidate[0].local_path -PublicUrl $publicUrl
    $result = [ordered]@{
      id = [string]$item.id
      title = [string]$item.title
      public_url = $publicUrl
      size_bytes = [int64]$test.size_bytes
      checksum_sha256 = [string]$test.checksum_sha256
      byte_identical = [bool]$test.byte_identical
      verified_at = [string]$test.verified_at
      error = $null
    }
    & "$PSScriptRoot/Update-Candidate.ps1" -Id $item.id -Set @{
      validation_status = 'passed: public R2 download is byte-identical to the reviewed local source; authoritative provenance is evaluated separately'
    } -InventoryPath $InventoryPath | Out-Null
  } catch {
    $result = [ordered]@{
      id = [string]$item.id
      title = [string]$item.title
      public_url = $publicUrl
      size_bytes = $null
      checksum_sha256 = $null
      byte_identical = $false
      verified_at = (Get-Date).ToUniversalTime().ToString('o')
      error = $_.Exception.Message
    }
  }
  $results += [pscustomobject]$result
  [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    plan_path = $PlanPath
    total_items = @($plan.items).Count
    completed_items = $results.Count
    passed_items = @($results | Where-Object byte_identical).Count
    failed_items = @($results | Where-Object { -not $_.byte_identical }).Count
    results = $results
  } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
  [pscustomobject]$result
}

if (@($results | Where-Object { -not $_.byte_identical }).Count) {
  throw 'One or more public R2 objects failed byte-identical validation.'
}

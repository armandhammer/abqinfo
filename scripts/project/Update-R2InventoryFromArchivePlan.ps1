[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$PlanPath,
  [Parameter(Mandatory)][string]$PublicValidationPath,
  [string]$R2InventoryPath = 'project-state/r2-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$validation = Get-Content -Raw -Encoding UTF8 -LiteralPath $PublicValidationPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $R2InventoryPath | ConvertFrom-Json

foreach ($item in @($plan.items)) {
  $result = @($validation.results | Where-Object id -eq $item.id)
  if ($result.Count -ne 1 -or -not $result[0].byte_identical) {
    throw "Public byte-identical validation is missing for '$($item.id)'."
  }
  $url = "https://files.abqinfo.com/$($item.r2_key)"
  $response = Invoke-WebRequest -Method Head -Uri $url
  $remoteLength = [int64](@($response.Headers.'Content-Length')[0])
  if ($remoteLength -ne [int64]$item.size_bytes) {
    throw "Public Content-Length mismatch for '$($item.id)'."
  }
  $etag = ([string](@($response.Headers.ETag)[0])).Trim('"')
  $lastModified = [string](@($response.Headers.'Last-Modified')[0])
  $existing = @($inventory.objects | Where-Object key -eq $item.r2_key)
  $record = [pscustomobject][ordered]@{
    key = [string]$item.r2_key
    size_bytes = [int64]$item.size_bytes
    last_modified = $lastModified
    etag = $etag
    storage_class = 'STANDARD'
    public_url = $url
  }
  if ($existing.Count -eq 0) {
    $inventory.objects += $record
  } elseif ($existing.Count -eq 1) {
    $index = [array]::IndexOf([array]$inventory.objects, $existing[0])
    $inventory.objects[$index] = $record
  } else {
    throw "R2 inventory contains duplicate key '$($item.r2_key)'."
  }
}

$inventory.objects = @($inventory.objects | Sort-Object key)
$inventory.object_count = $inventory.objects.Count
$inventory.total_bytes = [int64](($inventory.objects | Measure-Object -Property size_bytes -Sum).Sum)
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')

$json = $inventory | ConvertTo-Json -Depth 8
$fullPath = [IO.Path]::GetFullPath($R2InventoryPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, $json, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force

[pscustomobject]@{
  object_count = $inventory.object_count
  total_bytes = $inventory.total_bytes
  added_or_reconciled = @($plan.items).Count
  inventory_path = $R2InventoryPath
}

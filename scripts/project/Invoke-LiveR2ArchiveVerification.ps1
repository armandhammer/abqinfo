[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$LinkInventoryPath,
  [Parameter(Mandatory)][string]$MasterInventoryPath,
  [Parameter(Mandatory)][string]$OutputPath,
  [int]$BatchSize = 25,
  [int]$ThrottleLimit = 8,
  [int]$TimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$links = Get-Content -Raw -Encoding UTF8 -LiteralPath $LinkInventoryPath | ConvertFrom-Json
$master = Get-Content -Raw -Encoding UTF8 -LiteralPath $MasterInventoryPath | ConvertFrom-Json
$expected = @{}
foreach ($candidate in @($master.candidates)) {
  if ($candidate.r2_key) {
    $key = [string]$candidate.r2_key
    if (-not $expected.ContainsKey($key)) {
      $expected[$key] = [ordered]@{
        ids = [Collections.Generic.List[string]]::new()
        size_bytes = if ($candidate.size_bytes) { [int64]$candidate.size_bytes } else { $null }
        checksum_sha256 = if ($candidate.checksum_sha256) { [string]$candidate.checksum_sha256 } else { $null }
      }
    }
    if ([string]$candidate.id -notin $expected[$key].ids) { $expected[$key].ids.Add([string]$candidate.id) }
    if (-not $expected[$key].size_bytes -and $candidate.size_bytes) { $expected[$key].size_bytes = [int64]$candidate.size_bytes }
    if (-not $expected[$key].checksum_sha256 -and $candidate.checksum_sha256) { $expected[$key].checksum_sha256 = [string]$candidate.checksum_sha256 }
  }
}
$items = @($links.links | Where-Object is_r2_archive | Group-Object url | ForEach-Object {
  $link = $_.Group[0]
  $uri = [uri]$link.url
  $key = $uri.AbsolutePath.TrimStart('/')
  $record = if ($expected.ContainsKey($key)) { $expected[$key] } else { $null }
  [pscustomobject]@{
    url = [string]$link.url
    key = $key
    expected_ids = if ($record) { @($record.ids) } else { @() }
    expected_size_bytes = if ($record) { $record.size_bytes } else { $null }
    expected_checksum_sha256 = if ($record) { $record.checksum_sha256 } else { $null }
  }
})

$results = [Collections.Generic.List[object]]::new()
if (Test-Path -LiteralPath $OutputPath) {
  $prior = Get-Content -Raw -Encoding UTF8 -LiteralPath $OutputPath | ConvertFrom-Json
  foreach ($result in @($prior.results)) {
    $successful = [int]$result.http_status -ge 200 -and [int]$result.http_status -lt 400
    $hashOkay = -not [bool]$result.hash_checked -or [bool]$result.hash_match
    if ($successful -and $hashOkay) { $results.Add($result) }
  }
}
$done = @($results | ForEach-Object { [string]$_.url })
$pending = @($items | Where-Object { $_.url -notin $done })

function Write-Checkpoint {
  $summary = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    link_inventory = $LinkInventoryPath
    master_inventory = $MasterInventoryPath
    total_items = $items.Count
    completed_items = $results.Count
    resolved_items = @($results | Where-Object { $_.http_status -ge 200 -and $_.http_status -lt 400 }).Count
    failed_items = @($results | Where-Object { $_.http_status -lt 200 -or $_.http_status -ge 400 }).Count
    hash_checked_items = @($results | Where-Object hash_checked).Count
    hash_match_items = @($results | Where-Object hash_match).Count
    hash_mismatch_items = @($results | Where-Object { $_.hash_checked -and -not $_.hash_match }).Count
    results = @($results)
  }
  $fullPath = [IO.Path]::GetFullPath($OutputPath)
  $temporaryPath = "$fullPath.tmp-$PID"
  [IO.File]::WriteAllText($temporaryPath, ($summary | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
}

while ($pending.Count -gt 0) {
  $batch = @($pending | Select-Object -First $BatchSize)
  $batchResults = @($batch | ForEach-Object -Parallel {
    $item = $_
    $client = [Net.Http.HttpClient]::new()
    $client.Timeout = [TimeSpan]::FromSeconds($using:TimeoutSeconds)
    try {
      $response = $client.GetAsync($item.url, [Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
      $status = [int]$response.StatusCode
      $lengthHeader = $response.Content.Headers.ContentLength
      $actualSize = if ($lengthHeader) { [int64]$lengthHeader } else { $null }
      $hashChecked = [bool]$item.expected_checksum_sha256
      $hash = $null
      $bytesRead = 0L
      if ($hashChecked -and $status -ge 200 -and $status -lt 400) {
        $stream = $response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
        $sha = [Security.Cryptography.SHA256]::Create()
        $buffer = [byte[]]::new(1048576)
        try {
          while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
            $sha.TransformBlock($buffer, 0, $read, $buffer, 0) | Out-Null
            $bytesRead += $read
          }
          $sha.TransformFinalBlock([byte[]]::new(0), 0, 0) | Out-Null
          $hash = (-join ($sha.Hash | ForEach-Object { $_.ToString('x2') }))
          if ($null -eq $actualSize) { $actualSize = $bytesRead }
        } finally { $sha.Dispose(); $stream.Dispose() }
      }
      [pscustomobject][ordered]@{
        url = [string]$item.url
        key = [string]$item.key
        expected_ids = @($item.expected_ids)
        expected_size_bytes = $item.expected_size_bytes
        expected_checksum_sha256 = $item.expected_checksum_sha256
        http_status = $status
        remote_size_bytes = $actualSize
        size_match = if ($null -ne $item.expected_size_bytes -and $null -ne $actualSize) { [int64]$item.expected_size_bytes -eq [int64]$actualSize } else { $null }
        hash_checked = $hashChecked
        remote_checksum_sha256 = $hash
        hash_match = if ($hashChecked -and $hash) { $hash -eq [string]$item.expected_checksum_sha256 } else { $null }
        etag = [string]$response.Headers.ETag
        last_modified = [string]$response.Content.Headers.LastModified
        error = $null
      }
    } catch {
      [pscustomobject][ordered]@{
        url = [string]$item.url; key = [string]$item.key; expected_ids = @($item.expected_ids)
        expected_size_bytes = $item.expected_size_bytes; expected_checksum_sha256 = $item.expected_checksum_sha256
        http_status = 0; remote_size_bytes = $null; size_match = $false; hash_checked = [bool]$item.expected_checksum_sha256
        remote_checksum_sha256 = $null; hash_match = $false; etag = $null; last_modified = $null; error = $_.Exception.Message
      }
    } finally { $client.Dispose() }
  } -ThrottleLimit $ThrottleLimit)
  foreach ($result in $batchResults) { $results.Add($result) }
  $pending = @($pending | Select-Object -Skip $batch.Count)
  Write-Checkpoint
  [pscustomobject]@{ completed = $results.Count; total = $items.Count; resolved = @($results | Where-Object { $_.http_status -ge 200 -and $_.http_status -lt 400 }).Count; hash_matches = @($results | Where-Object hash_match).Count } | ConvertTo-Json -Compress
}
Write-Checkpoint

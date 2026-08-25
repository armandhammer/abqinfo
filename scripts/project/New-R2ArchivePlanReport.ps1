[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$PlanPath,
  [Parameter(Mandatory)][string]$OutputPath,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$plan = Get-Content -Raw -Encoding UTF8 -LiteralPath $PlanPath | ConvertFrom-Json
$items = @($plan.items)
$batchBytes = [int64](($items | Measure-Object -Property size_bytes -Sum).Sum)
$added = if ($plan.PSObject.Properties['added_bytes']) { [int64]$plan.added_bytes } else { $batchBytes }
$projected = if ($plan.PSObject.Properties['projected_r2_bytes']) { [int64]$plan.projected_r2_bytes } else { [int64]$plan.current_r2_bytes + $added }
$large = @($items | Where-Object { $_.size_bytes -gt 25MB })
$overLimit = @($items | Where-Object { $_.size_bytes -gt [int64]$plan.maximum_object_bytes })
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$terminal = @('validated','excluded','duplicate','superseded','blocked','requires human review')
$remaining = @($inventory.candidates | Where-Object { $_.status -notin $terminal -and $_.id -notin $items.id })
$remainingKnown = @($remaining | Where-Object { $null -ne $_.size_bytes -and [int64]$_.size_bytes -gt 0 } |
  Group-Object { if ($_.checksum_sha256) { $_.checksum_sha256 } elseif ($_.direct_file_url) { $_.direct_file_url } else { $_.id } } |
  ForEach-Object { $_.Group | Select-Object -First 1 })
$remainingKnownBytes = [int64](($remainingKnown | Measure-Object -Property size_bytes -Sum).Sum)
$remainingUnknown = @($remaining | Where-Object { $null -eq $_.size_bytes -or [int64]$_.size_bytes -le 0 }).Count
$completeLowerBound = $projected + $remainingKnownBytes

$lines = @(
  '# R2 archive plan report'
  ''
  "Generated from ``$PlanPath``."
  ''
  "- Current bucket storage: $($plan.current_r2_bytes) bytes"
  "- Files proposed: $($items.Count)"
  "- Total size of files in batch: $batchBytes bytes ($([math]::Round($batchBytes / 1MB, 2)) MiB)"
  "- Storage added: $added bytes ($([math]::Round($added / 1MB, 2)) MiB)"
  "- Projected bucket storage: $projected bytes ($([math]::Round($projected / 1GB, 2)) GiB)"
  "- Files larger than 25 MiB: $($large.Count)"
  "- Files larger than $($plan.maximum_object_bytes) bytes: $($overLimit.Count)"
  "- Remaining nonterminal candidates: $($remaining.Count)"
  "- Exact size of remaining candidates with known size, deduplicated: $remainingKnownBytes bytes ($([math]::Round($remainingKnownBytes / 1MB, 2)) MiB)"
  "- Remaining candidates without reliable size metadata: $remainingUnknown"
  "- Complete-project storage lower bound from currently known sizes: $completeLowerBound bytes ($([math]::Round($completeLowerBound / 1GB, 2)) GiB)"
  "- Complete-project estimate limitation: unknown-size and not-yet-discovered files prevent a defensible final total; the lower bound is not a storage commitment."
  ''
  '| Stable ID | Title | Type | Exact bytes | Human size | Over 25 MiB | R2 key |'
  '|---|---|---:|---:|---:|---:|---|'
)
foreach ($item in $items) {
  $lines += "| $($item.id) | $($item.title -replace '\|','/') | $($item.file_type) | $($item.size_bytes) | $([math]::Round($item.size_bytes / 1MB, 2)) MiB | $(if ($item.size_bytes -gt 25MB) { 'Yes' } else { 'No' }) | ``$($item.r2_key)`` |"
}
if ($large.Count) {
  $lines += @('', '## Files larger than 25 MiB', '')
  foreach ($item in $large) {
    $lines += "- **$($item.title)** — $($item.size_bytes) bytes ($([math]::Round($item.size_bytes / 1MB, 2)) MiB), $($item.file_type). $($item.large_file_assessment)"
  }
}
$lines | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{ files=$items.Count; added_bytes=$added; projected_bytes=$projected; over_25_mib=$large.Count; over_limit=$overLimit.Count; report=$OutputPath }

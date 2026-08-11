[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$R2InventoryPath = 'project-state/r2-inventory.json',
  [string]$SourcePrioritiesPath = 'project-state/source-priorities.json',
  [string]$OutputPath = 'project-state/source-catalog.md'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -Raw -LiteralPath $InventoryPath | ConvertFrom-Json
$r2 = Get-Content -Raw -LiteralPath $R2InventoryPath | ConvertFrom-Json
$prioritySources = if (Test-Path -LiteralPath $SourcePrioritiesPath) { @((Get-Content -Raw -LiteralPath $SourcePrioritiesPath | ConvertFrom-Json).sources) } else { @() }
$lines = [Collections.Generic.List[string]]::new()
$lines.Add('# ABQ Info authoritative source catalog')
$lines.Add('')
$lines.Add("Generated: $((Get-Date).ToUniversalTime().ToString('o'))")
$lines.Add('')
$lines.Add("This catalog is derived from `master-inventory.json`, the authoritative project queue. It records $(@($inventory.candidates).Count) candidates and $(@($r2.objects).Count) R2 objects totaling $($r2.total_bytes) bytes.")
$lines.Add('')
$lines.Add('## Queue status')
$lines.Add('')
$lines.Add('| Status | Count |')
$lines.Add('| --- | ---: |')
foreach ($property in $inventory.counts.PSObject.Properties) { $lines.Add("| $($property.Name) | $($property.Value) |") }
$lines.Add('')
$lines.Add('## Preserved documents')
$lines.Add('')
$lines.Add('| Title | Agency | Date | Exact bytes | Canonical page | Source | Archived copy |')
$lines.Add('| --- | --- | --- | ---: | --- | --- | --- |')
foreach ($candidate in $inventory.candidates | Where-Object { $_.status -eq 'validated' -and $_.r2_url -and $_.file_type -eq 'PDF' } | Sort-Object agency,title) {
  $title = ([string]$candidate.title).Replace('|','\|')
  $source = if ($candidate.source_url) { "[source]($($candidate.source_url))" } elseif ($candidate.direct_file_url) { "[source]($($candidate.direct_file_url))" } else { '' }
  $lines.Add("| $title | $($candidate.agency) | $($candidate.date) | $($candidate.size_bytes) | $($candidate.proposed_canonical_page) | $source | [R2]($($candidate.r2_url)) |")
}
$lines.Add('')
$lines.Add('## Maintained live sources')
$lines.Add('')
$lines.Add('| Title | Agency | Canonical page | URL |')
$lines.Add('| --- | --- | --- | --- |')
foreach ($candidate in $inventory.candidates | Where-Object { $_.status -eq 'validated' -and -not $_.r2_url -and $_.source_url } | Sort-Object agency,title) {
  $title = ([string]$candidate.title).Replace('|','\|')
  $lines.Add("| $title | $($candidate.agency) | $($candidate.proposed_canonical_page) | [source]($($candidate.source_url)) |")
}
$lines.Add('')
$lines.Add('## Deferred and last-resort sources')
$lines.Add('')
$lines.Add('| Source | Agency | Priority | Automatic crawl | Use rule |')
$lines.Add('| --- | --- | --- | --- | --- |')
foreach ($source in $prioritySources | Sort-Object priority_tier,name) {
  $name = ([string]$source.name).Replace('|','\|')
  $rule = ([string]$source.use_after).Replace('|','\|')
  $lines.Add("| [$name]($($source.url)) | $($source.agency) | $($source.priority_tier) | $($source.automatic_crawl) | $rule |")
}
$lines.Add('')
$lines.Add('## Exceptions')
$lines.Add('')
$lines.Add('| ID | Status | Title | Reason |')
$lines.Add('| --- | --- | --- | --- |')
foreach ($candidate in $inventory.candidates | Where-Object { $_.status -in @('excluded','duplicate','superseded','blocked','requires human review') } | Sort-Object status,id) {
  $reason = if ($candidate.exclusion_reason) { $candidate.exclusion_reason } else { (@($candidate.processing_notes) -join '; ') }
  $lines.Add("| $($candidate.id) | $($candidate.status) | $(([string]$candidate.title).Replace('|','\|')) | $(([string]$reason).Replace('|','\|')) |")
}
$directory = Split-Path -Parent $OutputPath
if ($directory) { New-Item -ItemType Directory -Force $directory | Out-Null }
$lines | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]@{ OutputPath = $OutputPath; Candidates = @($inventory.candidates).Count; R2Objects = @($r2.objects).Count; R2Bytes = $r2.total_bytes } | ConvertTo-Json -Compress

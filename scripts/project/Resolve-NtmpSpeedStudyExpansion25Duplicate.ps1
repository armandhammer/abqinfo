[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$pairs = [ordered]@{
  'src-4055f2c2c2855c3f' = 'src-9b50c853b151ada2'
  'src-68d0f4c2eab1abcc' = 'src-5492d231debc826a'
  'src-3ee27f72a343adbd' = 'src-82ed5901df5a3610'
  'src-60cacc1053d6ff09' = 'src-c2112472deff2555'
  'src-481c7da828be0275' = 'src-50b22c2cff55127c'
  'src-09a7c06f0ee97da0' = 'src-6c6f2aed1a9d4d1f'
  'src-84df2cc205ac4eed' = 'src-ce04fb6842a09dea'
  'src-f70f9e2027603c7b' = 'src-70d6d253b034c1aa'
  'src-6ec094424a36ea7e' = 'src-443d248392597a00'
  'src-fd7fb9dd8737ab5d' = 'src-f18cd98a58a4fef5'
  'src-46babb6f9318d547' = 'src-d19827d1fca91d3f'
  'src-355de0c6e2a75205' = 'src-7c6240f55fadae7a'
  'src-4631527cd57ef0f8' = 'src-cef309f0fc19d674'
  'src-40d70969977fa87d' = 'src-310e89e31b12747a'
  'src-e76196d4a7b799ac' = 'src-b978a32849d783ce'
  'src-4947ff6d7d8d78f7' = 'src-c68882c45fa8d45c'
  'src-9c795e2736c419a6' = 'src-ea9e689316a9e3ee'
  'src-a06ed44222a26f73' = 'src-55919b89045da7bf'
  'src-5a721d4def74af93' = 'src-23d0c6c8780944f9'
  'src-c2352b77a1c1bb08' = 'src-eefaabfa61697495'
}

$results = foreach ($entry in $pairs.GetEnumerator()) {
  $duplicateId = [string]$entry.Key
  $canonicalId = [string]$entry.Value
  $duplicate = @($inventory.candidates | Where-Object id -eq $duplicateId)
  $canonical = @($inventory.candidates | Where-Object id -eq $canonicalId)
  if ($duplicate.Count -ne 1 -or $canonical.Count -ne 1) { throw "Expected one duplicate and one canonical candidate for $duplicateId." }
  $duplicate = $duplicate[0]
  $canonical = $canonical[0]
  if (-not $duplicate.checksum_sha256 -or $duplicate.checksum_sha256 -ne $canonical.checksum_sha256) {
    throw "Candidates $duplicateId and $canonicalId are not byte-identical."
  }

  $duplicate.status = 'duplicate'
  $duplicate.r2_url = $null
  $duplicate.r2_key = $null
  $duplicate.r2_etag = $null
  $duplicate.r2_last_modified = $null
  $duplicate.proposed_canonical_page = $null
  $duplicate.description = $null
  $duplicate.description_word_count = 0
  $duplicate.implementation_location = $null
  $duplicate.implementation_locations = @()
  $duplicate.validation_status = "duplicate: exact SHA-256 match to canonical candidate $canonicalId"
  $duplicate.exclusion_reason = "Byte-identical duplicate of $canonicalId; alternate City source retained in provenance, but only one archive object and page entry are required."
  $duplicate.processing_notes = @(@($duplicate.processing_notes) + "Exact checksum duplicate of $canonicalId; canonical record provides the single archive object and page entry." | Sort-Object -Unique)
  $duplicate.updated_at = (Get-Date).ToUniversalTime().ToString('o')
  [pscustomobject]@{ Duplicate = $duplicateId; Canonical = $canonicalId; Checksum = $duplicate.checksum_sha256 }
}

foreach ($status in $inventory.allowed_statuses) {
  $inventory.counts.$status = @($inventory.candidates | Where-Object status -eq $status).Count
}
$inventory.next_pending_id = @($inventory.candidates | Where-Object status -eq 'pending review' | Sort-Object id | Select-Object -First 1).id
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')
[IO.File]::WriteAllText([IO.Path]::GetFullPath($InventoryPath), ($inventory | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))

$results | ConvertTo-Json -Compress

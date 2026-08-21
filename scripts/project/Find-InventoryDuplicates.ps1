[CmdletBinding()]
param([string]$InventoryPath = 'project-state/master-inventory.json')

$inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json
$duplicates = @()
$duplicates += $inventory.candidates | Where-Object checksum_sha256 | Group-Object checksum_sha256 | Where-Object Count -gt 1 | ForEach-Object {
  [pscustomobject]@{Basis='checksum_sha256';Value=$_.Name;Ids=@($_.Group.id)}
}
$duplicates += $inventory.candidates | Where-Object direct_file_url | Group-Object direct_file_url | Where-Object Count -gt 1 | ForEach-Object {
  [pscustomobject]@{Basis='direct_file_url';Value=$_.Name;Ids=@($_.Group.id)}
}
$duplicates | ConvertTo-Json -Depth 5


$ErrorActionPreference = 'Stop'
$folder = 'project-state/discovery/owner-decisions-2026-09-26'
$rows = Get-Content -Raw "$folder/baseline-records.json" | ConvertFrom-Json
$results = @()
foreach ($row in $rows | Where-Object { $_.r2_key }) {
 $verification = & scripts/project/Test-R2PublicObject.ps1 -SourcePath $row.local_path -PublicUrl $row.r2_url
 $results += [pscustomobject]@{ id=$row.id; key=$row.r2_key; verification=$verification }
 ConvertTo-Json -InputObject @($results) -Depth 15 | Set-Content "$folder/existing-art-public-verification.json" -Encoding utf8
 Write-Output "Existing ART exact GET verified: $($row.id)"
}

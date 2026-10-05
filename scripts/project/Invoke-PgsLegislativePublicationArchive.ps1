[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskPath = 'project-state/governance/pgs-legislative-publication-2026-10-05/'
$pop = Get-Content -Raw -Encoding UTF8 ($taskPath+'population-v2.json') | ConvertFrom-Json
$before = Get-Content -Raw -Encoding UTF8 ($taskPath+'before-r2.json') | ConvertFrom-Json
$saved = Get-Content -Raw -Encoding UTF8 'project-state/r2-inventory.json' | ConvertFrom-Json
$policy = Get-Content -Raw -Encoding UTF8 'project-state/r2-storage-policy.json' | ConvertFrom-Json
if ($before.total_bytes -ne $saved.total_bytes -or $before.object_count -ne $saved.object_count) { throw 'Live R2 baseline drift' }
if ([int64]$before.total_bytes+133251 -gt [int64]$policy.maximum_projected_r2_bytes) { throw 'Storage ceiling' }
$sourceFiles = @{'src-f7c7bd5b273def22'='o-39fs3.pdf';'src-68582bc4fe41fb4f'='o-132fin.pdf';'src-fcbe6a7ebcf916a1'='o-9fin.pdf'}
$sizes = @{'src-f7c7bd5b273def22'=83406;'src-68582bc4fe41fb4f'=25029;'src-fcbe6a7ebcf916a1'=24816}
$items = @()
foreach ($object in $pop.archive_objects) {
  $sourcePath = 'research/staging/pgs-legislative-publication-2026-10-05/'+$sourceFiles[$object.candidate_id]
  $hash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
  $size = (Get-Item -LiteralPath $sourcePath).Length
  if ($hash -ne $object.sha256 -or $size -ne $sizes[$object.candidate_id]) { throw 'Source bytes mismatch' }
  if (@($before.objects | Where-Object { $_.key -ieq $object.r2_key }).Count) { throw 'Frozen key already exists; no overwrite or reupload' }
  $items += [pscustomobject]@{id=$object.candidate_id;source_url=('https://www.cabq.gov/council/documents/pgs/'+$sourceFiles[$object.candidate_id]);source_path=$sourcePath;r2_key=$object.r2_key;expected_size_bytes=$size;expected_checksum_sha256=$hash;public_url=('https://files.abqinfo.com/'+$object.r2_key)}
}
$items | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 ($taskPath+'source-verification.json')
$result = [ordered]@{state='in_progress';started_at=(Get-Date).ToUniversalTime().ToString('o');before_objects=$before.object_count;before_bytes=$before.total_bytes;added_objects=0;added_bytes=0;results=@()}
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 ($taskPath+'archive-result.json')
foreach ($item in $items) {
  $intent = [ordered]@{state='intent_before_put';recorded_at=(Get-Date).ToUniversalTime().ToString('o');item=$item;prior_results=$result.results;authority=$taskPath+'authority.json'}
  $intent | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 ($taskPath+'archive-intent.json')
  & python scripts/project/Resolve-TaskGovernance.py active --phase mutation --operation archive --candidate $item.id --r2-key $item.r2_key --source-sha256 $item.expected_checksum_sha256 | Out-Null
  if ($LASTEXITCODE) { throw 'Fresh governance check failed' }
  & "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $item.source_path -ObjectKey $item.r2_key -MaxObjectBytes 150000000 -MaxProjectedStorageBytes $policy.maximum_projected_r2_bytes | Out-Null
  $public = & "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $item.source_path -PublicUrl $item.public_url
  $result.results += [ordered]@{id=$item.id;source_url=$item.source_url;r2_key=$item.r2_key;public_url=$item.public_url;expected_size_bytes=$item.expected_size_bytes;expected_checksum_sha256=$item.expected_checksum_sha256;public_size_bytes=$public.size_bytes;public_checksum_sha256=$public.checksum_sha256;byte_identical=$public.byte_identical;verified_at=$public.verified_at}
  $result.added_objects++;$result.added_bytes += $item.expected_size_bytes
  $result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 ($taskPath+'archive-result.json')
  Write-Host "Verified exact public bytes: $($item.r2_key)"
}
& "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath ($taskPath+'after-r2.json') | Out-Null
$after = Get-Content -Raw -Encoding UTF8 ($taskPath+'after-r2.json') | ConvertFrom-Json
if ($after.object_count -ne $before.object_count+3 -or $after.total_bytes -ne $before.total_bytes+133251) { throw 'Unexpected R2 delta' }
$index = @{};foreach ($object in $after.objects) { $index[$object.key]=$object }
foreach ($object in $before.objects) { if (-not $index.ContainsKey($object.key) -or $index[$object.key].etag -ne $object.etag -or $index[$object.key].size_bytes -ne $object.size_bytes) { throw 'Existing R2 object changed' } }
$result.state='complete';$result.after_objects=$after.object_count;$result.after_bytes=$after.total_bytes;$result.completed_at=(Get-Date).ToUniversalTime().ToString('o')
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 ($taskPath+'archive-result.json')

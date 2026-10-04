Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$taskRoot='project-state/governance/sunport-exact-archive-2026-10-04'
$key='transportation/transportation-plans/cabq-sunport-sustainable-airport-master-plan-2019.pdf'
$sha='d4583c4d9e5e1233c402f64222fd8837ff7f0fc0a352dc2d5153776842f39d02'
$source='research/staging/sunport-exact-archive-2026-10-04/original.pdf'
$policy=Get-Content project-state/r2-storage-policy.json -Raw -Encoding utf8 | ConvertFrom-Json
if ($policy.maximum_projected_r2_bytes -ne 13000000000) { throw 'Storage policy differs from owner baseline' }
$listing=Get-Content "$taskRoot/r2-before.json" -Raw -Encoding utf8 | ConvertFrom-Json
if ($listing.object_count -ne 1611 -or $listing.total_bytes -ne 10691241695) { throw 'R2 baseline mismatch' }
if (@($listing.objects | Where-Object key -eq $key).Count) { throw 'Canonical key already exists' }
if ((Get-Item -LiteralPath $source).Length -ne 280024902 -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha) { throw 'Source bytes differ from exact exception' }
$intent=[ordered]@{state='authorized_exact_object_upload_intent';recorded_at_utc=(Get-Date).ToUniversalTime().ToString('o');candidate_id='src-1f9cf39555e7be6f';object_key=$key;source_path=$source;size_bytes=280024902;sha256=$sha;key_absent_in_complete_listing=$true;baseline_objects=1611;baseline_bytes=10691241695;projected_objects=1612;projected_bytes=10971266597;authority="$taskRoot/authority.json";unchanged_original=$true;overwrite=$false;delete=$false}
$intent | ConvertTo-Json -Depth 8 | Set-Content "$taskRoot/upload-intent.json" -Encoding utf8
& python scripts/project/OwnerResources20261004.py refresh sunport-exact-archive-2026-10-04
if ($LASTEXITCODE) { throw 'Governance refresh failed' }
& python scripts/project/Resolve-TaskGovernance.py active --phase mutation --operation archive --candidate src-1f9cf39555e7be6f --r2-key $key --source-sha256 $sha
if ($LASTEXITCODE) { throw 'Governance preflight failed' }
# One invocation-specific exact-object limit; standing policy is unchanged.
$result=& ./scripts/upload-r2-document.ps1 -SourcePath $source -ObjectKey $key -MaxObjectBytes 280024902 -MaxProjectedStorageBytes 13000000000 -Confirm:$false
$result | ConvertTo-Json -Depth 8 | Set-Content "$taskRoot/upload-result.json" -Encoding utf8
& ./scripts/project/Test-R2PublicObject.ps1 -SourcePath $source -PublicUrl "https://files.abqinfo.com/$key" | ConvertTo-Json -Depth 8 | Set-Content "$taskRoot/public-verification.json" -Encoding utf8
& ./scripts/project/Get-R2Inventory.ps1 -OutputPath "$taskRoot/r2-after.json"
if ($LASTEXITCODE) { throw 'Final R2 listing failed' }
$after=Get-Content "$taskRoot/r2-after.json" -Raw -Encoding utf8 | ConvertFrom-Json
if ($after.object_count -ne 1612 -or $after.total_bytes -ne 10971266597) { throw 'Final storage mismatch' }

[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$taskRoot='project-state/governance/mcduffie-review-2026-10-06/'
$intent=Get-Content ($taskRoot+'r2-preflight.json') -Raw -Encoding utf8|ConvertFrom-Json
if($intent.state -ne 'upload_intent_saved_no_put_yet'){throw 'Unexpected upload state'}
if(Test-Path ($taskRoot+'r2-result.json')){throw 'Upload result exists; reconcile and verify instead of PUT'}
& "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath 'tmp/mcduffie-r2-fresh.json'|Out-Null
$prior=Get-Content ($taskRoot+'r2-live-before.json') -Raw -Encoding utf8|ConvertFrom-Json
$fresh=Get-Content 'tmp/mcduffie-r2-fresh.json' -Raw -Encoding utf8|ConvertFrom-Json
$signature={param($objects) @($objects|ForEach-Object {$_.key+'|'+$_.size_bytes+'|'+$_.etag})}
if(Compare-Object (& $signature $prior.objects) (& $signature $fresh.objects)){throw 'R2 drift before PUT'}
if(@($fresh.objects|Where-Object {$_.key -ieq $intent.r2_key -or $_.size_bytes -eq $intent.added_bytes}).Count){throw 'Key or same-size collision'}
& python "$PSScriptRoot/Resolve-TaskGovernance.py" active --phase mutation --operation archive --candidate $intent.candidate_id --r2-key $intent.r2_key --source-sha256 $intent.sha256 |Out-Null
if($LASTEXITCODE){throw 'Fresh governance failed'}
$upload=@(& "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $intent.source -ObjectKey $intent.r2_key -MaxObjectBytes 150000000 -MaxProjectedStorageBytes 13000000000|Where-Object {$_.PSObject.Properties['ObjectKey']})
if($upload.Count -ne 1){throw 'Uploader returned no single result'}
$result=[ordered]@{candidate_id=$intent.candidate_id;key=$intent.r2_key;size_bytes=$intent.added_bytes;sha256=$intent.sha256;state='uploaded_pending_public_verification';verified=$false;upload=$upload[0];recorded_at=(Get-Date).ToUniversalTime().ToString('o')}
$result|ConvertTo-Json -Depth 20|Set-Content ($taskRoot+'r2-result.json') -Encoding utf8
$verification=& "$PSScriptRoot/Test-R2PublicObject.ps1" -SourcePath $intent.source -PublicUrl ('https://files.abqinfo.com/'+$intent.r2_key)
if(-not $verification.byte_identical -or $verification.size_bytes -ne $intent.added_bytes -or $verification.checksum_sha256 -cne $intent.sha256){throw 'Public full-byte verification failed'}
$result.verified=$true;$result.state='public_exact_bytes_verified';$result['public_verification']=$verification
$result|ConvertTo-Json -Depth 20|Set-Content ($taskRoot+'r2-result.json') -Encoding utf8
& "$PSScriptRoot/Get-R2Inventory.ps1" -OutputPath ($taskRoot+'r2-live-after.json')|Out-Null
Write-Output 'One original uploaded without overwrite; full public GET size/SHA-256 match.'

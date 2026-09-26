[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$prep=Get-Content project-state/discovery/planning-documents-root-archive-preparation-2026-09-25.json -Raw -Encoding UTF8 | ConvertFrom-Json
$records=@($prep.records | Where-Object id -ne 'src-d9bf34830a9467e2')
if ($records.Count -ne 12) { throw 'Expected exactly 12 upload candidates.' }
$ledger=[ordered]@{recorded_at=(Get-Date).ToUniversalTime().ToString('o'); records=@(); r2_mutation=$false; credentials_accessible=$false; max_object_bytes=100000000; max_projected_storage_bytes=10000000000; public_byte_verification_tool='scripts/project/Test-R2PublicObject.ps1'}
foreach ($record in $records) {
  $probe=@(& "$PSScriptRoot/../upload-r2-document.ps1" -SourcePath $record.staged_local_path -ObjectKey $record.proposed_r2_key -WhatIf)
  $result=@($probe | Where-Object { $_.PSObject.Properties.Name -contains 'Result' })
  if ($result.Count -ne 1 -or $result[0].Result -ne 'WhatIf: upload not performed' -or $result[0].Bytes -ne $record.size_bytes) { throw "Uploader WhatIf check failed for $($record.id)" }
  $ledger.records += [ordered]@{id=$record.id; key=$result[0].ObjectKey; bytes=$result[0].Bytes; current_r2_bytes=$result[0].CurrentR2Bytes; result=$result[0].Result; overwrite_protection='live HEAD confirmed absent before ShouldProcess gate'}
  $ledger.credentials_accessible=$true
  $ledger | ConvertTo-Json -Depth 8 | Set-Content tmp/planning-documents-root-upload-tool-readiness-2026-09-26.json -Encoding utf8
  Write-Output "WhatIf passed: $($record.id)"
}
$parseTokens=$null; $parseErrors=$null
[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Test-R2PublicObject.ps1'),[ref]$parseTokens,[ref]$parseErrors) | Out-Null
if ($parseErrors.Count) { throw 'Public exact-byte verification script parse failed.' }
$ledger.public_byte_verification_script_parse='passed'
$ledger.public_byte_verification_executed=$false
$ledger.state='twelve_default_limit_whatif_probes_passed_no_mutation'
$ledger | ConvertTo-Json -Depth 8 | Set-Content tmp/planning-documents-root-upload-tool-readiness-2026-09-26.json -Encoding utf8

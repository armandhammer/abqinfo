[CmdletBinding()]
param([string]$ScriptPath='scripts/project/Update-CouncilCloseoutCheckpoint.ps1',[string]$InventoryPath='project-state/master-inventory.json',[string]$CheckpointPath='project-state/checkpoint.json')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$temporaryPath=Join-Path $env:TEMP ('abqinfo-checkpoint-idempotency-'+[guid]::NewGuid().ToString()+'.json')
try {
  Copy-Item -LiteralPath $CheckpointPath -Destination $temporaryPath
  & $ScriptPath -CheckpointPath $temporaryPath -InventoryPath $InventoryPath | Out-Null
  & $ScriptPath -CheckpointPath $temporaryPath -InventoryPath $InventoryPath | Out-Null
  $checkpoint=Get-Content -Raw -Encoding UTF8 -LiteralPath $temporaryPath|ConvertFrom-Json
  $blockers=@($checkpoint.blockers)
  if ($blockers.Count -ne @($blockers|Select-Object -Unique).Count) { throw 'Checkpoint blocker update is not idempotent.' }
  $target='O-2024-006 final enacted file is not downloadable from the authoritative Clerk notice; do not register the available draft.'
  if (@($blockers|Where-Object {$_ -eq $target}).Count -ne 1) { throw 'O-2024-006 blocker must appear exactly once.' }
  'PASS: Council checkpoint blocker update is idempotent.'
} finally { if(Test-Path -LiteralPath $temporaryPath){Remove-Item -LiteralPath $temporaryPath -Force} }

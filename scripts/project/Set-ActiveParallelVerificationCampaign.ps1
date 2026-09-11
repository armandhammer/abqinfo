[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ManifestPath,
  [string]$ActiveRunPath='project-state/active-run.json',
  [switch]$Replace,
  [string]$CoordinatorLeasePath,
  [string]$CoordinatorOwnerToken
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/ParallelVerification.Campaign.Common.ps1"

& git symbolic-ref --quiet HEAD|Out-Null
if($LASTEXITCODE){throw 'Only the coordinator on an attached branch may set the active campaign.'}
if(-not$CoordinatorLeasePath){$gitCommon=(& git rev-parse --git-common-dir).Trim();if(-not[IO.Path]::IsPathRooted($gitCommon)){$gitCommon=Join-Path (Get-Location).Path $gitCommon};$CoordinatorLeasePath=Join-Path $gitCommon 'abqinfo-verification-locks/campaign-coordinator.lock'}
Assert-ParallelVerificationCoordinatorLeaseAccess -LeasePath ([IO.Path]::GetFullPath($CoordinatorLeasePath)) -OwnerToken $CoordinatorOwnerToken
$manifestFull=[IO.Path]::GetFullPath($ManifestPath)
$campaign=Read-ParallelVerificationJson $manifestFull
$errors=@(Test-ParallelVerificationCampaignObject $campaign);if($errors.Count){throw "Campaign validation failed: $($errors -join '; ')"}
if(((Get-Item -LiteralPath $manifestFull).Attributes -band [IO.FileAttributes]::ReadOnly)-eq 0){throw 'Campaign manifest is not read-only.'}
$activeFull=[IO.Path]::GetFullPath($ActiveRunPath)
if((Test-Path -LiteralPath $activeFull)-and -not $Replace){throw 'An active-run pointer already exists. Use Replace only after reviewing the existing campaign.'}
$pointer=[ordered]@{schema_version=1;type='parallel-verification-campaign';campaign_id=[string]$campaign.campaign_id;campaign_sha256=[string]$campaign.campaign_sha256;manifest_path=$manifestFull;artifact_root=Split-Path -Parent $manifestFull;base_commit=[string]$campaign.base_commit;updated_at=(Get-Date).ToUniversalTime().ToString('o');owner='coordinator'}
$parent=Split-Path -Parent $activeFull;if(-not(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent -Force|Out-Null}
$temporary="$activeFull.tmp-$PID-$([guid]::NewGuid().ToString('N'))"
try{[IO.File]::WriteAllText($temporary,($pointer|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $temporary -Destination $activeFull -Force}finally{if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary -Force}}
$pointer|ConvertTo-Json -Depth 8

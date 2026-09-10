[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ManifestPath,
  [Parameter(Mandatory)][string]$WorktreeRoot,
  [switch]$PlanOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/ParallelVerification.Campaign.Common.ps1"

$manifestFull=[IO.Path]::GetFullPath($ManifestPath);$campaign=Read-ParallelVerificationJson $manifestFull;$errors=@(Test-ParallelVerificationCampaignObject $campaign);if($errors.Count){throw "Campaign validation failed: $($errors -join '; ')"}
$repo=(& git rev-parse --show-toplevel).Trim();if($LASTEXITCODE){throw 'Unable to resolve repository root.'};$repo=[IO.Path]::GetFullPath($repo).TrimEnd('\','/')
$root=[IO.Path]::GetFullPath($WorktreeRoot).TrimEnd('\','/');if($root-eq$repo -or $root.StartsWith("$repo\",[StringComparison]::OrdinalIgnoreCase)){throw 'WorktreeRoot must be outside the repository.'}
$commit=(& git rev-parse "$($campaign.base_commit)^{commit}").Trim();if($LASTEXITCODE -or $commit-ne[string]$campaign.base_commit){throw 'Campaign base commit cannot be resolved exactly.'}
$inventoryPath=[string]$campaign.inventory_path;if(-not[IO.Path]::IsPathRooted($inventoryPath)){$inventoryPath=Join-Path $repo $inventoryPath};if((Get-ParallelVerificationFileHash $inventoryPath)-ne[string]$campaign.inventory_sha256){throw 'Coordinator inventory does not match campaign snapshot.'}
$plans=foreach($lane in @($campaign.lanes)){[pscustomobject][ordered]@{lane_id=$lane;path=Join-Path (Join-Path $root ([string]$campaign.campaign_id)) ([string]$lane);commit=$commit;mode='detached read-only campaign lane'}}
if(-not$PlanOnly){foreach($plan in $plans){if(Test-Path -LiteralPath $plan.path){throw "Worktree path exists: $($plan.path)"}};New-Item -ItemType Directory -Path (Join-Path $root ([string]$campaign.campaign_id)) -Force|Out-Null;foreach($plan in $plans){& git worktree add --detach $plan.path $commit;if($LASTEXITCODE){throw "Unable to create worktree for lane $($plan.lane_id)"}}}
[pscustomobject][ordered]@{campaign_id=$campaign.campaign_id;manifest_path=$manifestFull;plan_only=[bool]$PlanOnly;worktrees=@($plans)}|ConvertTo-Json -Depth 6

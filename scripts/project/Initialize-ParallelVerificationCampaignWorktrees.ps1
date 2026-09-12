[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$ManifestPath,
  [Parameter(Mandatory)][string]$WorktreeRoot,
  [switch]$PlanOnly,
  [switch]$ResumeExisting
)

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. "$PSScriptRoot/ParallelVerification.Campaign.Common.ps1"

$manifestFull=[IO.Path]::GetFullPath($ManifestPath);$campaign=Read-ParallelVerificationJson $manifestFull;$errors=@(Test-ParallelVerificationCampaignObject $campaign);if($errors.Count){throw "Campaign validation failed: $($errors -join '; ')"}
$repo=(& git rev-parse --show-toplevel).Trim();if($LASTEXITCODE){throw 'Unable to resolve repository root.'};$repo=[IO.Path]::GetFullPath($repo).TrimEnd('\','/')
$root=[IO.Path]::GetFullPath($WorktreeRoot).TrimEnd('\','/');if($root-eq$repo -or $root.StartsWith("$repo\",[StringComparison]::OrdinalIgnoreCase)){throw 'WorktreeRoot must be outside the repository.'}
$commit=(& git rev-parse "$($campaign.base_commit)^{commit}").Trim();if($LASTEXITCODE -or $commit-ne[string]$campaign.base_commit){throw 'Campaign base commit cannot be resolved exactly.'}
$inventoryPath=[string]$campaign.inventory_path;if(-not[IO.Path]::IsPathRooted($inventoryPath)){$inventoryPath=Join-Path $repo $inventoryPath};if((Get-ParallelVerificationFileHash $inventoryPath)-ne[string]$campaign.inventory_sha256){throw 'Coordinator inventory does not match campaign snapshot.'}
$plans=foreach($lane in @($campaign.lanes)){[pscustomobject][ordered]@{lane_id=$lane;path=Join-Path (Join-Path $root ([string]$campaign.campaign_id)) ([string]$lane);commit=$commit;mode='detached read-only campaign lane';state=if(Test-Path -LiteralPath (Join-Path (Join-Path $root ([string]$campaign.campaign_id)) ([string]$lane))){'existing'}else{'planned'}}}
if(-not$PlanOnly){
  New-Item -ItemType Directory -Path (Join-Path $root ([string]$campaign.campaign_id)) -Force|Out-Null
  foreach($plan in $plans){
    if(Test-Path -LiteralPath $plan.path){
      if(-not$ResumeExisting){throw "Worktree path exists: $($plan.path)"}
      $existingCommit=(& git -C $plan.path rev-parse HEAD).Trim();if($LASTEXITCODE -or $existingCommit-ne$commit){throw "Existing worktree is not at the campaign commit: $($plan.path)"}
      & git -C $plan.path symbolic-ref --quiet HEAD|Out-Null;if(-not$LASTEXITCODE){throw "Existing campaign worktree is not detached: $($plan.path)"}
      $dirty=@(& git -C $plan.path status --porcelain);if($LASTEXITCODE -or $dirty.Count){throw "Existing campaign worktree is not clean: $($plan.path)"}
      $plan.state='reused'
      continue
    }
    & git worktree add --detach $plan.path $commit | Out-Null;if($LASTEXITCODE){throw "Unable to create worktree for lane $($plan.lane_id)"};$plan.state='created'
  }
}
[pscustomobject][ordered]@{campaign_id=$campaign.campaign_id;manifest_path=$manifestFull;plan_only=[bool]$PlanOnly;worktrees=@($plans)}|ConvertTo-Json -Depth 6

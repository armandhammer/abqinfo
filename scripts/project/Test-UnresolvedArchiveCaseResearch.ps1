[CmdletBinding()]
param(
    [string]$ResearchPath = 'project-state/discovery/archive-reconciliation-unresolved-case-research-2026-09-17.json',
    [string]$R2Path = 'project-state/r2-inventory.json',
    [string]$LiveR2Path = 'project-state/discovery/live-r2-object-inventory-2026-09-16.json',
    [string]$MasterPath = 'project-state/master-inventory.json'
)
$ErrorActionPreference = 'Stop'
function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
function Fail([string]$Message) { throw $Message }
$research = Read-Json $ResearchPath
$r2 = Read-Json $R2Path
$live = Read-Json $LiveR2Path
$master = Read-Json $MasterPath
$ids = @('src-6735737588d294e0','src-3c9907796a0cfaf3','src-f6feb3549d055097')
if (@($research.cases).Count -ne 3 -or ((@($research.cases.master_id | Sort-Object) -join ',') -ne (($ids | Sort-Object) -join ','))) { Fail 'Research artifact does not cover exactly the three authorized cases.' }
if (@($research.cases | Where-Object user_decision_required -like 'Yes:*').Count -ne 2) { Fail 'Research artifact must isolate exactly two remaining user decisions.' }
if ([int]$live.object_count -ne 1180 -or [int64]$live.total_bytes -ne 8614076524) { Fail 'Saved live-R2 reconciliation baseline changed.' }
$liveByKey = @{}; foreach ($object in @($live.objects)) { $liveByKey[[string]$object.key] = $object }
$repoByKey = @{}; foreach ($object in @($r2.objects)) { if ($repoByKey.ContainsKey([string]$object.key)) { Fail "Duplicate R2 key: $($object.key)" }; $repoByKey[[string]$object.key] = $object }
if ($repoByKey.Count -lt $liveByKey.Count) { Fail 'Repository R2 inventory is smaller than saved live baseline.' }
foreach ($key in $liveByKey.Keys) { foreach ($field in @('key','size_bytes','last_modified','etag','storage_class','public_url')) { if (-not $repoByKey.ContainsKey($key) -or [string]$repoByKey[$key].$field -ne [string]$liveByKey[$key].$field) { Fail "R2 equality mismatch for $key field $field." } } }
$masterById = @{}; foreach ($candidate in @($master.candidates)) { $masterById[[string]$candidate.id] = $candidate }
foreach ($case in @($research.cases)) { $candidate = $masterById[[string]$case.master_id]; if ($null -eq $candidate -or $candidate.r2_key -ne $case.r2_key) { Fail "Master factual linkage changed for $($case.master_id)." } }
if ($research.campaign_conclusion.site_content_modified -ne $false -or $research.campaign_conclusion.live_r2_modified -ne $false) { Fail 'Research artifact records an unauthorized external/content change.' }
Write-Output 'Unresolved archive-case research validation passed: 3 cases, 2 user decisions, and exact R2 accounting preserved.'

[CmdletBinding()]
param(
    [string]$LiveR2Path = 'project-state/discovery/live-r2-object-inventory-2026-09-16.json',
    [string]$R2Path = 'project-state/r2-inventory.json'
)
$ErrorActionPreference = 'Stop'
function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -DateKind String }
function Fail([string]$Message) { throw $Message }
$live = Read-Json $LiveR2Path
$repo = Read-Json $R2Path
$liveByKey = @{}
foreach ($o in @($live.objects)) { if ($liveByKey.ContainsKey([string]$o.key)) { Fail "Duplicate live key: $($o.key)" }; $liveByKey[[string]$o.key] = $o }
$repoKeys = @{}
foreach ($o in @($repo.objects)) { if ($repoKeys.ContainsKey([string]$o.key)) { Fail "Duplicate repository key: $($o.key)" }; $repoKeys[[string]$o.key] = $true }
if ($liveByKey.Count -ne $repoKeys.Count) { Fail 'Live and repository key counts differ.' }
foreach ($key in $liveByKey.Keys) { if (-not $repoKeys.ContainsKey($key)) { Fail "Repository key absent from saved live inventory: $key" } }
$before = @($repo.objects)
$repo.objects = @($before | ForEach-Object {
    $liveObject = $liveByKey[[string]$_.key]
    [ordered]@{ key = $liveObject.key; size_bytes = $liveObject.size_bytes; last_modified = $liveObject.last_modified; etag = $liveObject.etag; storage_class = $liveObject.storage_class; public_url = $liveObject.public_url }
} | Sort-Object key)
$repo.object_count = $repo.objects.Count
$totalBytes = [int64]0
foreach ($object in @($repo.objects)) { $totalBytes += [int64]$object.size_bytes }
$repo.total_bytes = $totalBytes
$full = [IO.Path]::GetFullPath($R2Path)
$tmp = "$full.final-metadata.tmp"
[IO.File]::WriteAllText($tmp, ($repo | ConvertTo-Json -Depth 100) + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $tmp -Destination $full -Force
[pscustomobject]@{ normalized_from_saved_live = $repo.objects.Count; final_object_count = $repo.object_count; final_total_bytes = $repo.total_bytes } | ConvertTo-Json

[CmdletBinding()]
param(
    [string]$ManifestPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-repair-manifest-2026-09-17.json',
    [string]$InventoryPath = 'project-state/master-inventory.json',
    [string]$LiveR2Path = 'project-state/discovery/live-r2-object-inventory-2026-09-16.json',
    [string]$OutputPath = 'project-state/discovery/archive-reconciliation-provenance-verification-2026-09-17.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$candidateByAction = @{
    'repair-001' = 'src-6735737588d294e0'; 'repair-007' = 'src-bd084d192e7b78ce'; 'repair-008' = 'src-7405cfc41e5500c4'; 'repair-017' = 'src-3c9907796a0cfaf3'; 'repair-019' = 'src-0782d8521e42a068'; 'repair-020' = 'src-f6feb3549d055097'
    'repair-021' = 'src-bb1e08fed8c049a7'; 'repair-022' = 'src-087842cdf31bbd1c'; 'repair-023' = 'src-030f7d2a680a31d4'; 'repair-024' = 'src-4360b7ad1acbabdb'; 'repair-025' = 'src-7dd4dca158dd74d0'; 'repair-026' = 'src-ff0cce054f5417f8'; 'repair-027' = 'src-14f45e5400b067bc'; 'repair-028' = 'src-d763272eeccf1740'; 'repair-029' = 'src-51c281bcea861ad9'; 'repair-030' = 'src-f34377f7d362089c'; 'repair-031' = 'src-a729bb09514a9eb3'; 'repair-032' = 'src-a1823b506c80a5e1'; 'repair-033' = 'src-7cd7534bc544a4cb'; 'repair-034' = 'src-3916288248bba241'; 'repair-035' = 'src-f2022d135f87e307'; 'repair-036' = 'src-df2ad3ce6a0795b8'; 'repair-037' = 'src-f6392e3d79ac62a5'; 'repair-038' = 'src-4055919dde906ce1'; 'repair-039' = 'src-81b04c1358323136'; 'repair-040' = 'src-fc539ddea39cd340'; 'repair-041' = 'src-65575cfa5553d19a'
}

$manifest = Get-Content -Raw -Encoding UTF8 $ManifestPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 $InventoryPath | ConvertFrom-Json
$live = Get-Content -Raw -Encoding UTF8 $LiveR2Path | ConvertFrom-Json
$actions = @($manifest.actions | Where-Object safety_gate -eq 'blocked_on_provenance_research')
if ($actions.Count -ne 27 -or $candidateByAction.Count -ne 27) { throw 'Expected exactly 27 provenance actions and mappings.' }
$masterById = @{}; foreach ($candidate in @($inventory.candidates)) { $masterById[[string]$candidate.id] = $candidate }
$liveByKey = @{}; foreach ($object in @($live.objects)) { $liveByKey[[string]$object.key] = $object }

function Get-RemoteHash([string]$Url, [string]$Suffix) {
    $path = Join-Path ([IO.Path]::GetTempPath()) ("abqinfo-provenance-$([guid]::NewGuid().ToString('n'))-$Suffix.pdf")
    try {
        Invoke-WebRequest -Uri $Url -OutFile $path -UseBasicParsing -MaximumRedirection 10 -TimeoutSec 180 -Headers @{ 'Cache-Control' = 'no-cache'; 'User-Agent' = 'ABQInfo provenance verification/1.0' }
        $file = Get-Item -LiteralPath $path
        [pscustomobject]@{ url = $Url; size_bytes = [int64]$file.Length; checksum_sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
    } finally {
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
    }
}

$results = foreach ($action in $actions | Sort-Object action_id) {
    $candidateId = $candidateByAction[[string]$action.action_id]
    if (-not $candidateId -or -not $masterById.ContainsKey($candidateId)) { throw "Missing master candidate for $($action.action_id)." }
    $candidate = $masterById[$candidateId]
    $key = [string](@($action.affected_r2_keys)[0])
    if (-not $liveByKey.ContainsKey($key)) { throw "Missing saved live-R2 object for '$key'." }
    $officialUrl = if ($candidate.direct_file_url) { [string]$candidate.direct_file_url } else { [string]$candidate.source_url }
    if ([string]::IsNullOrWhiteSpace($officialUrl)) { throw "No authoritative direct-file URL for $candidateId." }
    $official = Get-RemoteHash $officialUrl 'official'
    $r2 = Get-RemoteHash ([string]$liveByKey[$key].public_url) 'r2'
    [ordered]@{
        action_id = [string]$action.action_id
        issue_group_id = [string](@($action.covered_issue_group_ids)[0])
        r2_key = $key
        master_candidate_id = $candidateId
        authoritative_direct_file_url = $officialUrl
        saved_live_r2_object = $liveByKey[$key]
        official_file = $official
        public_r2_file = $r2
        byte_identical = ($official.size_bytes -eq $r2.size_bytes -and $official.checksum_sha256 -eq $r2.checksum_sha256)
        master_size_matches_official = ($null -ne $candidate.size_bytes -and [int64]$candidate.size_bytes -eq $official.size_bytes)
        master_checksum_matches_official = (-not [string]::IsNullOrWhiteSpace([string]$candidate.checksum_sha256) -and [string]$candidate.checksum_sha256 -eq $official.checksum_sha256)
    }
}

$output = [ordered]@{ schema_version = 1; generated_at = (Get-Date).ToUniversalTime().ToString('o'); purpose = 'Targeted read-only byte comparison of the 27 archive-reconciliation provenance cases; no storage mutation performed.'; manifest = $ManifestPath; master_inventory = $InventoryPath; saved_live_r2_inventory = $LiveR2Path; result_count = @($results).Count; byte_identical_count = @($results | Where-Object byte_identical).Count; results = @($results) }
$fullPath = [IO.Path]::GetFullPath($OutputPath); $temporaryPath = "$fullPath.tmp-$PID"; [IO.File]::WriteAllText($temporaryPath, ($output | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
Write-Output ("Verified {0}/{1} byte-identical official-to-R2 pairs." -f $output.byte_identical_count, $output.result_count)

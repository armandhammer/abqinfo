[CmdletBinding()]
param(
    [string]$ReportPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-2026-09-16.json',
    [string]$MasterInventoryPath = 'project-state/master-inventory.json',
    [string]$R2InventoryPath = 'project-state/r2-inventory.json',
    [string]$OriginRef = 'origin/main',
    [string]$OutputPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-classification-2026-09-16.json',
    [string]$ReviewPacketPath = 'project-state/discovery/live-abqinfo-archive-reconciliation-review-packet-2026-09-16.json'
)
$ErrorActionPreference = 'Stop'
function Arr($v) { @($v) }
function Unique($v) { @(Arr $v | Where-Object { $_ -ne $null -and "$($_)" -ne '' } | Sort-Object -Unique) }
function Run-Git([string[]]$Args) { $o = & git @Args 2>$null; if ($LASTEXITCODE -ne 0) { return '' }; return (($o -join "`n").Trim()) }
function Get-Recs([string]$Key) { if ($masterByKey.ContainsKey($Key)) { return @($masterByKey[$Key]) }; return @() }

$report = Get-Content $ReportPath -Raw | ConvertFrom-Json
$master = Get-Content $MasterInventoryPath -Raw | ConvertFrom-Json
$r2 = Get-Content $R2InventoryPath -Raw | ConvertFrom-Json
$masterRecords = Arr $master.candidates
$r2Objects = Arr $r2.objects
$masterByKey = @{}
foreach ($rec in $masterRecords) { if ($rec.r2_key) { if (-not $masterByKey.ContainsKey($rec.r2_key)) { $masterByKey[$rec.r2_key] = [System.Collections.Generic.List[object]]::new() }; $masterByKey[$rec.r2_key].Add($rec) } }
$r2ByKey = @{}; foreach ($o in $r2Objects) { $r2ByKey[$o.key] = $o }
$hashToKeys = @{}
foreach ($rec in $masterRecords) { if ($rec.r2_key -and $rec.checksum_sha256) { $h=$rec.checksum_sha256.ToLowerInvariant(); if (-not $hashToKeys.ContainsKey($h)) { $hashToKeys[$h]=[System.Collections.Generic.HashSet[string]]::new() }; [void]$hashToKeys[$h].Add($rec.r2_key) } }
$storageDuplicateGroups = @(foreach ($h in $hashToKeys.Keys) { $keys=@($hashToKeys[$h]); if ($keys.Count -gt 1) { [pscustomobject]@{ sha256=$h; r2_keys=$keys; key_count=$keys.Count; records=@(foreach($k in $keys){@($masterByKey[$k]|ForEach-Object id)}) } } })
$storageDupByKey=@{}; foreach($g in $storageDuplicateGroups){foreach($k in $g.r2_keys){$storageDupByKey[$k]=$g}}

$publishedMissing = @(Arr $report.published_r2_links | Where-Object { $_.classification -eq 'published_missing_repository_r2_record' })
$unreferenced = @(Arr $report.r2_objects | Where-Object { -not $_.published })
$expectedMissing = @(Arr $report.expected_published_records | Where-Object { $_.classification -eq 'expected_page_missing_live_link' })

$classifiedUnreferenced = @(foreach ($o in $unreferenced) {
    $recs=Get-Recs $o.key; $repo=$r2ByKey[$o.key]; $dup=$storageDupByKey[$o.key]
    $statuses=Unique ($recs | ForEach-Object status); $ids=@($recs|ForEach-Object id)
    $class='unreferenced_unaccounted_storage_candidate'; $review=$true; $reason='No repository R2 or master record accounts for this live object.'
    if ($dup) { $class='unreferenced_storage_duplicate_of_other_r2_key'; $review=$true; $reason='Different R2 keys share an exact recorded SHA-256; retention/canonicalization requires review.' }
    elseif ($recs.Count -gt 0 -and ($statuses | Where-Object { $_ -notin @('superseded','duplicate','excluded') }).Count -eq 0) { $class='unreferenced_superseded_or_duplicate_master_object'; $review=$false; $reason='All linked master records are superseded, duplicate, or excluded.' }
    elseif ($recs.Count -gt 0) { $class='unreferenced_known_master_object'; $review=$true; $reason='A live but unpublished object has active/validated master linkage; editorial retention or publication intent is unresolved.' }
    elseif ($repo) { $class='unreferenced_repository_inventory_only'; $review=$true; $reason='Object is in repository R2 inventory but has no master or live-page linkage.' }
    [pscustomobject]@{ key=$o.key; public_url=$o.public_url; size_bytes=$o.size_bytes; etag=$o.etag; master_record_ids=$ids; master_statuses=$statuses; repository_r2_record_present=[bool]$repo; checksum_sha256s=Unique ($recs|ForEach-Object checksum_sha256); storage_duplicate_group=$dup; classification=$class; mechanically_resolvable=(-not $review); requires_human_review=$review; review_reason=$reason }
})

$classifiedPublished = @(foreach ($p in $publishedMissing) {
    $recs=Get-Recs $p.key; $v=$p.verification; $sizeMatch=($v.size_match -eq $true); $hashMatch=($v.hash_match -eq $true)
    if ($recs.Count -gt 0 -and ($sizeMatch -or $hashMatch)) { $class='published_object_missing_repository_r2_record_stale_inventory'; $review=$false; $reason='Live object matches recorded master size/hash; repository r2-inventory is stale.' }
    elseif ($recs.Count -eq 0) { $class='published_object_without_master_record'; $review=$true; $reason='Published live object has no authoritative master record.' }
    else { $class='published_object_metadata_conflict'; $review=$true; $reason='Published object lacks sufficient exact agreement with recorded master metadata.' }
    [pscustomobject]@{ key=$p.key; live_pages=$p.live_pages; live_size_bytes=$p.verification.remote_size_bytes; master_record_ids=@($p.master_record_ids); master_statuses=@($p.master_statuses); expected_sizes=@($p.expected_sizes); expected_hashes=@($p.expected_hashes); verification=$v; classification=$class; mechanically_resolvable=(-not $review); requires_human_review=$review; review_reason=$reason }
})

$originCache=@{}
$classifiedExpected = @(foreach ($e in $expectedMissing) {
    $links=@($report.repository_r2_links | Where-Object key -eq $e.key)
    $paths=Unique ($links|ForEach-Object content_path)
    $originHits=@(); $history=@()
    foreach($path in $paths) {
        if (-not $originCache.ContainsKey($path)) { $originCache[$path]=Run-Git @('show',("{0}:{1}" -f $OriginRef,$path)) }
        if ($originCache[$path] -and $originCache[$path].IndexOf($e.key,[System.StringComparison]::OrdinalIgnoreCase) -ge 0) { $originHits += $path }
        $h=Run-Git @('log','--all','--format=%h %s','-S', $e.key,'--',$path); if($h){$history += $h -split "`n"}
    }
    if ($links.Count -gt 0 -and $originHits.Count -eq 0) { $class='expected_link_present_on_current_branch_not_live'; $review=$false; $reason='Repository content contains the expected link, but the live site does not; deployment lag.' }
    elseif ($links.Count -gt 0) { $class='expected_link_present_on_origin_not_live'; $review=$false; $reason='Origin/main contains the expected link, but the live site does not; deployment lag.' }
    else { $class='expected_link_absent_from_repository_content'; $review=$true; $reason='Expected published record has no matching current repository link; editorial implementation or metadata decision is required.' }
    [pscustomobject]@{ id=$e.id; title=$e.title; key=$e.key; expected_pages=$e.expected_pages; missing_expected_pages=$e.missing_expected_pages; current_repository_paths=$paths; origin_main_paths=Unique $originHits; targeted_history=Unique $history; classification=$class; mechanically_resolvable=(-not $review); requires_human_review=$review; review_reason=$reason }
})

$all=@($classifiedUnreferenced+$classifiedPublished+$classifiedExpected)
$counts=@{}; foreach($i in $all){if(-not $counts.ContainsKey($i.classification)){$counts[$i.classification]=0};$counts[$i.classification]++}
$overlap=[pscustomobject]@{ discrepancy_sets=@{ unreferenced_r2_objects=$classifiedUnreferenced.Count; published_missing_repository_r2_records=$classifiedPublished.Count; expected_not_live=$classifiedExpected.Count }; set_overlap_keys=@(); note='The three input discrepancy sets are mechanically disjoint by definition; storage-duplicate groups and repeated master IDs are annotations, not additional stored-file counts.'; duplicate_master_keys_count=@($report.duplicate_master_r2_keys).Count; actual_storage_duplicate_group_count=$storageDuplicateGroups.Count }
$output=[pscustomobject]@{ schema_version='1.0'; generated_at=(Get-Date).ToUniversalTime().ToString('o'); inputs=[pscustomobject]@{ report=$ReportPath; master_inventory=$MasterInventoryPath; r2_inventory=$R2InventoryPath; origin_ref=$OriginRef }; summary=[pscustomobject]@{ total_items=$all.Count; unreferenced=$classifiedUnreferenced.Count; published_missing_repository_r2=$classifiedPublished.Count; expected_not_live=$classifiedExpected.Count; mechanically_resolvable=@($all|Where-Object mechanically_resolvable).Count; requires_human_review=@($all|Where-Object requires_human_review).Count; category_counts=$counts; actual_storage_duplicate_groups=$storageDuplicateGroups.Count }; overlap=$overlap; storage_duplicate_groups=$storageDuplicateGroups; unreferenced_r2_objects=$classifiedUnreferenced; published_objects_missing_repository_r2_inventory=$classifiedPublished; expected_but_not_live=$classifiedExpected }
$output | ConvertTo-Json -Depth 12 | Set-Content -Path $OutputPath -Encoding utf8
$packet=[pscustomobject]@{ schema_version='1.0'; generated_at=$output.generated_at; source_classification=$OutputPath; summary=[pscustomobject]@{ review_items=@($all|Where-Object requires_human_review).Count; storage_duplicate_groups=$storageDuplicateGroups.Count }; cases=@($all|Where-Object requires_human_review) }
$packet | ConvertTo-Json -Depth 12 | Set-Content -Path $ReviewPacketPath -Encoding utf8
Write-Output ("Classified {0} discrepancies; {1} require human review." -f $all.Count,$packet.summary.review_items)

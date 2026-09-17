[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$LiveLinkInventoryPath,
  [Parameter(Mandatory)][string]$LiveR2InventoryPath,
  [Parameter(Mandatory)][string]$LiveVerificationPath,
  [Parameter(Mandatory)][string]$MasterInventoryPath,
  [Parameter(Mandatory)][string]$RepositoryR2InventoryPath,
  [string]$ContentRoot = 'content',
  [Parameter(Mandatory)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$liveLinks = Get-Content -Raw -Encoding UTF8 -LiteralPath $LiveLinkInventoryPath | ConvertFrom-Json
$liveR2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $LiveR2InventoryPath | ConvertFrom-Json
$verification = Get-Content -Raw -Encoding UTF8 -LiteralPath $LiveVerificationPath | ConvertFrom-Json
$master = Get-Content -Raw -Encoding UTF8 -LiteralPath $MasterInventoryPath | ConvertFrom-Json
$repoR2 = Get-Content -Raw -Encoding UTF8 -LiteralPath $RepositoryR2InventoryPath | ConvertFrom-Json

function Get-Key([string]$Url) { return ([uri]$Url).AbsolutePath.TrimStart('/') }
function Get-PagePath([string]$Url) { return ([uri]$Url).AbsolutePath.Trim('/').TrimEnd('/') }
function Get-PublicPageUrl([string]$RepositoryPath) {
  $route = $RepositoryPath.Replace('\','/').TrimStart('/')
  if ($route -match '^content/(.*)\.md$') { $route = $Matches[1] }
  if ($route -match '(^|/)(_index|index)$') { $route = $route -replace '(^|/)(_index|index)$','$1' }
  return 'https://abqinfo.com/' + $route.Trim('/') + '/'
}
function Get-EquivalentPageUrls([string]$Url) {
  $urls = [Collections.Generic.List[string]]::new(); $urls.Add($Url)
  $aliases = @{
    'https://abqinfo.com/maps/maps/' = 'https://abqinfo.com/maps-data/maps/'
    'https://abqinfo.com/public-works/stormwater/' = 'https://abqinfo.com/public-works/stormwater-drainage/'
    'https://abqinfo.com/city-data/public-safety/' = 'https://abqinfo.com/city-data/public-safety-data/'
  }
  if ($aliases.ContainsKey($Url)) { $urls.Add($aliases[$Url]) }
  return @($urls)
}

$liveR2Links = @($liveLinks.links | Where-Object is_r2_archive)
$liveByKey = @{}
foreach ($link in $liveR2Links) {
  $key = Get-Key $link.url
  if (-not $liveByKey.ContainsKey($key)) { $liveByKey[$key] = [Collections.Generic.List[object]]::new() }
  $liveByKey[$key].Add($link)
}
$liveObjects = @{}
foreach ($object in @($liveR2.objects)) { $liveObjects[[string]$object.key] = $object }
$repoObjects = @{}
foreach ($object in @($repoR2.objects)) { $repoObjects[[string]$object.key] = $object }
$masterByKey = @{}
foreach ($candidate in @($master.candidates)) {
  if (-not $candidate.r2_key) { continue }
  $key = [string]$candidate.r2_key
  if (-not $masterByKey.ContainsKey($key)) { $masterByKey[$key] = [Collections.Generic.List[object]]::new() }
  $masterByKey[$key].Add($candidate)
}
$verifiedByKey = @{}
foreach ($result in @($verification.results)) { $verifiedByKey[[string]$result.key] = $result }

$repoLinks = [Collections.Generic.List[object]]::new()
foreach ($file in @(Get-ChildItem -LiteralPath $ContentRoot -Recurse -Filter '*.md' | Sort-Object FullName)) {
  $relative = [IO.Path]::GetRelativePath((Get-Location).Path, $file.FullName).Replace('\','/')
  $lines = Get-Content -Encoding UTF8 -LiteralPath $file.FullName
  $heading = ''
  foreach ($line in $lines) {
    $headingMatch = [regex]::Match($line, '^\s{0,3}#{1,6}\s+(?<heading>.*?)\s*#*\s*$')
    if ($headingMatch.Success) { $heading = ($headingMatch.Groups['heading'].Value -replace '\s+',' ').Trim() }
    foreach ($match in [regex]::Matches($line, '\[(?<label>[^\]]*)\]\((?<url>https?://[^)\s]+)\)')) {
      $url = [string]$match.Groups['url'].Value
      $kind = if (([uri]$url).Host -eq 'files.abqinfo.com') { 'r2_archive' } elseif ($url -match '(?i)\.(pdf|docx?|xlsx?|csv|zip|pptx?|json)(?:$|[?#])') { 'document_or_data' } else { $null }
      if (-not $kind) { continue }
      $repoLinks.Add([ordered]@{ content_path=$relative; visible_item=[string]$match.Groups['label'].Value; nearest_heading=$heading; url=$url; link_kind=$kind; is_r2_archive=($kind -eq 'r2_archive'); key=if($kind -eq 'r2_archive'){Get-Key $url}else{$null} })
    }
  }
}
$repoR2Links = @($repoLinks | Where-Object is_r2_archive)

$published = foreach ($key in ($liveByKey.Keys | Sort-Object)) {
  $object = if ($liveObjects.ContainsKey($key)) { $liveObjects[$key] } else { $null }
  $repoObject = if ($repoObjects.ContainsKey($key)) { $repoObjects[$key] } else { $null }
  $records = if ($masterByKey.ContainsKey($key)) { @($masterByKey[$key] | ForEach-Object { $_ }) } else { @() }
  $check = if ($verifiedByKey.ContainsKey($key)) { $verifiedByKey[$key] } else { $null }
  $expectedSizes = @($records | Where-Object size_bytes | ForEach-Object {[int64]$_.size_bytes} | Sort-Object -Unique)
  $expectedHashes = @($records | Where-Object checksum_sha256 | ForEach-Object {[string]$_.checksum_sha256} | Sort-Object -Unique)
  $classification = if (-not $object) { 'published_missing_live_r2_object' }
    elseif (-not $repoObject) { 'published_missing_repository_r2_record' }
    elseif (-not @($records).Count) { 'published_without_master_record' }
    elseif (-not $check -or $check.http_status -lt 200 -or $check.http_status -ge 400) { 'published_resolution_failed' }
    elseif ($check.hash_checked -and -not $check.hash_match) { 'published_hash_mismatch' }
    elseif ($expectedSizes.Count -gt 1 -or $expectedHashes.Count -gt 1) { 'published_conflicting_master_metadata' }
    elseif ($expectedSizes.Count -eq 1 -and [int64]$object.size_bytes -ne $expectedSizes[0]) { 'published_size_mismatch' }
    else { 'published_verified' }
  [ordered]@{
    key=$key; live_occurrences=@($liveByKey[$key]).Count; live_pages=@($liveByKey[$key] | Select-Object -ExpandProperty page_url -Unique)
    live_object_present=[bool]$object; live_size_bytes=if($object){[int64]$object.size_bytes}else{$null}
    repository_r2_record_present=[bool]$repoObject; repository_r2_size_bytes=if($repoObject){[int64]$repoObject.size_bytes}else{$null}
    master_record_ids=@($records|ForEach-Object {[string]$_.id}); master_statuses=@($records|ForEach-Object {[string]$_.status}|Sort-Object -Unique)
    expected_sizes=$expectedSizes; expected_hashes=$expectedHashes
    verification=$check; classification=$classification
  }
}

$objects = foreach ($key in ($liveObjects.Keys | Sort-Object)) {
  $object = $liveObjects[$key]
  $records = if ($masterByKey.ContainsKey($key)) { @($masterByKey[$key] | ForEach-Object { $_ }) } else { @() }
  $publishedObject = $liveByKey.ContainsKey($key)
  $repoObject = $repoObjects.ContainsKey($key)
  $classification = if ($publishedObject -and $repoObject -and @($records).Count) { 'published_and_accounted' }
    elseif ($publishedObject -and -not $repoObject) { 'published_unlisted_in_repository_r2_inventory' }
    elseif ($publishedObject -and -not @($records).Count) { 'published_without_master_record' }
    elseif (-not $publishedObject -and $repoObject) { 'unreferenced_but_known_repository_object' }
    elseif (-not $publishedObject -and @($records).Count) { 'unreferenced_but_known_master_object' }
    else { 'unreferenced_unaccounted_object' }
  [ordered]@{key=$key;size_bytes=[int64]$object.size_bytes;last_modified=$object.last_modified;etag=$object.etag;public_url=$object.public_url;published=[bool]$publishedObject;repository_r2_record=[bool]$repoObject;master_record_ids=@($records|ForEach-Object {[string]$_.id});classification=$classification}
}

$expectedPublished = foreach ($candidate in @($master.candidates | Where-Object { $_.status -in @('implemented','validated') -and $_.r2_url })) {
  $key = if ($candidate.r2_key) {[string]$candidate.r2_key} else {Get-Key ([string]$candidate.r2_url)}
  $locations = @($candidate.implementation_locations | Where-Object { $_ })
  if (-not $locations.Count -and $candidate.implementation_location) { $locations = @([string]$candidate.implementation_location) }
  if (-not $locations.Count -and $candidate.proposed_canonical_page) { $locations = @([string]$candidate.proposed_canonical_page) }
  $expectedPages = @($locations | ForEach-Object { Get-PublicPageUrl ([string]$_) })
  $actualPages = if ($liveByKey.ContainsKey($key)) {@($liveByKey[$key] | Select-Object -ExpandProperty page_url -Unique)} else {@()}
  $acceptablePages = @($expectedPages | ForEach-Object { Get-EquivalentPageUrls $_ } | Sort-Object -Unique)
  $missingPages = @($expectedPages | Where-Object { @(Get-EquivalentPageUrls $_ | Where-Object { $_ -in $actualPages }).Count -eq 0 })
  [ordered]@{id=[string]$candidate.id;title=[string]$candidate.title;key=$key;expected_pages=$expectedPages;acceptable_live_pages=$acceptablePages;actual_live_pages=$actualPages;missing_expected_pages=$missingPages;published=[bool]@($actualPages).Count;classification=if(@($missingPages).Count){'expected_page_missing_live_link'}else{'expected_page_represented'}}
}

$duplicateKeys = foreach ($key in ($masterByKey.Keys | Sort-Object)) {
  $records = @($masterByKey[$key] | ForEach-Object { $_ })
  if (@($records).Count -gt 1) { [ordered]@{key=$key;record_count=@($records).Count;records=@($records|ForEach-Object {[ordered]@{id=$_.id;status=$_.status;title=$_.title;source_url=$_.source_url}});classification='duplicate_master_records_share_r2_key'} }
}
$superseded = @($master.candidates | Where-Object { $_.status -in @('superseded','duplicate') -and $_.r2_key } | ForEach-Object {[ordered]@{id=$_.id;status=$_.status;title=$_.title;key=$_.r2_key;exclusion_reason=$_.exclusion_reason}})
$repositoryOnly = foreach ($key in ($repoObjects.Keys | Where-Object { -not $liveObjects.ContainsKey($_) } | Sort-Object)) {
  $object = $repoObjects[$key]
  [ordered]@{key=$key;size_bytes=[int64]$object.size_bytes;last_modified=$object.last_modified;etag=$object.etag;public_url=$object.public_url;classification='repository_r2_inventory_object_absent_from_live_listing'}
}

$summary = [ordered]@{
  live_pages=$liveLinks.page_count; live_document_link_occurrences=$liveLinks.document_link_count; live_unique_r2_urls=$liveLinks.unique_r2_archive_url_count
  live_r2_object_count=$liveR2.object_count; live_r2_total_bytes=[int64]$liveR2.total_bytes; repository_r2_object_count=$repoR2.object_count; repository_r2_total_bytes=[int64]$repoR2.total_bytes
  published_verified=@($published|Where-Object classification -eq 'published_verified').Count; published_failures=@($published|Where-Object classification -ne 'published_verified').Count
  live_objects_published=@($objects|Where-Object published).Count; live_objects_unreferenced=@($objects|Where-Object {-not $_.published}).Count
  live_objects_without_master=@($objects|Where-Object {$_.classification -match 'without_master|unaccounted'}).Count; master_records_expected_published=$expectedPublished.Count; expected_pages_missing=@($expectedPublished|Where-Object classification -eq 'expected_page_missing_live_link').Count
  repository_r2_objects_absent_from_live_listing=@($repositoryOnly).Count
  duplicate_master_r2_key_groups=@($duplicateKeys).Count; superseded_or_duplicate_master_r2_records=$superseded.Count
}
$report = [ordered]@{schema_version=1;generated_at=(Get-Date).ToUniversalTime().ToString('o');summary=$summary;inputs=[ordered]@{live_links=$LiveLinkInventoryPath;live_r2=$LiveR2InventoryPath;live_verification=$LiveVerificationPath;master=$MasterInventoryPath;repository_r2=$RepositoryR2InventoryPath;content_root=$ContentRoot};published_r2_links=@($published);r2_objects=@($objects);repository_only_r2_objects=@($repositoryOnly);expected_published_records=@($expectedPublished);repository_r2_links=@($repoR2Links);duplicate_master_r2_keys=@($duplicateKeys);superseded_or_duplicate_master_records=$superseded}
$fullPath=[IO.Path]::GetFullPath($OutputPath);$temporaryPath="$fullPath.tmp-$PID";[IO.File]::WriteAllText($temporaryPath,($report|ConvertTo-Json -Depth 14),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
$summary | ConvertTo-Json -Compress

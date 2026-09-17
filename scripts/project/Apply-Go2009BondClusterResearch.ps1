[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DecisionPath = 'project-state/discovery/go2009-bond-cluster-research-2026-09-11.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$inventory = Get-Content -LiteralPath $InventoryPath -Raw -Encoding UTF8 | ConvertFrom-Json
$artifact = Get-Content -LiteralPath $DecisionPath -Raw -Encoding UTF8 | ConvertFrom-Json
$index = @{}; foreach ($candidate in @($inventory.candidates)) { $index[[string]$candidate.id] = $candidate }
$seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)

function Set-Decision($row, [string]$status) {
  $id=[string]$row.id; if(-not $seen.Add($id)){throw "Duplicate decision ID: $id"}; if(-not $index.ContainsKey($id)){throw "Missing candidate: $id"}
  $candidate=$index[$id]; if([string]$candidate.status -ne 'pending review'){throw "Unexpected candidate status: $id = $($candidate.status)"}
  $url=[string]$row.authoritative_url; $candidate.direct_file_url=$url; if(@($candidate.referring_urls)-notcontains $url){$candidate.referring_urls=@($candidate.referring_urls)+@($url)}
  $reasonProperty=$row.PSObject.Properties['reason']; $evidenceProperty=$row.PSObject.Properties['evidence']; $reason=if($reasonProperty -and $reasonProperty.Value){[string]$reasonProperty.Value}elseif($evidenceProperty){[string]$evidenceProperty.Value}else{'Reviewed in the dated 2009 GO-bond research artifact.'}
  if($status -eq 'approved for addition'){
    $candidate.title=[string]$row.title; $candidate.description=[string]$row.description; $candidate.description_word_count=[int]$row.description_word_count; $candidate.proposed_canonical_page=[string]$row.proposed_canonical_page; $candidate.size_bytes=[int64]$row.size_bytes; $candidate.checksum_sha256=[string]$row.checksum_sha256; $candidate.implementation_locations=@([string]$row.proposed_canonical_page); $candidate.validation_status='passed: authoritative City PDF reviewed and HTTP 200 verified; awaiting authorized editorial placement'; $candidate.exclusion_reason=$null
  } elseif($status -eq 'duplicate'){
    $canonicalId=[string]$row.canonical_id; if(-not $index.ContainsKey($canonicalId)){throw "Missing canonical record $canonicalId for $id"}; $canonical=$index[$canonicalId]; $canonicalUrl=if($canonical.direct_file_url){[string]$canonical.direct_file_url}else{[string]$canonical.source_url}; $candidate.cited_successors=@($candidate.cited_successors)+@($canonicalUrl)|Select-Object -Unique; $candidate.validation_status='terminal research decision: duplicate by exact, normalized-text, or contained-content comparison'; $candidate.exclusion_reason="Duplicate or contained component of canonical inventory record $canonicalId. $reason"
  } elseif($status -eq 'requires human review'){
    $candidate.validation_status='requires human review: source version or independent-record value remains unresolved'; $candidate.exclusion_reason=$null
  } else {$candidate.validation_status='terminal research decision: excluded';$candidate.exclusion_reason=$reason}
  $note="2009 GO-bond integration 2026-09-11: $reason";if(@($candidate.processing_notes)-notcontains $note){$candidate.processing_notes=@($candidate.processing_notes)+@($note)};$candidate.status=$status;$candidate.updated_at=(Get-Date).ToUniversalTime().ToString('o')
}
foreach($row in @($artifact.approved_for_addition)){Set-Decision $row 'approved for addition'};foreach($row in @($artifact.duplicate)){Set-Decision $row 'duplicate'};foreach($row in @($artifact.requires_human_review)){Set-Decision $row 'requires human review'};foreach($row in @($artifact.excluded)){Set-Decision $row 'excluded'}
if($seen.Count -ne 35){throw "Unexpected integration count: $($seen.Count)"}
# Correct three legacy canonical links after the newly verified records exist.
$repairs=@(
  @{id='src-4204206743b66c6c';canonical='src-b049c4df2812749b';reason='Re-adjudicated 2026-09-11: this public-safety authorization is not contained in the Community Facilities summary; it is the alternate delivery of the separately retained Public Safety authorization.'},
  @{id='src-5c9206c81408ce50';canonical='src-535234f371b3922c';reason='Re-adjudicated 2026-09-11: this police summary is a contained or alternate schedule of the separately retained Police summary, not a Community Facilities component.'},
  @{id='src-3ef781d4a038852a';canonical='src-d2d3b593d77a2885';reason='Re-adjudicated 2026-09-11: this byte-identical Family and Community Services schedule follows its requires-human-review counterpart; it is not fully contained in the Community Facilities summary.'}
)
foreach($repair in $repairs){$candidate=$index[$repair.id];$canonical=$index[$repair.canonical];$url=if($canonical.direct_file_url){[string]$canonical.direct_file_url}else{[string]$canonical.source_url};$candidate.cited_successors=@($candidate.cited_successors)+@($url)|Select-Object -Unique;$candidate.exclusion_reason="Duplicate or alternate delivery of canonical inventory record $($repair.canonical). $($repair.reason)";$candidate.validation_status='re-adjudicated duplicate relationship after 2009 GO-bond content comparison';$candidate.processing_notes=@($candidate.processing_notes)+@($repair.reason)|Select-Object -Unique;$candidate.updated_at=(Get-Date).ToUniversalTime().ToString('o')}
$counts=[ordered]@{};foreach($status in $inventory.allowed_statuses){$counts[$status]=@($inventory.candidates|Where-Object{[string]$_.status-eq$status}).Count};$inventory.counts=[pscustomobject]$counts;$next=@($inventory.candidates|Where-Object{$_.status -in @('pending review','approved for addition','downloaded','parsed','description drafted','placement assigned') -or ($_.status -eq 'implemented' -and $_.validation_status -ne 'passed')}|Sort-Object id|Select-Object -First 1);$inventory.next_pending_id=if($next.Count){$next[0].id}else{$null};$inventory.generated_at=(Get-Date).ToUniversalTime().ToString('o');$full=[IO.Path]::GetFullPath($InventoryPath);$temporary="$full.tmp-$PID";try{[IO.File]::WriteAllText($temporary,($inventory|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $temporary -Destination $full -Force}finally{if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary -Force}};[pscustomobject]@{integrated=$seen.Count;re_adjudicated=$repairs.Count;counts=$inventory.counts;next_pending_id=$inventory.next_pending_id}|ConvertTo-Json -Depth 5

[CmdletBinding()]
param([string]$InventoryPath='project-state/master-inventory.json')

Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 or newer is required.' }
$inventory=Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath|ConvertFrom-Json
$urls=[ordered]@{
  'src-4dd0d7313497ab4e'='https://www.cabq.gov/parksandrecreation/recreation/bike/documents/technical-appendices-of-the-albuquerque-comprehensive-on-street-bicycle-plan.pdf'
  'src-ce3c9f54fa83aba9'='https://www.cabq.gov/council/documents/councilor-district-2-documents/TrafficReportFINALJuly2014.pdf'
  'src-66d6dd3f2f7408bb'='https://www.cabq.gov/council/documents/councilor-district-2-documents/Appendix.pdf'
}
foreach($entry in $urls.GetEnumerator()){
  $candidate=@($inventory.candidates|Where-Object id -eq $entry.Key)
  if($candidate.Count-ne 1){throw "Expected one candidate for $($entry.Key)."}
  $candidate[0].direct_file_url=$entry.Value
  $candidate[0].file_type='PDF'
  $candidate[0].status='pending review'
  $candidate[0].size_bytes=$null
  $candidate[0].checksum_sha256=$null
  $candidate[0].local_path=$null
  $candidate[0].processing_notes=@($candidate[0].processing_notes|Where-Object{$_ -notmatch '^Downloaded exact size:'})+@('Resolved the Plone /view wrapper to its authoritative direct PDF URL.')|Sort-Object -Unique
  $candidate[0].updated_at=(Get-Date).ToUniversalTime().ToString('o')
}
$inventory.generated_at=(Get-Date).ToUniversalTime().ToString('o')
$json=$inventory|ConvertTo-Json -Depth 12
$full=[IO.Path]::GetFullPath($InventoryPath);$temporary="$full.tmp-$PID"
[IO.File]::WriteAllText($temporary,$json,[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $temporary -Destination $full -Force
[pscustomobject]@{Resolved=$urls.Count}|ConvertTo-Json -Compress

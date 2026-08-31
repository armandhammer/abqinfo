[CmdletBinding()]
param(
  [string]$QueuePath = 'project-state/discovery/map-dashboard-interactive-audit-queue.json',
  [string]$HttpAuditPath = 'project-state/discovery/map-dashboard-http-audit-2026-08-30.json',
  [string]$RenderedAuditPath = 'tmp/map-dashboard-rendered-audit-progress.json',
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$ReportPath = 'project-state/discovery/map-dashboard-audit-report-2026-08-30.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 or newer is required to preserve canonical JSON formatting.' }

$queue = Get-Content -Raw -Encoding UTF8 -LiteralPath $QueuePath | ConvertFrom-Json
$http = Get-Content -Raw -Encoding UTF8 -LiteralPath $HttpAuditPath | ConvertFrom-Json
$rendered = Get-Content -Raw -Encoding UTF8 -LiteralPath $RenderedAuditPath | ConvertFrom-Json
$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
if (@($queue.items).Count -ne 66 -or @($rendered.results).Count -ne 66) { throw 'Expected a complete 66-link audit.' }

$httpById = @{}; foreach ($item in $http.results) { $httpById[[string]$item.id] = $item }
$renderedById = @{}; foreach ($item in $rendered.results) { $renderedById[[string]$item.id] = $item }
$usableOverrides = @(
  'interactive-922772f1241f3027','interactive-39dc369f8428464a','interactive-98959984b4d407e3',
  'interactive-149ea9e6395a41ca','interactive-8cb092f67a03b619','interactive-f03b7b0925523dae',
  'interactive-00b4e4cf87f6ddb7','interactive-fe13d8844ba9e9b6','interactive-ddbf1a1c7f09590b'
)
$broken = @('interactive-6fbc2807b4cbf713','interactive-f6d67da41bbf96a6')

foreach ($item in $queue.items) {
  $id = [string]$item.id
  $h = $httpById[$id]
  $r = $renderedById[$id]
  $status = [string]$r.classification
  $note = 'Rendered-browser review completed against the exact implemented URL.'
  if ([string]$item.url -match '(?i)(/rest/services/|/(MapServer|FeatureServer)(/|$)|/api/reports/)') {
    $status = 'metadata only'
    $note = 'Intentional secondary data, service-directory, or report endpoint; not presented as the primary interactive map.'
  }
  if ($id -in $usableOverrides) {
    $status = 'validated usable'
    $note = if ($id -in @('interactive-149ea9e6395a41ca','interactive-8cb092f67a03b619')) {
      'Viewer renders its official government-system acknowledgement gate; the application is available after the visitor accepts that gate.'
    } else { 'Rendered application exposed usable map, dashboard, story, data, or navigation controls.' }
  }
  if ($id -in $broken) {
    $status = 'retired or broken'
    $note = if ($id -eq 'interactive-6fbc2807b4cbf713') {
      'Publicly labeled ArcGIS application redirects visitors to a City of Albuquerque ArcGIS sign-in; removed because a working current-data Map Viewer is already provided.'
    } else {
      'Standalone APS resource returns HTTP 403 and blank rendered content; removed because the full report is preserved in the archived APS action plan appendix.'
    }
  }
  $item.audit_status = $status
  $renderedTitle = if ($r.PSObject.Properties['title']) { $r.title } else { $null }
  $renderedFinalUrl = if ($r.PSObject.Properties['final_url']) { $r.final_url } else { $null }
  $renderedSignals = if ($r.PSObject.Properties['usability_signals']) { @($r.usability_signals) } else { @() }
  $item.http_validation = [pscustomobject]@{
    status = $h.http_status; final_url = $h.final_url; title = $h.response_title; error = $h.request_error
  }
  $item.rendered_validation = [pscustomobject]@{
    title = $renderedTitle; final_url = $renderedFinalUrl; classification = $status; usability_signals = $renderedSignals; observation = $note
  }
  $item.checked_at = [string]$r.checked_at
  $item.notes = @($item.notes) + @($note) | Sort-Object -Unique
}

$statuses = @('pending interactive review','validated usable','retired or broken','metadata only','requires human review')
$counts = [ordered]@{}; foreach ($status in $statuses) { $counts[$status] = @($queue.items | Where-Object audit_status -eq $status).Count }
$queue.status_definitions = $statuses
$queue.counts = [pscustomobject]$counts
$queue.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$queue.next_pending_id = $null

$bike = @($inventory.candidates | Where-Object id -eq 'src-6fbc2807b4cbf713')
if ($bike.Count -ne 1) { throw 'Expected one inventory candidate for the broken bikeways viewer.' }
$bike[0].status = 'excluded'
$bike[0].implementation_location = $null
$bike[0].implementation_locations = @()
$bike[0].validation_status = 'failed rendered-browser validation: application redirects public visitors to City of Albuquerque ArcGIS sign-in'
$bike[0].exclusion_reason = 'Unusable public link; removed in favor of the working Current Bikeways and Trails Data Map Viewer already implemented on both affected pages.'
$bike[0].processing_notes = @($bike[0].processing_notes) + @('HTTP 200 and public ArcGIS metadata were a false positive; rendered public-session behavior controls usability validation.') | Sort-Object -Unique
$bike[0].updated_at = (Get-Date).ToUniversalTime().ToString('o')

$aps = @($inventory.candidates | Where-Object id -eq 'src-f6d67da41bbf96a6')
if ($aps.Count -eq 1) {
  $aps[0].validation_status = 'duplicate confirmed; standalone APS URL returns HTTP 403/blank content, while the complete mapping-session report is preserved in the archived action plan appendix'
  $aps[0].exclusion_reason = 'Broken standalone duplicate; retained content is preserved within the archived APS Vision Zero for Youth Action Plan.'
  $aps[0].processing_notes = @($aps[0].processing_notes) + @('Removed the broken standalone implementation and folded its appendix context into the archived action-plan entry.') | Sort-Object -Unique
  $aps[0].updated_at = (Get-Date).ToUniversalTime().ToString('o')
}

$inventory.counts.validated = @($inventory.candidates | Where-Object status -eq 'validated').Count
$inventory.counts.excluded = @($inventory.candidates | Where-Object status -eq 'excluded').Count
$inventory.generated_at = (Get-Date).ToUniversalTime().ToString('o')

$report = [ordered]@{
  schema_version = 1
  completed_at = (Get-Date).ToUniversalTime().ToString('o')
  links_reviewed = 66
  counts = $counts
  content_removals = @(
    [pscustomobject]@{id='interactive-6fbc2807b4cbf713';title='Bikeways and Trails Public Map Viewer';reason='redirects public visitors to ArcGIS sign-in';replacement='Current Bikeways and Trails Data Map Viewer already implemented'},
    [pscustomobject]@{id='interactive-f6d67da41bbf96a6';title='APS Vision Zero Mapping Session Report';reason='HTTP 403 and blank rendered content';replacement='complete report preserved in archived action plan appendix'}
  )
  unresolved = @($queue.items | Where-Object audit_status -in @('pending interactive review','requires human review')).Count
}

foreach ($pair in @(@($QueuePath,$queue),@($InventoryPath,$inventory),@($ReportPath,$report))) {
  $full = [IO.Path]::GetFullPath([string]$pair[0]); $temporary = "$full.tmp-$PID"
  [IO.File]::WriteAllText($temporary,($pair[1] | ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporary -Destination $full -Force
}
$report | ConvertTo-Json -Compress -Depth 6

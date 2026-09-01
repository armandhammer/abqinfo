[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$OutputPath = 'project-state/discovery/pending-review-priority.json',
  [int]$MaxItems = 500
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Add-MatchScore {
  param(
    [string]$Text,
    [string]$Pattern,
    [int]$Points,
    [string]$Reason,
    [ref]$Score,
    [Collections.Generic.List[string]]$Reasons
  )
  if ($Text -match $Pattern) {
    $Score.Value += $Points
    $Reasons.Add($Reason)
  }
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
$ranked = foreach ($candidate in @($inventory.candidates | Where-Object status -eq 'pending review')) {
  $score = 0
  $reasons = [Collections.Generic.List[string]]::new()
  $text = @(
    $candidate.title,
    $candidate.file_type,
    $candidate.agency,
    $candidate.source_url,
    $candidate.direct_file_url,
    $candidate.parent_url,
    @($candidate.referring_urls),
    @($candidate.processing_notes)
  ) -join ' '

  $yearMatches = [regex]::Matches($text, '(?<!\d)(20(?:0[0-9]|1[0-9]|2[0-6]))(?!\d)')
  $detectedYear = if ($yearMatches.Count) {
    @($yearMatches | ForEach-Object { [int]$_.Groups[1].Value } | Sort-Object -Descending | Select-Object -First 1)[0]
  } else { $null }
  if ($detectedYear) {
    $recencyPoints = switch ($detectedYear) {
      2026 { 44 }
      2025 { 40 }
      2024 { 34 }
      2023 { 28 }
      2022 { 16 }
      2021 { 12 }
      2020 { 8 }
      default { 0 }
    }
    if ($recencyPoints) {
      $score += $recencyPoints
      $reasons.Add("recent authoritative record ($detectedYear)")
    }
  }

  if ($candidate.file_type -match '(?i)pdf|spreadsheet|excel|word|powerpoint|dataset|map|dashboard|gis') {
    $score += 18
    $reasons.Add('substantive document or data format')
  } elseif ($candidate.direct_file_url) {
    $score += 12
    $reasons.Add('direct downloadable file')
  }
  Add-MatchScore $text '(?i)\b(plan|study|assessment|analysis|report|master plan|technical standard|design standard|design guideline|specification)\b' 22 'plan, study, report, or standard terminology' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(appendix|appendices|adopted|enacted|resolution|ordinance|amendment|record of decision|environmental assessment)\b' 14 'lineage or adoption evidence' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(map|dashboard|dataset|data dictionary|open data|gis|feature service)\b' 12 'map or reusable data resource' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(corridor|intersection|roadway|street|bridge|traffic|transit|rail|bike|bicycle|pedestrian|trail|complete streets|vision zero|transportation)\b' 12 'transportation-system relevance' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(budget|capital improvement|cip|financial forecast|acfr|infrastructure capital improvement)\b' 10 'budget or capital-program relevance' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(performance measure|target assessment|annual report|bond program|active project|project dashboard|asset management|safety plan|transportation improvement program|\bTIP\b|\bSTIP\b)\b' 12 'current program, performance, or investment value' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(development|land use|zoning|sector plan|area plan|comprehensive plan|redevelopment)\b' 10 'development and land-use relevance' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(historic|historical|archive|previous|superseded|19[0-9]{2}|20[01][0-9])\b' 8 'potential historical-planning value' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(albuquerque|bernall?illo|mrmpo|mrcog|rio metro|rail runner|nmrx|nmdot)\b' 8 'Albuquerque-area institutional relevance' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(gaatc|gartc)\b' 8 'in-scope transportation advisory body' ([ref]$score) $reasons

  Add-MatchScore $text '(?i)\b(agenda|minutes|meeting notice|zoom meeting|public comment form)\b' -34 'routine meeting material; review after durable plans and studies' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(application|permit form|registration form|request form|contact us|employment|job opening|press release|news release|job aid|instruction booklet|sign posting agreement|checklist)\b' -28 'likely administrative or ephemeral material' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(construction notice|closure notice|door hanger|flyer|three[- ]week look[- ]ahead|temporary traffic control|project schedule)\b' -30 'temporary construction communication rather than durable project record' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(council meeting amendment|committee amendment|floor amendment|floor substitute|approved amendment)\b' -22 'isolated legislative amendment requires parent-record context' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(event|observance|community conversation|awareness month)\b' -24 'event material rather than durable civic information' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)(\bspanish\b|_spanish|\bespa.{0,16}ol\b|\bbilingual flyer\b)' -30 'alternate-language copy should follow review of the canonical substantive record' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(motorcycle training|aviation safety|airport security|firearms|animal welfare)\b' -22 'likely outside ABQInfo core scope' ([ref]$score) $reasons
  Add-MatchScore ([string]$candidate.title) '(?i)^(amendment \d+|report|redline draft|written comments|see appendices|presentation slides|public meeting presentation materials|read (a pdf of )?the final report\.?|download the final plan\.?|view the meeting flyer\.?)$' -30 'generic link text needs parent-context review' ([ref]$score) $reasons
  Add-MatchScore ([string]$candidate.title) '(?i)\b(scope|introduction|meeting presentation|public meeting|comments)\b.*\.pdf$' -18 'generic component file ranked below named publications' ([ref]$score) $reasons
  Add-MatchScore $text '(?i)\b(gallup|espa[nñ]ola|edgewood|madrid|truth or consequences|las cruces|farmington|roswell|alamogordo)\b' -35 'local project outside the Albuquerque metropolitan focus' ([ref]$score) $reasons
  if ($candidate.source_url -match '(?i)onbase\.cabq\.gov') {
    $score -= 30
    $reasons.Add('user-designated last-resort source')
  }

  $tier = if ($score -ge 50) { 'high' } elseif ($score -ge 25) { 'medium' } else { 'low' }
  [pscustomobject][ordered]@{
    rank_score = $score
    priority_tier = $tier
    reasons = @($reasons)
    id = $candidate.id
    title = $candidate.title
    agency = $candidate.agency
    date = $candidate.date
    detected_year = $detectedYear
    file_type = $candidate.file_type
    size_bytes = $candidate.size_bytes
    source_url = $candidate.source_url
    direct_file_url = $candidate.direct_file_url
    parent_url = $candidate.parent_url
    discovery_method = $candidate.discovery_method
    crawl_depth = $candidate.crawl_depth
    proposed_canonical_page = $candidate.proposed_canonical_page
  }
}

$ranked = @($ranked | Sort-Object @{Expression='rank_score';Descending=$true}, @{Expression='id';Descending=$false})
for ($index = 0; $index -lt $ranked.Count; $index++) {
  $ranked[$index] | Add-Member -NotePropertyName rank -NotePropertyValue ($index + 1)
}
$outputQueue = if ($MaxItems -gt 0) { @($ranked | Select-Object -First $MaxItems) } else { $ranked }
$report = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString('o')
  method = 'Deterministic metadata-only prioritization; ranking does not approve, exclude, or otherwise change candidate status.'
  pending_review_count = $ranked.Count
  queue_count = $outputQueue.Count
  counts_by_priority_tier = [ordered]@{
    high = @($ranked | Where-Object priority_tier -eq 'high').Count
    medium = @($ranked | Where-Object priority_tier -eq 'medium').Count
    low = @($ranked | Where-Object priority_tier -eq 'low').Count
  }
  queue = $outputQueue
}

$fullPath = [IO.Path]::GetFullPath($OutputPath)
$temporaryPath = "$fullPath.tmp-$PID"
[IO.File]::WriteAllText($temporaryPath, ($report | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporaryPath -Destination $fullPath -Force
$report | ConvertTo-Json -Depth 4

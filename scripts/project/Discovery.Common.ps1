Set-StrictMode -Version Latest

function Get-DefaultDiscoveryRelevantPattern {
  return '(?i)(bike|bicycl|trail|active.transport|pedestrian|complete.street|transport|traffic|road|street|corridor|mobility|facility.plan|projects?|maps?|gis|geospatial|data(?:set)?|dashboards?|apps?|applications?)'
}

function Get-BicycleHistoryRelevantPattern {
  return '(?i)(bike|bicycl|trail|active.transport|pedestrian|complete.street|facility.plan|projects?|maps?|gis|geospatial|data(?:set)?|dashboards?|apps?|applications?)'
}

function Get-DefaultRecognizedPublishingHosts {
  return @(
    'arcgis.com',
    'hub.arcgis.com',
    'storymaps.arcgis.com',
    'experience.arcgis.com'
  )
}

function Test-DiscoveryHostMatch {
  param(
    [Parameter(Mandatory)][string]$HostName,
    [Parameter(Mandatory)][AllowEmptyCollection()][string[]]$HostPatterns
  )

  foreach ($pattern in $HostPatterns) {
    if ([string]::IsNullOrWhiteSpace($pattern)) { continue }
    if ($HostName -ieq $pattern -or $HostName.EndsWith('.' + $pattern,[StringComparison]::OrdinalIgnoreCase)) {
      return $true
    }
  }
  return $false
}

function Get-DiscoveryHostClassification {
  param(
    [Parameter(Mandatory)][string]$HostName,
    [Parameter(Mandatory)][AllowEmptyCollection()][string[]]$AllowedHosts,
    [Parameter(Mandatory)][AllowEmptyCollection()][string[]]$RecognizedPublishingHosts
  )

  if (Test-DiscoveryHostMatch -HostName $HostName -HostPatterns $AllowedHosts) {
    return 'recursively allowed government host'
  }
  if (Test-DiscoveryHostMatch -HostName $HostName -HostPatterns $RecognizedPublishingHosts) {
    return 'recognized official publishing platform'
  }
  return 'external host pending provenance review'
}

function Get-DiscoverySeedAncestorUrls {
  param(
    [Parameter(Mandatory)][string]$Url,
    [string]$MinimumPathPrefix
  )

  try { $uri = [uri]$Url } catch { return @() }
  $segments = @($uri.AbsolutePath.Trim('/') -split '/' | Where-Object { $_ })
  if ($segments.Count -le 1) { return @() }

  $minimum = if ([string]::IsNullOrWhiteSpace($MinimumPathPrefix)) {
    '/' + $segments[0] + '/'
  } else {
    '/' + $MinimumPathPrefix.Trim('/') + '/'
  }

  $ancestors = [Collections.Generic.List[string]]::new()
  for ($count = $segments.Count - 1; $count -ge 1; $count--) {
    $path = '/' + (($segments[0..($count - 1)] -join '/')) + '/'
    if (-not $path.StartsWith($minimum,[StringComparison]::OrdinalIgnoreCase)) { continue }
    $ancestors.Add(('{0}://{1}{2}' -f $uri.Scheme,$uri.Authority,$path))
    if ($path -ieq $minimum) { break }
  }
  return @($ancestors)
}

function Get-DiscoveryLinkPolicy {
  param(
    [Parameter(Mandatory)][string]$Url,
    [AllowEmptyString()][string]$AnchorText = '',
    [Parameter(Mandatory)][AllowEmptyCollection()][string[]]$AllowedHosts,
    [Parameter(Mandatory)][AllowEmptyCollection()][string[]]$RecognizedPublishingHosts,
    [Parameter(Mandatory)][string]$RelevantPattern,
    [Parameter(Mandatory)][string]$DocumentPattern,
    [bool]$IsCollectionEdge = $false,
    [bool]$IsSpecial = $false,
    [bool]$IsInfrastructure = $false,
    [bool]$CaptureRelevantOutboundLinks = $true
  )

  try { $uri = [uri]$Url } catch {
    return [pscustomobject]@{capture=$false;recursive=$false;allowed_host=$false;is_document=$false;is_relevant=$false;host_classification='invalid URL'}
  }

  $allowed = Test-DiscoveryHostMatch -HostName $uri.Host -HostPatterns $AllowedHosts
  $isDocument = $Url -match $DocumentPattern
  $isRelevant = ("$AnchorText $($uri.AbsolutePath)" -match $RelevantPattern) -or $IsCollectionEdge
  $capture = $isDocument -or $isRelevant -or $IsSpecial
  if ($IsInfrastructure -and -not $isRelevant -and -not $IsSpecial) { $capture = $false }
  if (-not $allowed -and -not $CaptureRelevantOutboundLinks) { $capture = $false }

  return [pscustomobject]@{
    capture = [bool]$capture
    recursive = [bool]($capture -and $allowed -and -not $isDocument)
    allowed_host = [bool]$allowed
    is_document = [bool]$isDocument
    is_relevant = [bool]$isRelevant
    host_classification = Get-DiscoveryHostClassification -HostName $uri.Host -AllowedHosts $AllowedHosts -RecognizedPublishingHosts $RecognizedPublishingHosts
  }
}

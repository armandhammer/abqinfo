[CmdletBinding()]
param(
  [Parameter(Mandatory, ValueFromPipeline)]$Decision,
  [string]$Context = 'content publication decision'
)

begin {
  Set-StrictMode -Version Latest
  $ErrorActionPreference = 'Stop'

  function Assert-Words([string]$Value, [int]$Minimum, [string]$Label) {
    $count = if ([string]::IsNullOrWhiteSpace($Value)) { 0 } else { @($Value -split '\s+' | Where-Object { $_ }).Count }
    if ($count -lt $Minimum) { throw "$Context requires $Label of at least $Minimum words; found $count." }
  }
}

process {
  if (-not $Decision.PSObject.Properties['quality_assessment'] -or $null -eq $Decision.quality_assessment) {
    throw "$Context is missing quality_assessment. Provenance, archival integrity, and a good description do not establish standalone public value."
  }
  $quality = $Decision.quality_assessment
  $required = @('reviewed_document_content','visual_inspection_completed','standalone_public_value','information_density','series_relationship','publication_form','rationale','page_count','extracted_word_count')
  foreach ($name in $required) {
    if (-not $quality.PSObject.Properties[$name]) { throw "$Context quality_assessment is missing '$name'." }
  }
  if (-not [bool]$quality.reviewed_document_content) { throw "$Context must confirm reviewed_document_content." }
  if (-not [bool]$quality.visual_inspection_completed) { throw "$Context must confirm visual inspection; extracted text alone is insufficient." }
  if ([string]$quality.standalone_public_value -notin @('high','medium','low')) { throw "$Context has invalid standalone_public_value." }
  if ([string]$quality.information_density -notin @('substantial','limited','visual_or_tabular')) { throw "$Context has invalid information_density." }
  if ([string]$quality.series_relationship -notin @('standalone','component','serial')) { throw "$Context has invalid series_relationship." }
  if ([string]$quality.publication_form -notin @('standalone','consolidated_master','archive_only')) { throw "$Context has invalid publication_form." }
  if ([int]$quality.page_count -lt 0 -or [int]$quality.extracted_word_count -lt 0) { throw "$Context has invalid content measurements." }
  Assert-Words ([string]$quality.rationale) 20 'a substantive public-value rationale'

  if ([string]$quality.publication_form -eq 'archive_only') {
    throw "$Context is archive-only and cannot be planned as a visible site addition."
  }
  if ([string]$quality.standalone_public_value -eq 'low' -and [string]$quality.publication_form -eq 'standalone') {
    throw "$Context has low standalone public value and cannot be published as a standalone entry."
  }
  if ([string]$quality.series_relationship -ne 'standalone') {
    if (-not $quality.PSObject.Properties['aggregation_rationale']) { throw "$Context is part of a series or component set but lacks aggregation_rationale." }
    Assert-Words ([string]$quality.aggregation_rationale) 20 'an aggregation rationale'
    if ([string]$quality.publication_form -eq 'standalone') {
      if (-not $quality.PSObject.Properties['standalone_exception']) { throw "$Context is a series/component record proposed standalone but lacks standalone_exception." }
      Assert-Words ([string]$quality.standalone_exception) 20 'a standalone-series exception rationale'
    }
  }
  $thinTextRecord = ([int]$quality.page_count -gt 0 -and [int]$quality.page_count -le 2 -and [int]$quality.extracted_word_count -lt 250 -and [string]$quality.information_density -ne 'visual_or_tabular')
  if (($thinTextRecord -or [string]$quality.information_density -eq 'limited') -and [string]$quality.publication_form -eq 'standalone') {
    if (-not $quality.PSObject.Properties['limited_content_exception']) { throw "$Context is a limited-content standalone record but lacks limited_content_exception." }
    Assert-Words ([string]$quality.limited_content_exception) 20 'a limited-content exception rationale'
  }

  [pscustomobject]@{ id=[string]$Decision.id; passed=$true; publication_form=[string]$quality.publication_form }
}

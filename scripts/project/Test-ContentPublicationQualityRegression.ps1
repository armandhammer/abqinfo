[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-Rejected($Decision, [string]$Pattern) {
  try {
    & "$PSScriptRoot/Test-ContentPublicationQuality.ps1" -Decision $Decision | Out-Null
  } catch {
    if ($_.Exception.Message -notmatch $Pattern) { throw "Unexpected quality-gate error: $($_.Exception.Message)" }
    return
  }
  throw "Quality gate unexpectedly accepted '$($Decision.id)'."
}

function New-QualityDecision([string]$Id) {
  [pscustomobject]@{
    id = $Id
    quality_assessment = [pscustomobject]@{
      reviewed_document_content = $true
      visual_inspection_completed = $true
      standalone_public_value = 'high'
      information_density = 'substantial'
      series_relationship = 'standalone'
      publication_form = 'standalone'
      rationale = 'This document contains a distinct and substantial body of public information that supports a clear research and reference use without depending on related fragments.'
      page_count = 10
      extracted_word_count = 2500
    }
  }
}

Assert-Rejected ([pscustomobject]@{id='missing-assessment'}) 'missing quality_assessment'

$thin = New-QualityDecision 'thin-standalone'
$thin.quality_assessment.information_density = 'limited'
$thin.quality_assessment.page_count = 1
$thin.quality_assessment.extracted_word_count = 40
Assert-Rejected $thin 'limited_content_exception'

$serial = New-QualityDecision 'unreviewed-series'
$serial.quality_assessment.series_relationship = 'serial'
Assert-Rejected $serial 'aggregation_rationale'

$valid = New-QualityDecision 'valid-substantial-record'
$result = & "$PSScriptRoot/Test-ContentPublicationQuality.ps1" -Decision $valid
if (-not $result.passed) { throw 'Quality gate rejected a complete, substantial standalone record.' }

[pscustomobject]@{ passed=$true; rejected_missing_assessment=$true; rejected_unjustified_thin_record=$true; rejected_unreviewed_series=$true; accepted_substantial_record=$true } | ConvertTo-Json -Compress

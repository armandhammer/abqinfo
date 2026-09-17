[CmdletBinding()]
param(
  [Parameter(Mandatory)][string[]]$ResearchPaths,
  [string]$InventoryPath = 'project-state/master-inventory.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-Value($Object, [string]$Name, $Default = $null) {
  $property = $Object.PSObject.Properties[$Name]
  if ($property -and $null -ne $property.Value) { return $property.Value }
  return $Default
}

$applied = 0
$skipped = 0
foreach ($researchPath in $ResearchPaths) {
  $artifact = Get-Content -Raw -Encoding UTF8 -LiteralPath $researchPath | ConvertFrom-Json
  $batchId = [string](Get-Value $artifact 'batch_id' ([IO.Path]::GetFileNameWithoutExtension($researchPath)))
  foreach ($status in @('approved for addition','duplicate','superseded','requires human review','excluded')) {
    $propertyName = $status.Replace(' ','_')
    $property = $artifact.PSObject.Properties[$propertyName]
    if (-not $property) { continue }
    foreach ($row in @($property.Value)) {
      $id = [string]$row.id
      $inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $InventoryPath | ConvertFrom-Json
      $candidate = @($inventory.candidates | Where-Object id -eq $id)
      if ($candidate.Count -ne 1) { throw "Expected one inventory candidate for '$id'." }
      $marker = "$batchId integration 2026-09-12"
      if ([string]$candidate[0].status -ne 'pending review') {
        if ([string]$candidate[0].status -eq $status -and @($candidate[0].processing_notes) -contains $marker) { $skipped++; continue }
        throw "Unexpected candidate status for '$id': $($candidate[0].status)."
      }

      $authoritativeUrl = [string](Get-Value $row 'authoritative_url' '')
      $directUrl = $authoritativeUrl -replace '/view$',''
      $notes = @($candidate[0].processing_notes) + @($marker)
      $set = @{
        status = $status
        source_url = $authoritativeUrl
        direct_file_url = $directUrl
        size_bytes = [int64](Get-Value $row 'size_bytes' 0)
        checksum_sha256 = [string](Get-Value $row 'checksum_sha256' '')
        processing_notes = @($notes | Sort-Object -Unique)
      }

      if ($status -eq 'approved for addition') {
        $locations = @([string]$row.proposed_canonical_page)
        foreach ($cross in @(Get-Value $row 'cross_listings' @())) {
          $page = [string](Get-Value $cross 'page' '')
          if ($page) { $locations += $page }
        }
        $set.title = [string]$row.title
        $set.description = [string]$row.description
        $set.proposed_canonical_page = [string]$row.proposed_canonical_page
        $set.implementation_locations = @($locations | Sort-Object -Unique)
        $set.cross_listing_approved = @($locations | Sort-Object -Unique).Count -gt 1
        $set.validation_status = 'passed: authoritative City record reviewed and exact source bytes measured; awaiting archive-first implementation'
        $set.exclusion_reason = $null
      } elseif ($status -eq 'duplicate' -or $status -eq 'superseded') {
        $canonicalUrl = [string](Get-Value $row 'canonical_url' '')
        $basis = [string](Get-Value $row 'basis' 'Canonical relationship documented in the research artifact.')
        $set.cited_successors = @(@($candidate[0].cited_successors) + @($canonicalUrl) | Where-Object { $_ } | Sort-Object -Unique)
        $set.validation_status = "terminal research decision: $status"
        $set.exclusion_reason = $basis
      } elseif ($status -eq 'requires human review') {
        $set.validation_status = 'requires human review: unresolved enacted-version, provenance, or series-policy question documented in the research artifact'
        $set.exclusion_reason = $null
      } else {
        $set.validation_status = 'terminal research decision: excluded'
        $set.exclusion_reason = [string](Get-Value $row 'exclusion_reason' (Get-Value $row 'reason' 'Excluded by reviewed Council-record category decision.'))
      }
      & "$PSScriptRoot/Update-Candidate.ps1" -Id $id -Set $set -InventoryPath $InventoryPath | Out-Null
      $applied++
    }
  }
}

[pscustomobject]@{ applied = $applied; skipped = $skipped; artifacts = $ResearchPaths.Count } | ConvertTo-Json -Compress

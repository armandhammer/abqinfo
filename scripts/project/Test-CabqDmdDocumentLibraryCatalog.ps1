[CmdletBinding()]
param(
  [string]$CatalogPath = 'project-state/discovery/cabq-dmd-document-library-crawl.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $CatalogPath)) { throw "Catalog not found: $CatalogPath" }
$catalog = Get-Content -Raw -Encoding UTF8 -LiteralPath $CatalogPath | ConvertFrom-Json
$errors = [Collections.Generic.List[string]]::new()
$candidates = @($catalog.candidates)
$files = @($candidates | Where-Object { $_.direct_file_url })

if (@($catalog.frontier).Count) { $errors.Add("Catalog frontier is not exhausted: $(@($catalog.frontier).Count) items remain.") }
if (-not @($catalog.pages | Where-Object { ([string]$_.url).TrimEnd('/') -eq 'https://www.cabq.gov/municipaldevelopment/documents' }).Count) { $errors.Add('Root DMD document library was not recorded.') }
if (@($catalog.pages | Where-Object status -eq 'error').Count) { $errors.Add("Collection-page failures remain: $(@($catalog.pages | Where-Object status -eq 'error').Count).") }
if (@($candidates.id | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Candidate IDs are not unique.') }
if (@($candidates.url | Group-Object | Where-Object Count -gt 1).Count) { $errors.Add('Candidate URLs are not unique.') }
if (@($files | Where-Object { $null -eq $_.size_bytes -and -not $_.metadata_error }).Count) { $errors.Add('At least one file lacks both an exact size and a recorded metadata failure.') }
if (@($files | Where-Object { $_.size_bytes -lt 0 }).Count) { $errors.Add('At least one file has a negative size.') }
if (@($candidates | Where-Object { -not $_.parent_url -or -not @($_.discovery_path).Count -or -not $_.discovery_method }).Count) { $errors.Add('At least one candidate lacks provenance path metadata.') }

$result = [ordered]@{
  collection_pages = @($catalog.pages).Count
  candidates = $candidates.Count
  files = $files.Count
  exact_sizes = @($files | Where-Object { $null -ne $_.size_bytes }).Count
  metadata_failures = @($files | Where-Object { $_.metadata_error }).Count
  over_25_mib = @($files | Where-Object { $null -ne $_.size_bytes -and [int64]$_.size_bytes -gt 25MB }).Count
  over_100_mb = @($files | Where-Object { $null -ne $_.size_bytes -and [int64]$_.size_bytes -gt 100000000 }).Count
  errors = @($errors)
}
$result | ConvertTo-Json -Depth 5
if ($errors.Count) { exit 1 }

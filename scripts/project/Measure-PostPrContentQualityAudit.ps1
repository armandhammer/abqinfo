[CmdletBinding()]
param(
  [Parameter(Mandatory)][string]$AuditPath,
  [string]$AlternateRepositoryRoot = 'C:\Users\ben\Documents\ABQinfo',
  [string]$CacheDirectory = 'research/staging/quality-audit-cache'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$python = 'C:\Users\ben\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$extractor = Join-Path $PSScriptRoot 'extract_pdf.py'
$audit = Get-Content -Raw -Encoding UTF8 -LiteralPath $AuditPath | ConvertFrom-Json
New-Item -ItemType Directory -Force -Path $CacheDirectory | Out-Null

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-DocxText([string]$Path) {
  $archive = [IO.Compression.ZipFile]::OpenRead([IO.Path]::GetFullPath($Path))
  try {
    $entry = $archive.GetEntry('word/document.xml')
    if (-not $entry) { return '' }
    $reader = [IO.StreamReader]::new($entry.Open())
    try { $xml = $reader.ReadToEnd() } finally { $reader.Dispose() }
    return [Net.WebUtility]::HtmlDecode(($xml -replace '<w:tab[^>]*/>', ' ' -replace '</w:p>', "`n" -replace '<[^>]+>', ' '))
  } finally { $archive.Dispose() }
}

$measured = 0
$downloaded = 0
$errors = 0
foreach ($document in @($audit.documents)) {
  $path = ''
  if ($document.local_path -and (Test-Path -LiteralPath $document.local_path)) {
    $path = [string]$document.local_path
  } elseif ($document.local_path) {
    $alternate = Join-Path $AlternateRepositoryRoot ([string]$document.local_path)
    if (Test-Path -LiteralPath $alternate) { $path = $alternate }
  }

  $sourceForMeasurement = if ($document.r2_url) { [string]$document.r2_url } elseif ($document.direct_file_url) { [string]$document.direct_file_url } else { [string]$document.linked_url }
  if (-not $path) {
    $extension = [IO.Path]::GetExtension(([uri]$sourceForMeasurement).AbsolutePath)
    if (-not $extension) { $extension = '.' + ([string]$document.file_type).ToLowerInvariant() }
    $name = if ($document.candidate_id) { [string]$document.candidate_id } else { [guid]::NewGuid().ToString('n') }
    $path = Join-Path $CacheDirectory ($name + $extension)
    if (-not (Test-Path -LiteralPath $path)) {
      try {
        Invoke-WebRequest -UseBasicParsing -Uri $sourceForMeasurement -OutFile $path -TimeoutSec 90 -Headers @{'User-Agent'='Mozilla/5.0 ABQInfo quality audit'}
        $downloaded++
      } catch {
        $document | Add-Member -Force -NotePropertyName content_measurement -NotePropertyValue ([pscustomobject]@{status='failed';error=$_.Exception.Message;source_url=$sourceForMeasurement})
        $errors++
        continue
      }
    }
  }

  try {
    $file = Get-Item -LiteralPath $path
    $text = ''
    $pages = $null
    $xfa = $false
    $type = ([string]$document.file_type).ToUpperInvariant()
    if ($type -eq 'PDF' -or $file.Extension -eq '.pdf') {
      $parsed = (& $python $extractor $file.FullName) | ConvertFrom-Json
      $text = [string]$parsed.text
      $pages = [int]$parsed.pages
      $xfa = [bool]$parsed.xfa_placeholder
    } elseif ($type -eq 'DOCX' -or $file.Extension -eq '.docx') {
      $text = Get-DocxText $file.FullName
    }
    $words = @([regex]::Matches($text, "\b[\p{L}\p{N}][\p{L}\p{N}'’-]*\b")).Count
    $characters = (($text -replace '\s+', ' ').Trim()).Length
    $density = if ($pages -and $pages -gt 0) { [math]::Round($words / $pages, 1) } else { $null }
    $family = if ($document.title -match '(?i)Development Process Manual.*Minutes|DPM.*Minutes') {
      'dpm-executive-committee-minutes'
    } elseif ($document.title -match '(?i)General Obligation Bond|GO Bond|Bond (Project )?Scope|Bond Summary|Bond Authorization|Funding Allocation') {
      'general-obligation-bond-component'
    } elseif ($document.title -match '(?i)Annual Listing of Obligations') {
      'annual-listing-of-obligations'
    } else { $null }
    $flags = @()
    if ($pages -and $pages -le 2) { $flags += 'two-pages-or-less' }
    if ($words -lt 250) { $flags += 'under-250-extracted-words' }
    if ($pages -and $density -lt 150) { $flags += 'under-150-words-per-page' }
    if ($family) { $flags += 'series-or-component-record' }
    $document | Add-Member -Force -NotePropertyName content_measurement -NotePropertyValue ([pscustomobject]@{
      status = 'measured'
      local_path_used = $path
      source_url = $sourceForMeasurement
      size_bytes = [int64]$file.Length
      checksum_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
      pages = $pages
      extracted_words = $words
      extracted_characters = $characters
      words_per_page = $density
      xfa_placeholder = $xfa
      aggregation_family = $family
      review_flags = @($flags)
    })
    $measured++
  } catch {
    $document | Add-Member -Force -NotePropertyName content_measurement -NotePropertyValue ([pscustomobject]@{status='failed';error=$_.Exception.Message;source_url=$sourceForMeasurement;local_path_used=$path})
    $errors++
  }
}

$audit | Add-Member -Force -NotePropertyName measurement_summary -NotePropertyValue ([pscustomobject]@{
  measured_at = (Get-Date).ToUniversalTime().ToString('o')
  measured = $measured
  downloaded_for_audit = $downloaded
  failed = $errors
})
$audit | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath $AuditPath -Encoding utf8
$audit.measurement_summary | ConvertTo-Json -Compress

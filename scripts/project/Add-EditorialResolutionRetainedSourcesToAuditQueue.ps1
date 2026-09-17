[CmdletBinding()]
param([string]$QueuePath = 'project-state/discovery/retained-source-audit-queue.json')
$ErrorActionPreference = 'Stop'
$queue = Get-Content -LiteralPath $QueuePath -Raw | ConvertFrom-Json
$additions = @(
    [pscustomobject][ordered]@{
        candidate_id = 'src-6735737588d294e0'; source_url = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc/epchearings.pdf/view'; title = '2003 Environmental Planning Commission Recommendation and Notice of Decision - Mayor Proposed 2003-2012 Decade Plan'; agency = 'City of Albuquerque'; canonical_page = 'content/city-data/capital-spending.md'; audit_status = 'pending descendant crawl'; crawl_output = $null; discovered_documents = 0; archived_documents = 0; processing_notes = @('Added after the editorial resolution changed this retained official source to validated. No descendant crawl was repeated in this campaign.'); created_at = (Get-Date).ToUniversalTime().ToString('o'); updated_at = (Get-Date).ToUniversalTime().ToString('o')
    },
    [pscustomobject][ordered]@{
        candidate_id = 'src-3c9907796a0cfaf3'; source_url = 'https://www.cabq.gov/municipaldevelopment/documents/cip-documents/2003-bond-doc/WaterMasterPlanInfra.pdf/view'; title = 'Water Master Plan Infrastructure Zone (WIZ) Map - Appendix page B-6; parent document not located'; agency = 'City of Albuquerque'; canonical_page = 'content/city-data/capital-spending.md'; audit_status = 'pending descendant crawl'; crawl_output = $null; discovered_documents = 0; archived_documents = 0; processing_notes = @('Added after the editorial resolution changed this retained official source to validated. No descendant crawl was repeated in this campaign.'); created_at = (Get-Date).ToUniversalTime().ToString('o'); updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }
)
foreach ($addition in $additions) { if (-not @($queue.records | Where-Object candidate_id -eq $addition.candidate_id).Count) { $queue.records += $addition } }
$counts = [ordered]@{}; foreach ($status in $queue.allowed_statuses) { $counts[$status] = @($queue.records | Where-Object audit_status -eq $status).Count }
$queue.counts = [pscustomobject]$counts
$queue.generated_at = (Get-Date).ToUniversalTime().ToString('o')
$queue.next_pending_source_url = @($queue.records | Where-Object audit_status -eq 'pending descendant crawl' | Sort-Object source_url | Select-Object -First 1 -ExpandProperty source_url)
$json = $queue | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($QueuePath), "$json`r`n", [System.Text.UTF8Encoding]::new($false))
Write-Output "Retained-source audit queue now covers the two newly eligible editorial sources."

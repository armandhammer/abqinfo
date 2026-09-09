[CmdletBinding()]
param(
  [string]$InventoryPath = 'project-state/master-inventory.json',
  [string]$DownloadDirectory = 'research/staging/legistar-transportation-history'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# This deliberately begins with named plans, studies, reports, and paired report
# appendices from the official historical Legistar queue.  Legislative enactments
# remain provenance wrappers until the substantive source has been compared.
$records = @(
  @{ title = 'Rio Grande Complete Streets Plan'; date = '2018-09'; type = 'PDF'; matter = 'R-18-52'; attachment = 'R-52 (Exhibit A - Plan)'; url = 'https://legistar.granicus.com/cabq/attachments/1df427b1-4fd4-48db-b387-690542765915.pdf' },
  @{ title = 'Double Eagle II Aerospace Technology Park Transportation Distribution Status Report'; date = '2008-02'; type = 'DOC'; matter = 'EC-07-1'; attachment = 'EC-1.doc'; url = 'https://legistar.granicus.com/cabq/attachments/6594.doc' },
  @{ title = 'Double Eagle II Aerospace Technology Park Transportation Distribution Status Report — Attachment'; date = '2008-02'; type = 'PDF'; matter = 'EC-07-1'; attachment = 'EC-1att.pdf'; url = 'https://legistar.granicus.com/cabq/attachments/6595.pdf' },
  @{ title = 'Rio Grande and Candelaria Crash Rate Report'; date = '2013-12'; type = 'PDF'; matter = 'R-13-163'; attachment = 'R-163 DOT Crash Rate Report'; url = 'https://legistar.granicus.com/cabq/attachments/c7830e07-afd0-44e1-bc9a-c57951f3b699.pdf' },
  @{ title = 'Rio Grande and Candelaria Severity Index Report'; date = '2013-12'; type = 'PDF'; matter = 'R-13-163'; attachment = 'R-163 DOT Severity Index Report'; url = 'https://legistar.granicus.com/cabq/attachments/cea43a7a-714f-40d2-a1f4-3413e541d0dc.pdf' },
  @{ title = 'Albuquerque Rapid Transit Amended Design and Finance Plan Response'; date = '2016-11'; type = 'PDF'; matter = 'EC-16-226'; attachment = 'EC-226.pdf'; url = 'https://legistar.granicus.com/cabq/attachments/8d6914d5-f4aa-4941-90e4-1ea71bbb21b6.pdf' },
  @{ title = 'Albuquerque Rapid Transit Amended Design and Finance Plan Response — Maps and Figures'; date = '2016-11'; type = 'PDF'; matter = 'EC-16-226'; attachment = 'EC-226 Maps Figures 1-16.pdf'; url = 'https://legistar.granicus.com/cabq/attachments/e416cd78-331e-4f3e-8c76-0b372a35cd8d.pdf' },
  @{ title = 'Cutler Avenue Report'; date = '2018-09'; type = 'PDF'; matter = 'R-18-51'; attachment = 'R-51 (Attachment 1 - Cutler Avenue Report).pdf'; url = 'https://legistar.granicus.com/cabq/attachments/23b5f8b3-03c2-4e7d-9039-8635bb52a152.pdf' },
  @{ title = 'Route 66 Action Plan'; date = '2014-11'; type = 'PDF'; matter = 'R-14-115'; attachment = 'R-115 RT66 Action Plan Final'; url = 'https://legistar.granicus.com/cabq/attachments/7721c342-134b-428f-b6a5-1fec9471340b.pdf' },
  @{ title = 'Albuquerque Rapid Transit Small Starts Grant Attachment'; date = '2016-03'; type = 'PDF'; matter = 'R-16-24'; attachment = 'R-24 Attachment A'; url = 'https://legistar.granicus.com/cabq/attachments/4625fb48-aa7a-43e3-a7eb-fb815612dd12.pdf' },
  @{ title = 'Downtown Neighborhood Area Traffic Study'; date = '2014-08'; type = 'PDF'; matter = 'R-14-94'; attachment = 'R-94 Exhibit A'; url = 'https://legistar.granicus.com/cabq/attachments/678f1a92-1bb2-41c8-9014-05a802ddbe64.pdf' },
  @{ title = 'Pavement Rating Report for Street Maintenance Programs'; date = '2012-10'; type = 'PDF'; matter = 'EC-12-169'; attachment = 'EC-169.pdf'; url = 'https://legistar.granicus.com/cabq/attachments/13218.pdf' },
  @{ title = 'Park and Ride Transit Center Strategic Plan'; date = '2009-02'; type = 'DOC'; matter = 'EC-08-324'; attachment = 'EC-324.doc'; url = 'https://legistar.granicus.com/cabq/attachments/8164.doc' },
  @{ title = '2006–2011 Short Range Transit Plan Status Report'; date = '2009-02'; type = 'DOC'; matter = 'EC-08-320'; attachment = 'EC-320.doc'; url = 'https://legistar.granicus.com/cabq/attachments/8144.doc' },
  @{ title = 'Transit Department 10-Year Capital Needs Assessment'; date = '2009-02'; type = 'DOC'; matter = 'EC-08-317'; attachment = 'EC-317.doc'; url = 'https://legistar.granicus.com/cabq/attachments/8121.doc' },
  @{ title = 'Transit Department 10-Year Capital Needs Assessment — Status Report'; date = '2008-07'; type = 'DOC'; matter = 'EC-08-317'; attachment = 'EC-317att.doc'; url = 'https://legistar.granicus.com/cabq/attachments/8122.doc' },
  @{ title = 'Transit Department 10-Year Capital Needs Assessment — Supporting Material'; date = '2008-07'; type = 'DOC'; matter = 'EC-08-317'; attachment = 'EC-317att2.doc'; url = 'https://legistar.granicus.com/cabq/attachments/8123.doc' },
  @{ title = 'Rapid Transit Project Draft Environmental Impact Statement and Financial Plan Status Report'; date = '2007-12'; type = 'DOC'; matter = 'EC-07-573'; attachment = 'EC-573.doc'; url = 'https://legistar.granicus.com/cabq/attachments/6266.doc' },
  @{ title = 'Rapid Transit Project Draft Environmental Impact Statement and Financial Plan — Closeout Attachment'; date = '2007-04'; type = 'DOC'; matter = 'EC-07-573'; attachment = 'EC-573att.doc'; url = 'https://legistar.granicus.com/cabq/attachments/6267.doc' },
  @{ title = 'Short Range Transit Plan'; date = '2006-08'; type = 'DOC'; matter = 'EC-06-157'; attachment = 'EC-157.doc'; url = 'https://legistar.granicus.com/cabq/attachments/4220.doc' },
  @{ title = 'Short Range Transit Plan — Five-Year Recommendations'; date = '2006-04'; type = 'DOC'; matter = 'EC-06-157'; attachment = 'EC-157att.doc'; url = 'https://legistar.granicus.com/cabq/attachments/4221.doc' },
  @{ title = '2006–2011 Short Range Transit Plan — Status Report'; date = '2008-07'; type = 'DOC'; matter = 'EC-08-320'; attachment = 'EC-320att.doc'; url = 'https://legistar.granicus.com/cabq/attachments/8145.doc' },
  @{ title = 'Park and Ride Transit Center Strategic Plan — Status Report'; date = '2008-07'; type = 'DOC'; matter = 'EC-08-324'; attachment = 'EC-324att.doc'; url = 'https://legistar.granicus.com/cabq/attachments/8165.doc' },
  @{ title = 'Park and Ride Transit Center Strategic Plan — Supporting Material'; date = '2008-07'; type = 'DOC'; matter = 'EC-08-324'; attachment = 'EC-324att2.doc'; url = 'https://legistar.granicus.com/cabq/attachments/8166.doc' },
  @{ title = 'Double Eagle II Airport Master Plan'; date = '2019-09'; type = 'PDF'; matter = 'R-19-169'; attachment = 'R-169 Double Eagle II Airport Master Plan'; url = 'https://legistar.granicus.com/cabq/attachments/ab7f1a8b-2258-496c-ad4e-c6343ace4691.pdf' }
)

$results = foreach ($record in $records) {
  $matterUrl = "https://cabq.legistar.com/LegislationDetail.aspx?ID=$($record.matter)&Search=$($record.matter)"
  $candidate = & "$PSScriptRoot/Add-InventoryCandidate.ps1" `
    -SourceUrl $record.url `
    -DirectFileUrl $record.url `
    -Agency 'City of Albuquerque' `
    -Title $record.title `
    -Date $record.date `
    -FileType $record.type `
    -ParentUrl $matterUrl `
    -DiscoveryMethod "official CABQ Legistar historical transportation queue; $($record.matter), $($record.attachment)" `
    -CrawlDepth 2 `
    -InventoryPath $InventoryPath | ConvertFrom-Json
  if ($candidate.status -in @('pending review', 'downloading')) {
    $candidate = & "$PSScriptRoot/Download-Candidate.ps1" -Id $candidate.id -InventoryPath $InventoryPath -DownloadDirectory $DownloadDirectory | ConvertFrom-Json
  }
  [pscustomobject]@{ id = $candidate.id; status = $candidate.status; matter = $record.matter; title = $candidate.title; file_type = $candidate.file_type; size_bytes = $candidate.size_bytes; checksum_sha256 = $candidate.checksum_sha256; local_path = $candidate.local_path }
}
$results | ConvertTo-Json -Depth 4

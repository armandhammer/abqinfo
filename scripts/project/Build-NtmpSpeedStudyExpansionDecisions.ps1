[CmdletBinding()]
param([string]$OutputPath = 'project-state/discovery/ntmp-speed-study-expansion-23-decisions.json')

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$page = 'content/transportation/roadway-projects/speed-management.md'
$sourcePage = 'https://www.cabq.gov/neighborhood-traffic-management-program/studies'
$decisions = [Collections.Generic.List[object]]::new()

function Add-Decision([string]$Id, [string]$Title, [string]$Date, [string]$Key, [string]$Description) {
  $decisions.Add([pscustomobject][ordered]@{
    id = $Id
    title = $Title
    date = $Date
    r2_key = "transportation/roadway-projects/speed-management/$Key"
    canonical_page = $page
    source_page = $sourcePage
    description = $Description
    processing_notes = @(
      'Original authoritative City PDF preserved without modification.',
      'Description reviewed against extracted report findings and representative visual inspection.'
    )
  })
}

Add-Decision 'src-750a6401a2da53e9' '86th Street Speed Study' '2017-06' 'cabq-86th-street-speed-study-2017.pdf' 'Evaluates speeds, traffic volumes, and crash history on 86th Street and finds only one of four NTMP warrants, below the threshold for traffic-calming measures.'
Add-Decision 'src-83ea63e996d14a7a' '8th Street Speed Study — Coal Avenue to Atlantic Avenue' '2019-01' 'cabq-8th-street-coal-atlantic-speed-study-2019.pdf' 'Analyzes crashes, volumes, and speeds on 8th Street between Coal and Atlantic and finds two of four NTMP criteria, meeting the minimum threshold for traffic calming.'
Add-Decision 'src-e39307b93c5db8b6' 'Alvarado Drive Speed Study' '2021-08-16' 'cabq-alvarado-drive-speed-study-2021.pdf' 'Evaluates Alvarado Drive between Copper Avenue and Lomas Boulevard and finds two NTMP threshold sets were met, qualifying the corridor for traffic-calming measures.'
Add-Decision 'src-0c6fc2cc4030096d' 'Amherst Drive Speed Study' '2018-05' 'cabq-amherst-drive-speed-study-2018.pdf' 'Reviews speeds, volumes, and crashes on Amherst Drive, finding that none of the required NTMP criteria were met and traffic-calming improvements were not warranted.'
Add-Decision 'src-5247e676f00790a1' 'Andrew Drive Speed Study' '2019-01' 'cabq-andrew-drive-speed-study-2019.pdf' 'Studies Andrew Drive from Montgomery Boulevard to Dodd Place and concludes that none of the four NTMP criteria were met, below the traffic-calming threshold.'
Add-Decision 'src-28e73e3d95146a38' 'Arizona Street Speed Study' '2019-06' 'cabq-arizona-street-speed-study-2019.pdf' 'Uses updated 2019 traffic counts with crash, volume, and speed analysis for Arizona Street from Kathryn to Ross, finding no NTMP traffic-calming criteria were met.'
Add-Decision 'src-f42d3a89ef99b31e' 'Arroyo de Vista Speed Study' '2021-08-16' 'cabq-arroyo-de-vista-speed-study-2021.pdf' 'Evaluates Arroyo de Vista between Larchmont Drive and Calle de Tierra and finds none of nine NTMP threshold sets, so the street did not qualify for traffic calming.'
Add-Decision 'src-f89c6222ec8cf941' 'Avital Drive Speed Study' '2018-03' 'cabq-avital-drive-speed-study-2018.pdf' 'Documents speed, volume, and crash conditions on Avital Drive, finding no applicable NTMP warrants and concluding that traffic-calming measures were not justified.'
Add-Decision 'src-0241f72df40f8a47' 'Aztec Road Speed Study' '2018-05' 'cabq-aztec-road-speed-study-2018.pdf' 'Measures speed and traffic conditions on Aztec Road, documenting substantial speeding but concluding that the corridor did not meet the minimum NTMP traffic-calming threshold.'
Add-Decision 'src-8176ce3888683c9a' 'Azuelo Avenue Speed Study' '2018-05' 'cabq-azuelo-avenue-speed-study-2018.pdf' 'Evaluates speeds, volumes, and crashes on Azuelo Avenue and finds the street did not meet the minimum two-warrant threshold for traffic-calming improvements.'
Add-Decision 'src-7cb657e190db5117' 'Baldwin Avenue West Speed Study' '2016-09' 'cabq-baldwin-avenue-west-speed-study-2016.pdf' 'Examines Baldwin Avenue from Eubank Boulevard to Morris Street using speed surveys, traffic volumes, and crash history, finding no NTMP criteria for traffic calming were met.'
Add-Decision 'src-bb4c7549e1fc74f6' 'Baldwin Avenue East Speed Study' '2016-11' 'cabq-baldwin-avenue-east-speed-study-2016.pdf' 'Analyzes Baldwin Avenue from Morris Street to Indian School Road by segment, documenting traffic, crashes, and speeds while retaining the existing 25-mph local-street limit.'
Add-Decision 'src-1a225b1370d7b805' 'Bandelier Drive Speed Study' '2018-03' 'cabq-bandelier-drive-speed-study-2018.pdf' 'Finds speeding on several Bandelier Drive segments but only one NTMP warrant overall, recommending additional law-enforcement monitoring rather than qualifying the corridor for traffic calming.'
Add-Decision 'src-c0c3788492fdd727' 'Barnhart Street Speed Study' '2017-09' 'cabq-barnhart-street-speed-study-2017.pdf' 'Evaluates five Barnhart Street count locations and finds only the speeding warrant was met, below the two-warrant threshold required for NTMP traffic-calming improvements.'
Add-Decision 'src-1e839217f398a255' 'Bellehaven Avenue Speed Study' '2015-02' 'cabq-bellehaven-avenue-speed-study-2015.pdf' 'Reviews speed, traffic, and crash conditions on Bellehaven Avenue from Wyoming Boulevard to Indian School Road and finds no NTMP criteria warranting speed humps.'
Add-Decision 'src-699f75d877610795' 'Blue Ribbon Road Speed Study' '2021-08-16' 'cabq-blue-ribbon-road-speed-study-2021.pdf' 'Evaluates Blue Ribbon Road between Juan Tabo Drive and Vernon Drive and finds none of nine NTMP threshold sets, so the street did not qualify for traffic calming.'
Add-Decision 'src-1c4d6fe4276ea1e8' 'Brandywine Road Speed Study' '2016-05' 'cabq-brandywine-road-speed-study-2016.pdf' 'Reviews Brandywine Road traffic, speed, and crash data and finds no NTMP warrants, including only 14 percent of measured traffic exceeding 25 mph.'
Add-Decision 'src-ad34fdef8b9e50b6' 'Bursera Drive Speed Study' '2018-09' 'cabq-bursera-drive-speed-study-2018.pdf' 'Documents traffic and speeds on Bursera Drive, finding one speeding warrant at one count location but not the two criteria required for NTMP improvements.'
Add-Decision 'src-cc0cd09fe02ab65c' 'Calle de Tierra and Della Longa Lane Speed Study' '2019-12' 'cabq-calle-de-tierra-della-longa-speed-study-2019.pdf' 'Studies Calle de Tierra and Della Longa Lane from Manitoba Drive to Calle Alta, finding none of the four NTMP criteria for traffic-calming treatment.'
Add-Decision 'src-df6c2c0c74519f2e' 'Carolina Street Speed Study' '2018-03' 'cabq-carolina-street-speed-study-2018.pdf' 'Evaluates traffic, speeds, and crashes on Carolina Street, finding that none of the NTMP warrants were met despite 35 percent of measured traffic exceeding 25 mph.'
Add-Decision 'src-0b07feb02d238677' 'Casa Grande Avenue Speed Study' '2018-10' 'cabq-casa-grande-avenue-speed-study-2018.pdf' 'Analyzes Casa Grande Avenue from Sierra Grande Avenue to Upland Drive and finds none of the four NTMP criteria, below the minimum traffic-calming threshold.'
Add-Decision 'src-83ec976c2c12c38c' 'Conejo Road Speed Study' '2017-05' 'cabq-conejo-road-speed-study-2017.pdf' 'Documents speed, volume, and crash conditions on Conejo Road and concludes that the street did not meet the NTMP criteria required to warrant traffic calming.'
Add-Decision 'src-da7a537cb1071c9c' 'Conestoga Street Area Speed Study' '2021-07-13' 'cabq-conestoga-street-area-speed-study-2021.pdf' 'Evaluates Conestoga Drive, Sooner Trail, Kettle Road, and Homestead Circle, finding only Homestead Circle met the NTMP threshold and qualified for traffic-calming measures.'
Add-Decision 'src-a8d38587a1d1bf7c' 'Del Monte Trail Speed Study' '2018-03' 'cabq-del-monte-trail-speed-study-2018.pdf' 'Documents speeding on Del Monte Trail at one count location but finds only one of four NTMP warrants, below the minimum traffic-calming threshold.'
Add-Decision 'src-d5cf0b47387bea30' 'Dolores Drive Speed Study' '2018-03' 'cabq-dolores-drive-speed-study-2018.pdf' 'Analyzes traffic, speeds, and crashes on Dolores Drive and finds no NTMP warrants, with the 85th-percentile speed remaining below the qualifying threshold.'
Add-Decision 'src-892e86b93ed5c826' 'Dover Street Speed Study' '2019-01' 'cabq-dover-street-speed-study-2019.pdf' 'Studies Dover Street from McMahon Boulevard to Braniff Avenue and finds one of four NTMP criteria, insufficient to meet the minimum traffic-calming threshold.'
Add-Decision 'src-a3f16af6f3ddc648' 'Eastern Avenue Speed Study' '2019-01' 'cabq-eastern-avenue-speed-study-2019.pdf' 'Analyzes Eastern Avenue from Wellesley Drive to Carlisle Boulevard and finds none of the four NTMP criteria, below the threshold for traffic-calming treatment.'
Add-Decision 'src-a9c8f8d60c79e6df' 'Eastridge Drive Speed Study' '2021-08-16' 'cabq-eastridge-drive-speed-study-2021.pdf' 'Evaluates Eastridge Drive between Chelwood Park Boulevard and Haines Avenue and finds none of nine NTMP threshold sets, so the street did not qualify for traffic calming.'
Add-Decision 'src-82348e1af6d22d94' 'El Patron Road Speed Study' '2021-08-16' 'cabq-el-patron-road-speed-study-2021.pdf' 'Evaluates El Patron Road between High Range Road and Del Rey Road and finds none of nine NTMP threshold sets, so the street did not qualify for traffic calming.'

$wordErrors = @($decisions | ForEach-Object {
  $words = @($_.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { "$($_.id): $words words" }
})
if ($wordErrors.Count) { throw "Description word-count errors: $($wordErrors -join '; ')" }

[ordered]@{
  schema_version = 1
  batch_id = 'expansion-23-ntmp-speed-study-archive'
  decisions = @($decisions)
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{ Decisions = $decisions.Count; OutputPath = $OutputPath } | ConvertTo-Json -Compress

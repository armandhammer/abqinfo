[CmdletBinding()]
param([string]$OutputPath = 'project-state/discovery/ntmp-speed-study-expansion-25-decisions.json')

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

Add-Decision 'src-4055f2c2c2855c3f' '17th Street Speed Study' '2021-03' 'cabq-17th-street-speed-study-2021.pdf' 'Studies 17th Street from Old Town Road to Lomas Boulevard and finds none of the nine NTMP thresholds, below the minimum criterion for traffic calming.'
Add-Decision 'src-68d0f4c2eab1abcc' '61st Street Speed Study' '2021-03' 'cabq-61st-street-speed-study-2021.pdf' 'Studies 61st Street from Avalon Road to Bluewater Road and finds none of the nine NTMP thresholds, below the minimum criterion for traffic calming.'
Add-Decision 'src-3ee27f72a343adbd' '7th Street Speed Study' '2021-03' 'cabq-7th-street-speed-study-2021.pdf' 'Studies 7th Street from Coal Avenue to Stover Avenue and finds none of the nine NTMP thresholds, below the minimum criterion for traffic calming.'
Add-Decision 'src-32fdee2d2bef98ee' '8th Street Speed Study' '2017-05' 'cabq-8th-street-speed-study-2017.pdf' 'Reviews traffic volumes, crashes, and speeds on 8th Street and finds that none of the applicable NTMP criteria were met to warrant traffic calming.'
Add-Decision 'src-5f1d0094a0da7f1c' '9th Street Speed Study' '2018-10' 'cabq-9th-street-speed-study-2018.pdf' 'Studies 9th Street from Montaño Road to Douglas MacArthur Road and finds none of the four NTMP criteria, below the traffic-calming threshold.'
Add-Decision 'src-60cacc1053d6ff09' 'Baja Drive Speed Study' '2021-03' 'cabq-baja-drive-speed-study-2021.pdf' 'Studies Baja Drive from Juan Tabo Boulevard to Cairo Drive and finds none of the nine NTMP thresholds, below the minimum criterion for traffic calming.'
Add-Decision 'src-481c7da828be0275' 'Constitution Avenue Speed Study' '2021-03' 'cabq-constitution-avenue-speed-study-2021.pdf' 'Studies Constitution Avenue from Morris Street to Juan Tabo Boulevard and finds five of nine NTMP thresholds, meeting the minimum traffic-calming criterion.'
Add-Decision 'src-09a7c06f0ee97da0' 'Desert Springs Drive Speed Study' '2021-03' 'cabq-desert-springs-drive-speed-study-2021.pdf' 'Studies Desert Springs Drive from Spring Flower Road to Desert Canyon Place and finds four of nine NTMP thresholds, meeting the minimum traffic-calming criterion.'
Add-Decision 'src-d17338f308015c89' 'Eastern Avenue and Cardenas Drive Traffic Study' '2017-12' 'cabq-eastern-avenue-cardenas-drive-traffic-study-2017.pdf' 'Evaluates stop-control, signal, crash, and speed warrants at Eastern Avenue and Cardenas Drive, finding no warrant for changes while recommending periodic enforcement if concerns continue.'
Add-Decision 'src-286f138cacc5ea41' 'Española Street Speed Study' '2017-06' 'cabq-espanola-street-speed-study-2017.pdf' 'Reviews traffic volumes, crashes, and speeds on Española Street and finds that the roadway did not meet the minimum NTMP traffic-calming threshold.'
Add-Decision 'src-84df2cc205ac4eed' 'Field Drive Speed Study' '2021-03' 'cabq-field-drive-speed-study-2021.pdf' 'Studies Field Drive from Indian School Road to Snow Heights Boulevard and finds none of the nine NTMP thresholds, below the minimum traffic-calming criterion.'
Add-Decision 'src-f70f9e2027603c7b' 'Freedom Way Speed Study' '2021-03' 'cabq-freedom-way-speed-study-2021.pdf' 'Studies Freedom Way from Ventura Street to Don Diego Street and finds one of nine NTMP thresholds, meeting the stated minimum criterion for traffic calming.'
Add-Decision 'src-6ec094424a36ea7e' 'Iliff Road Speed Study' '2021-03' 'cabq-iliff-road-speed-study-2021.pdf' 'Studies Iliff Road from Coors Boulevard to Atrisco Drive and finds five of nine NTMP thresholds, meeting the minimum traffic-calming criterion.'
Add-Decision 'src-fd7fb9dd8737ab5d' 'Kimmick Drive Speed and Volume Study' '2021-11-23' 'cabq-kimmick-drive-speed-volume-study-2021.pdf' 'Documents directional traffic volumes and speed distributions on Kimmick Drive between Paseo del Norte Boulevard and Urraca Street, including two count locations and posted-speed comparisons.'
Add-Decision 'src-dc0c2ea9ec93cd61' 'La Corrida Road Speed Study' '2016-05' 'cabq-la-corrida-road-speed-study-2016.pdf' 'Evaluates La Corrida Road from Comanche Road to San Pedro Drive, finding substantial speeding and cut-through traffic but only one of two required NTMP criteria.'
Add-Decision 'src-46babb6f9318d547' 'Milky Way Street Speed Study' '2021-03' 'cabq-milky-way-street-speed-study-2021.pdf' 'Studies Milky Way Street from Black Arroyo Boulevard to McMahon Boulevard and finds none of the nine NTMP thresholds, below the minimum traffic-calming criterion.'
Add-Decision 'src-355de0c6e2a75205' 'Morningside Drive Speed Study' '2021-03' 'cabq-morningside-drive-speed-study-2021.pdf' 'Studies Morningside Drive from Coal Avenue to Pershing Avenue and finds none of the nine NTMP thresholds, below the minimum criterion for traffic calming.'
Add-Decision 'src-4631527cd57ef0f8' 'Ruidoso Road Speed Study' '2021-03' 'cabq-ruidoso-road-speed-study-2021.pdf' 'Studies Ruidoso Road from Curry Avenue to Mosquero Avenue and finds none of the nine NTMP thresholds, below the minimum criterion for traffic calming.'
Add-Decision 'src-40d70969977fa87d' 'San Francisco Road Speed Study' '2020-04' 'cabq-san-francisco-road-speed-study-2020.pdf' 'Studies San Francisco Road from San Pedro Drive to Louisiana Boulevard and finds one of four NTMP criteria, below the minimum traffic-calming threshold.'
Add-Decision 'src-8d76bc3e666b3ea1' 'Sicily Road Speed Study' '2017-05' 'cabq-sicily-road-speed-study-2017.pdf' 'Reviews speed, traffic-volume, and roadway conditions on Sicily Road and finds the street did not meet the two-warrant minimum required for NTMP traffic calming.'
Add-Decision 'src-e76196d4a7b799ac' 'Sierra Grande Avenue Speed Study' '2021-03' 'cabq-sierra-grande-avenue-speed-study-2021.pdf' 'Studies Sierra Grande Avenue from Loyola Avenue to Loyola Place and finds one of nine NTMP thresholds, meeting the stated minimum criterion for traffic calming.'
Add-Decision 'src-b863acfbb1cdeac7' 'Spanish Sun Avenue Speed Study' '2021-08-16' 'cabq-spanish-sun-avenue-speed-study-2021.pdf' 'Evaluates Spanish Sun Avenue between Monroe Street and Red Sun Drive and finds the segment did not qualify for traffic-calming measures under NTMP guidance.'
Add-Decision 'src-d08d3db0111ffdd0' 'Existing Speed Hump and Radar Sign Study' '2018-10' 'cabq-existing-speed-hump-radar-sign-study-2018.pdf' 'Compares before-and-after traffic speeds at numerous Albuquerque speed humps and radar-feedback signs, preserving location-specific evidence about how the installed treatments performed.'
Add-Decision 'src-4947ff6d7d8d78f7' 'Storrie Place Speed Study' '2021-03' 'cabq-storrie-place-speed-study-2021.pdf' 'Studies Storrie Place from Palomas Park Avenue to La Mariposa Place and finds none of the nine NTMP thresholds, below the minimum traffic-calming criterion.'
Add-Decision 'src-9c795e2736c419a6' 'Sunridge Avenue Speed Study' '2021-03' 'cabq-sunridge-avenue-speed-study-2021.pdf' 'Studies Sunridge Avenue from Sunburst Road to 90th Street and finds none of the nine NTMP thresholds, below the minimum criterion for traffic calming.'
Add-Decision 'src-8dcb29a979cb5bee' 'Tony Sanchez Drive Speed Study' '2020-03' 'cabq-tony-sanchez-drive-speed-study-2020.pdf' 'Studies Tony Sanchez Drive from Herman Roser Avenue to Jewel Cave Road and finds one of four NTMP criteria, below the minimum traffic-calming threshold.'
Add-Decision 'src-fe416bd8dfa0b1d3' 'Trail Ridge Road Speed Study' '2019-01' 'cabq-trail-ridge-road-speed-study-2019.pdf' 'Studies Trail Ridge Road from American Heritage Drive to Knight Road and finds one of four NTMP criteria, below the minimum traffic-calming threshold.'
Add-Decision 'src-a06ed44222a26f73' 'Truman Street Speed Study' '2021-03' 'cabq-truman-street-speed-study-2021.pdf' 'Studies Truman Street from Headingly Avenue to Candelaria Road and finds one of nine NTMP thresholds, meeting the stated minimum criterion for traffic calming under current program guidance.'
Add-Decision 'src-eaa0507db69a01f2' 'Trumbull Avenue Speed Study' '2017-09' 'cabq-trumbull-avenue-speed-study-2017.pdf' 'Reviews traffic volumes, crashes, and speeds on Trumbull Avenue and finds that none of the applicable NTMP criteria were met to warrant traffic calming.'
Add-Decision 'src-a30f9dff9a55b65b' 'Ventana West Parkway and Paseo del Norte Study' '2018-12' 'cabq-ventana-west-paseo-del-norte-study-2018.pdf' 'Finds a multi-way stop warranted at Ventana West Parkway and Paseo del Norte, while concluding that traffic calming on Ventana West Parkway was not warranted.'
Add-Decision 'src-1c9b4e21de9e0c92' 'Ventura Street Speed Study' '2017-05' 'cabq-ventura-street-speed-study-2017.pdf' 'Reviews traffic volumes, crashes, and speeds on Ventura Street and concludes that the roadway did not meet the applicable NTMP criteria for traffic calming.'
Add-Decision 'src-5a721d4def74af93' 'Vivian Drive Speed Study' '2021-03' 'cabq-vivian-drive-speed-study-2021.pdf' 'Studies Vivian Drive from Glendora Drive to Truchas Drive and finds one of nine NTMP thresholds, meeting the stated minimum criterion for traffic calming.'
Add-Decision 'src-eefaabfa61697495' 'Woodland and Phoenix Avenues Speed Study' '2018-10' 'cabq-woodland-phoenix-avenues-speed-study-2018.pdf' 'Evaluates Woodland and Phoenix avenues from Menaul Boulevard to Moon Street, finding that neither street met the minimum NTMP traffic-calming criterion.'
Add-Decision 'src-f01f6f758696cf79' 'Yucca Drive Speed Study' '2019-05' 'cabq-yucca-drive-speed-study-2019.pdf' 'Studies Yucca Drive from Cloudcroft Road to Central Avenue and finds two of four NTMP criteria, meeting the minimum traffic-calming threshold.'

$duplicateIds = @(
  'src-4055f2c2c2855c3f','src-68d0f4c2eab1abcc','src-3ee27f72a343adbd','src-60cacc1053d6ff09',
  'src-481c7da828be0275','src-09a7c06f0ee97da0','src-84df2cc205ac4eed','src-f70f9e2027603c7b',
  'src-6ec094424a36ea7e','src-fd7fb9dd8737ab5d','src-46babb6f9318d547','src-355de0c6e2a75205',
  'src-4631527cd57ef0f8','src-40d70969977fa87d','src-e76196d4a7b799ac','src-4947ff6d7d8d78f7',
  'src-9c795e2736c419a6','src-a06ed44222a26f73','src-5a721d4def74af93'
)
$decisions = @($decisions | Where-Object id -notin $duplicateIds)

$wordErrors = @($decisions | ForEach-Object {
  $words = @($_.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { "$($_.id): $words words" }
})
if ($wordErrors.Count) { throw "Description word-count errors: $($wordErrors -join '; ')" }

[ordered]@{
  schema_version = 1
  batch_id = 'expansion-25-ntmp-speed-study-archive'
  decisions = @($decisions)
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{ Decisions = $decisions.Count; OutputPath = $OutputPath } | ConvertTo-Json -Compress

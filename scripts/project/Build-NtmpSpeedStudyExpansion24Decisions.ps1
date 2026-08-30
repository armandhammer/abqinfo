[CmdletBinding()]
param([string]$OutputPath = 'project-state/discovery/ntmp-speed-study-expansion-24-decisions.json')

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

Add-Decision 'src-728f643345394dc4' 'Flora Vista Avenue Cut-Through Traffic Study' '2019-06' 'cabq-flora-vista-avenue-cut-through-traffic-study-2019.pdf' 'Supplements the 2018 Flora Vista speed study with peak-period observations between Condershire Drive and Coors Boulevard, finding cut-through traffic well below the NTMP threshold.'
Add-Decision 'src-ef06d7358f6a8c4d' 'Gallant Fox Road Speed Study' '2021-08-26' 'cabq-gallant-fox-road-speed-study-2021.pdf' 'Evaluates Gallant Fox Road between Juan Tabo Boulevard and Count Fleet Street and finds two NTMP threshold sets were met, qualifying the segment for traffic-calming measures.'
Add-Decision 'src-318000b2b03f9e81' 'General Stilwell Street Speed Study' '2018-05' 'cabq-general-stilwell-street-speed-study-2018.pdf' 'Documents speed, traffic-volume, and crash conditions on General Stilwell Street and concludes that the corridor did not meet the NTMP threshold for traffic-calming improvements.'
Add-Decision 'src-25ac8b2b16ee6df1' 'Gonzales Road Speed Study' '2020-03' 'cabq-gonzales-road-speed-study-2020.pdf' 'Analyzes crash, volume, and speed data on Gonzales Road and finds two of four NTMP criteria were met, satisfying the minimum traffic-calming threshold.'
Add-Decision 'src-2a52d0ec67939e94' 'Grande Drive Speed Study' '2017-04' 'cabq-grande-drive-speed-study-2017.pdf' 'Reviews traffic volumes, crashes, and speeds on Grande Drive and finds that none of the applicable NTMP criteria were met to warrant traffic calming.'
Add-Decision 'src-0a79d2ba39c98f19' 'Gun Club Road Speed Study' '2019-06' 'cabq-gun-club-road-speed-study-2019.pdf' 'Studies Gun Club Road from Coors Boulevard to Southfield Drive and finds two of four NTMP criteria were met, satisfying the minimum traffic-calming threshold.'
Add-Decision 'src-1c5b6b5453302e21' 'Gwin Road Speed Study' '2019-06' 'cabq-gwin-road-speed-study-2019.pdf' 'Analyzes Gwin Road from Unser Boulevard to 75th Street using crash, volume, and speed data and finds none of the four NTMP criteria were met.'
Add-Decision 'src-784b9822a6d67446' 'Harper Drive Speed Study' '2018-05' 'cabq-harper-drive-speed-study-2018.pdf' 'Finds Harper Drive met the minimum NTMP threshold and recommends permanent radar-feedback signs in each direction as a traffic-calming response.'
Add-Decision 'src-252b72094fe76273' 'Hidalgo Circle Speed Study' '2017-05' 'cabq-hidalgo-circle-speed-study-2017.pdf' 'Reviews speed, volume, and crash conditions on Hidalgo Circle and finds the street did not meet the two-warrant minimum required for NTMP traffic calming.'
Add-Decision 'src-390588245fb0f7e4' 'Hilton Avenue Speed Study' '2021-08-16' 'cabq-hilton-avenue-speed-study-2021.pdf' 'Evaluates Hilton Avenue between Wyoming Boulevard and General Chennault Street and finds none of nine NTMP threshold sets, so the segment did not qualify for traffic calming.'
Add-Decision 'src-8193b1f94e117608' 'Innovation Parkway Traffic and Safety Study' '2018-05' 'cabq-innovation-parkway-traffic-safety-study-2018.pdf' 'Combines speed, crash, operational, cut-through, stop-control, and pedestrian-beacon analyses for Innovation Parkway, recommending four radar-feedback signs while finding stop control and a HAWK beacon unwarranted.'
Add-Decision 'src-d4671b0db660def8' 'Jane Street Speed Study' '2018-05' 'cabq-jane-street-speed-study-2018.pdf' 'Documents speed, traffic-volume, and crash conditions on Jane Street and concludes that none of the NTMP criteria were met to warrant traffic calming.'
Add-Decision 'src-b413d9e47205ef64' 'Lafayette Drive Speed Study' '2015-03' 'cabq-lafayette-drive-speed-study-2015.pdf' 'Evaluates Lafayette Drive between Comanche Road and Delamar Avenue and finds that none of the City criteria were met to warrant speed humps.'
Add-Decision 'src-c9cc239ec8ae5fb2' 'Landau Street Speed Study' '2017-05' 'cabq-landau-street-speed-study-2017.pdf' 'Finds Landau Street met two of four NTMP warrants and identifies signage, striping, and speed humps or tables for more detailed traffic-calming evaluation.'
Add-Decision 'src-169af942c3378430' 'Los Lomas Road Speed Study' '2017-06' 'cabq-los-lomas-road-speed-study-2017.pdf' 'Evaluates traffic, crashes, and speeds on Los Lomas Road and concludes that the roadway did not meet the minimum NTMP traffic-calming threshold.'
Add-Decision 'src-a9c25db3eb18ad4a' 'Los Tretos Street Speed Study' '2017-06' 'cabq-los-tretos-street-speed-study-2017.pdf' 'Reviews traffic volumes, crashes, and speeds on Los Tretos Street and finds the street did not meet the minimum NTMP traffic-calming threshold.'
Add-Decision 'src-fca2fee9ce97b641' 'Lucretia Street Speed Study' '2018-10' 'cabq-lucretia-street-speed-study-2018.pdf' 'Studies Lucretia Street from Brian Avenue to Sapphire Street and finds one of four NTMP criteria, below the minimum threshold for traffic calming.'
Add-Decision 'src-66a63e9f64c19936' 'Luna Boulevard Speed Study' '2017-09' 'cabq-luna-boulevard-speed-study-2017.pdf' 'Reviews traffic volumes, crashes, and speeds on Luna Boulevard and finds that none of the NTMP criteria were met to warrant traffic calming.'
Add-Decision 'src-7f57859df60e6c62' 'Marble Avenue Speed Study' '2021-08-16' 'cabq-marble-avenue-speed-study-2021.pdf' 'Evaluates Marble Avenue between Stanford Drive and Girard Boulevard and finds none of nine NTMP threshold sets, so the street did not qualify for traffic calming.'
Add-Decision 'src-90ee10797ecae9b0' 'Mary Ellen Street Speed Study' '2018-03' 'cabq-mary-ellen-street-speed-study-2018.pdf' 'Documents speed and traffic conditions on Mary Ellen Street and concludes that none of the NTMP criteria were met to warrant traffic calming.'
Add-Decision 'src-024e9015bd3ca346' 'Milne Road Speed Study' '2018-10' 'cabq-milne-road-speed-study-2018.pdf' 'Studies Milne Road from Atrisco Drive to 64th Street and finds one of four NTMP criteria, below the minimum threshold for traffic calming.'
Add-Decision 'src-6b268503153a85d5' 'Morris Street Speed Study' '2019-01' 'cabq-morris-street-speed-study-2019.pdf' 'Studies Morris Street from Prospect and Norman avenues to Indian School Road and finds one of four NTMP criteria, below the minimum traffic-calming threshold.'
Add-Decision 'src-7756694083c48fbe' 'Ortiz Drive Speed Study' '2018-05' 'cabq-ortiz-drive-speed-study-2018.pdf' 'Documents speed, traffic-volume, and crash conditions on Ortiz Drive and concludes that none of the NTMP criteria were met to warrant traffic calming.'
Add-Decision 'src-6b8114bf65152029' 'Parsifal Street Speed Study' '2021-08-16' 'cabq-parsifal-street-speed-study-2021.pdf' 'Evaluates Parsifal Street between Easterday Drive and Constitution Avenue and finds none of nine NTMP threshold sets, so the street did not qualify for traffic calming.'
Add-Decision 'src-e724d365fa3c6251' 'Paso Fino Place Speed Study' '2018-05' 'cabq-paso-fino-place-speed-study-2018.pdf' 'Documents speed and traffic conditions on Paso Fino Place and concludes that none of the NTMP criteria were met to warrant traffic calming.'
Add-Decision 'src-a858ed6f98b007c7' 'Quincy Street Speed Study' '2018-10' 'cabq-quincy-street-speed-study-2018.pdf' 'Studies Quincy Street from Claremont Avenue to Phoenix Avenue and finds one of four NTMP criteria, below the minimum threshold for traffic calming.'
Add-Decision 'src-a373c766ee89a57b' 'San Pablo Street Speed Study' '2018-10' 'cabq-san-pablo-street-speed-study-2018.pdf' 'Studies San Pablo Street from Spring Avenue to Marble Avenue and finds one of four NTMP criteria, below the minimum threshold for traffic calming.'
Add-Decision 'src-3ffb5f69a35a216a' 'San Pasquale Avenue Speed Study' '2018-10' 'cabq-san-pasquale-avenue-speed-study-2018.pdf' 'Studies San Pasquale Avenue from Laguna Boulevard to Alhambra Avenue and finds one of four NTMP criteria, below the minimum threshold for traffic calming.'
Add-Decision 'src-8f938afaa196864e' 'San Rafael Avenue Speed Study' '2018-10' 'cabq-san-rafael-avenue-speed-study-2018.pdf' 'Studies San Rafael Avenue from Princeton Drive to Carlisle Boulevard and finds one of four NTMP criteria, below the minimum threshold for traffic calming.'
Add-Decision 'src-20b9ae8ffa26954f' 'Santa Clara Avenue Speed Study' '2018-12' 'cabq-santa-clara-avenue-speed-study-2018.pdf' 'Studies Santa Clara Avenue from Linda Vista Avenue to Amherst Drive and finds none of the four NTMP criteria, below the minimum traffic-calming threshold.'

$wordErrors = @($decisions | ForEach-Object {
  $words = @($_.description -split '\s+' | Where-Object { $_ }).Count
  if ($words -lt 20 -or $words -gt 50) { "$($_.id): $words words" }
})
if ($wordErrors.Count) { throw "Description word-count errors: $($wordErrors -join '; ')" }

[ordered]@{
  schema_version = 1
  batch_id = 'expansion-24-ntmp-speed-study-archive'
  decisions = @($decisions)
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8

[pscustomobject]@{ Decisions = $decisions.Count; OutputPath = $OutputPath } | ConvertTo-Json -Compress

[CmdletBinding()]
param(
    [string]$MasterInventoryPath = 'project-state/master-inventory.json'
)

$ErrorActionPreference = 'Stop'
$now = (Get-Date).ToUniversalTime().ToString('o')
$text = Get-Content -LiteralPath $MasterInventoryPath -Raw

function Set-ExactJsonValue {
    param([string]$Id, [string]$Property, [object]$Value)

    if ($null -eq $Value) {
        $jsonValue = 'null'
    } else {
        $jsonValue = ConvertTo-Json -InputObject $Value -Compress
    }
    $pattern = '(?s)("id": "' + [regex]::Escape($Id) + '".*?"' + [regex]::Escape($Property) + '": )("(?:[^"\\]|\\.)*"|null|\[\s*\]|\d+)'
    $script:text = [regex]::Replace($script:text, $pattern, {
        param($match)
        $match.Groups[1].Value + $jsonValue
    }, 1)
    if ($script:text -notmatch '"id": "' + [regex]::Escape($Id) + '"') { throw "Missing candidate $Id." }
}

function Add-ProcessingNote {
    param([string]$Id, [string]$Note)

    $jsonNote = ConvertTo-Json -InputObject $Note -Compress
    $pattern = '(?s)("id": "' + [regex]::Escape($Id) + '".*?"processing_notes": \[)(.*?)(\n\s*\])'
    $script:text = [regex]::Replace($script:text, $pattern, {
        param($match)
        $existing = $match.Groups[2].Value.TrimEnd()
        if ($existing) { return $match.Groups[1].Value + $existing + ",`r`n        " + $jsonNote + $match.Groups[3].Value }
        return $match.Groups[1].Value + "`r`n        " + $jsonNote + $match.Groups[3].Value
    }, 1)
}

function Resolve-Case {
    param(
        [string]$Id,
        [string]$Title,
        [object]$Date,
        [string]$Description,
        [string]$CanonicalPage,
        [string]$ImplementationLocation,
        [string]$ValidationStatus,
        [string]$ProcessingNote
    )

    Set-ExactJsonValue $Id 'status' 'validated'
    Set-ExactJsonValue $Id 'title' $Title
    Set-ExactJsonValue $Id 'date' $Date
    Set-ExactJsonValue $Id 'description' $Description
    Set-ExactJsonValue $Id 'description_word_count' @($Description -split '\s+' | Where-Object { $_ }).Count
    Set-ExactJsonValue $Id 'proposed_canonical_page' $CanonicalPage
    Set-ExactJsonValue $Id 'implementation_location' $ImplementationLocation
    Set-ExactJsonValue $Id 'implementation_locations' @($ImplementationLocation)
    Set-ExactJsonValue $Id 'validation_status' $ValidationStatus
    Set-ExactJsonValue $Id 'exclusion_reason' $null
    Set-ExactJsonValue $Id 'updated_at' $now
    Add-ProcessingNote $Id $ProcessingNote
}

Resolve-Case `
    -Id 'src-6735737588d294e0' `
    -Title '2003 Environmental Planning Commission Recommendation and Notice of Decision - Mayor Proposed 2003-2012 Decade Plan' `
    -Date '2003-01-16' `
    -Description 'Preserves the Environmental Planning Commission recommendation and official notice-of-decision record for the Mayor Proposed 2003-2012 Decade Plan. It records the Commission action that preceded later Mayor and City Council consideration; it is not the enacted capital program.' `
    -CanonicalPage 'content/city-data/capital-spending.md' `
    -ImplementationLocation 'content/city-data/capital-spending.md' `
    -ValidationStatus 'validated for City Data capital-spending placement; substantive EPC recommendation/decision record, distinguished from later enacted Council action' `
    -ProcessingNote 'Archive reconciliation editorial resolution 2026-09-17: user confirmed that this substantive EPC recommendation/Notice of Decision packet follows existing ABQInfo commission-record precedent. It is described as preceding later Mayor and Council action, not as an enacted capital program.'

Resolve-Case `
    -Id 'src-3c9907796a0cfaf3' `
    -Title 'Water Master Plan Infrastructure Zone (WIZ) Map - Appendix page B-6; parent document not located' `
    -Date $null `
    -Description 'Preserves the official standalone Water Master Plan Infrastructure Zone (WIZ) map marked appendix page B-6. The complete parent document has not been located, so the map is retained without inferring a parent-plan title or treating the appendix as a complete plan.' `
    -CanonicalPage 'content/city-data/capital-spending.md' `
    -ImplementationLocation 'content/city-data/capital-spending.md' `
    -ValidationStatus 'validated for City Data capital-spending placement with explicit parent-document limitation' `
    -ProcessingNote 'Archive reconciliation editorial resolution 2026-09-17: user authorized retention and eventual standalone presentation of this official appendix map. The parent document remains unlocated and is stated as a limitation.'

Resolve-Case `
    -Id 'src-f6feb3549d055097' `
    -Title 'Development Process Manual Executive Committee Agenda - April 4, 2018 (approved minutes not located)' `
    -Date '2018-04-04' `
    -Description 'Official Development Process Manual Executive Committee agenda for April 4, 2018. Approved minutes were not located after the recorded official-source review; the agenda is preserved only as an agenda and does not establish that the scheduled meeting occurred or that an action was adopted.' `
    -CanonicalPage 'content/development-land-use/development-process.md' `
    -ImplementationLocation 'annual DPM Executive Committee 2018 compilation (locally generated; R2 upload externally gated)' `
    -ValidationStatus 'validated for inclusion in the annual DPM Executive Committee compilation as Agenda - approved minutes not located; no individual visible placement before the compilation is uploaded' `
    -ProcessingNote 'Archive reconciliation editorial resolution 2026-09-17: user adopted annual consolidation for short DPM Executive Committee records. This agenda is included in the local 2018 packet with the exact approved-minutes limitation and no assertion that the meeting occurred.'

$text = $text -replace '"generated_at": "[^"]+"', ('"generated_at": "' + $now + '"')
$text = $text -replace '"validated": 1358', '"validated": 1361'
$text = $text -replace '"requires human review": 194', '"requires human review": 191'
[System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($MasterInventoryPath), $text, [System.Text.UTF8Encoding]::new($false))
Write-Output "Resolved 3 editorial cases with targeted changes in $MasterInventoryPath."

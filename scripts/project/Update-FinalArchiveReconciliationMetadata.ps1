[CmdletBinding()]
param(
    [string]$MasterPath = 'project-state/master-inventory.json',
    [string[]]$LinkedMasterIds = @('src-6735737588d294e0', 'src-3c9907796a0cfaf3', 'src-f6feb3549d055097')
)
$ErrorActionPreference = 'Stop'
$timestamp = (Get-Date).ToUniversalTime().ToString('o')
$path = [IO.Path]::GetFullPath($MasterPath)
$text = [IO.File]::ReadAllText($path)
$generated = [regex]::Match($text, '(?m)^  "generated_at": "[^"]+"')
if (-not $generated.Success) { throw 'Master inventory generated_at field was not found.' }
$text = $text.Remove($generated.Index, $generated.Length).Insert($generated.Index, "  `"generated_at`": `"$timestamp`"")
foreach ($id in $LinkedMasterIds) {
    $pattern = '(?s)("id": "' + [regex]::Escape($id) + '".*?"updated_at": ")[^"]+("\s*[},])'
    $match = [regex]::Match($text, $pattern)
    if (-not $match.Success) { throw "updated_at field was not found for $id." }
    $replacement = $match.Groups[1].Value + $timestamp + $match.Groups[2].Value
    $text = $text.Remove($match.Index, $match.Length).Insert($match.Index, $replacement)
}
[IO.File]::WriteAllText($path, $text, [Text.UTF8Encoding]::new($false))
[pscustomobject]@{ master_generated_at = $timestamp; updated_master_records = $LinkedMasterIds } | ConvertTo-Json

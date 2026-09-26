[CmdletBinding()]
param([Parameter(Mandatory)][string]$RequestsPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$requests=Get-Content $RequestsPath -Raw -Encoding UTF8|ConvertFrom-Json -DateKind String
$word=$null;$ppt=$null
try {
 foreach($r in $requests){
  if(Test-Path -LiteralPath $r.inspection_pdf){continue}
  $inputPath=[IO.Path]::GetFullPath($r.staged_path);$outputPath=[IO.Path]::GetFullPath($r.inspection_pdf)
  $doc=$null
  try {
   if($r.container -eq 'PPTX'){
    if(-not $ppt){$ppt=New-Object -ComObject PowerPoint.Application;$ppt.AutomationSecurity=3}
    $doc=$ppt.Presentations.Open($inputPath,-1,0,0);$doc.SaveAs($outputPath,32)
   }else{
    if(-not $word){$word=New-Object -ComObject Word.Application;$word.Visible=$false;$word.DisplayAlerts=0;$word.AutomationSecurity=3}
    $doc=$word.Documents.Open($inputPath,$false,$true);$doc.ExportAsFixedFormat($outputPath,17)
   }
   Write-Output ('Rendered inspection only: '+$r.staged_path)
  }catch{Write-Warning ($r.staged_path+': '+$_.Exception.Message)}
  finally{if($doc){if($r.container -eq 'PPTX'){$doc.Close()}else{$doc.Close(0)}}}
 }
}finally{if($word){try{$word.Quit()}catch{Write-Warning 'Word already closed after all render tasks'}};if($ppt){try{$ppt.Quit()}catch{Write-Warning 'PowerPoint already closed after all render tasks'}}}

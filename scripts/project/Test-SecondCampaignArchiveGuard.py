#!/usr/bin/env python3
"""Exercise the production R2 guard with isolated listings and no remote writes."""
import copy,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/'scripts/project/Invoke-SecondLargeOrdinaryCampaignArchive.ps1').read_text(encoding='utf-8-sig')
guard=source[source.index('function Guard {'):source.index('# The complete listing')]
folder=ROOT/'tmp/second-campaign-guard-regression';folder.mkdir(parents=True,exist_ok=True)
(folder/'Get-R2Inventory.ps1').write_text("param([string]$OutputPath)\nCopy-Item -LiteralPath $fixtureListing -Destination $OutputPath -Force\n",encoding='utf-8')
baseline={'objects':[{'key':'a/one.pdf','size_bytes':3,'etag':'One'},{'key':'b/two.pdf','size_bytes':5,'etag':'Two'}]}
intent={'r2_key':'c/new.pdf','fresh_source_qa':{'size_bytes':7},'upload_intent':{'key_was_absent':True}}
valid={'objects':baseline['objects']+[{'key':'c/new.pdf','size_bytes':7,'etag':'New'}],'total_bytes':15}
cases=[('valid',valid,[intent],True)]
def case(name,change,records=None):
 d=copy.deepcopy(valid);change(d);cases.append((name,d,[intent] if records is None else records,False))
case('missing_old_key',lambda d:d['objects'].pop(0))
case('old_size_changed',lambda d:d['objects'][0].update(size_bytes=4))
case('old_etag_changed',lambda d:d['objects'][0].update(etag='one'))
case('unexpected_new_key',lambda d:d['objects'][-1].update(key='c/unknown.pdf'))
case('intent_size_changed',lambda d:d['objects'][-1].update(size_bytes=8))
case('duplicate_intent',lambda d:None,[intent,intent])
case('storage_ceiling',lambda d:d.update(total_bytes=10000000001))
case('casefold_collision',lambda d:d['objects'].append({'key':'A/ONE.pdf','size_bytes':3,'etag':'Other'}))
case('changed_old_key_case',lambda d:d['objects'][0].update(key='A/ONE.pdf'))
tests=[]
for name,listing,intents,expected in cases:
 lp=folder/(name+'.json');lp.write_text(json.dumps(listing),encoding='utf-8')
 tests.append({'name':name,'listing':str(lp),'intents':intents,'expected_pass':expected})
fixtures=folder/'fixtures.json';fixtures.write_text(json.dumps({'baseline':baseline,'tests':tests}),encoding='utf-8')
driver=folder/'Run-GuardFixtures.ps1'
driver.write_text("Set-StrictMode -Version Latest\n$ErrorActionPreference='Stop'\nparam_dummy\n".replace('param_dummy',guard)+"\n$fx=Get-Content (Join-Path $PSScriptRoot 'fixtures.json') -Raw|ConvertFrom-Json\n$baseline=$fx.baseline\n$guardPath=Join-Path $PSScriptRoot 'guard-result.json'\nforeach($test in $fx.tests){\n $fixtureListing=$test.listing;$allFamilyRecords=@($test.intents);$passed=$false\n try{$result=Guard;$passed=$true}catch{}\n if($passed -ne $test.expected_pass){throw ('Unexpected guard result: '+$test.name)}\n}\nWrite-Output 'PASS: production guard rejects old-key/size/ETag changes, unknown/duplicate intents, casefold collisions and storage overflow; valid listing passes.'\n",encoding='utf-8')
result=subprocess.run(['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File',str(driver)],cwd=ROOT,capture_output=True,text=True)
assert result.returncode==0,(result.stdout,result.stderr)
print(result.stdout.strip())

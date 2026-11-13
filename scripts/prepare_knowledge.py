"""Split the complete import into bounded evidence windows and small hosted objects."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';SEED=DATA/'seed';SEED.mkdir(exist_ok=True)
manifest=json.loads((DATA/'manifest.json').read_text())
months={};seen=set()
for month in manifest['months']:
 for c in json.loads((DATA/('shard-'+month+'.json')).read_text()):
  messages=c['messages'];current=[];size=0
  def emit(msgs):
   if not any(m['role']=='user' for m in msgs):return
   if not any(m['role']=='agent' and len(m['text'])>35 and not re.search(r'hello and welcome|my name is|thank you for|rate your|how may i|how can i|hi.*welcome',m['text'],re.I) for m in msgs):return
   cid=c['id']+':'+msgs[0]['id']
   if cid in seen:return
   seen.add(cid);dt=msgs[-1]['time'];key=dt[:7]
   months.setdefault(key,[]).append({'id':cid,'source':c['id'],'updated':dt,'messages':msgs})
  for m in messages:
   if current and m['role']=='user' and (size>4500 or len(current)>20):
    emit(current);current=current[-2:];size=sum(len(x['text']) for x in current)
   current.append(m);size+=len(m['text'])
  if current:emit(current)
parts=[]
for month,records in sorted(months.items()):
 for i in range(0,len(records),150):
  key=month+'-'+str(i//150).zfill(3);items=records[i:i+150]
  (SEED/(key+'.json')).write_text(json.dumps(items,ensure_ascii=False));parts.append({'key':key,'month':month,'count':len(items)})
manifest['searchable_count']=len(seen);manifest['months']=sorted(months);manifest['parts']=parts;manifest['knowledge_format']='evidence-windows-v2'
(SEED/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'conversations':manifest['conversation_count'],'messages':manifest['message_count'],'evidence_windows':len(seen),'parts':len(parts),'largest_part_bytes':max(p.stat().st_size for p in SEED.glob('*.json'))}))

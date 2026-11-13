"""Fetch Freshchat history in resumable, bounded windows. Secrets never enter output."""
import csv,io,json,re,zipfile,time,urllib.request,urllib.error,concurrent.futures,hashlib,os
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data';DATA.mkdir(exist_ok=True)
CFG={}
for line in Path(os.environ.get('FRESHCHAT_ENV_FILE',str(ROOT/'.env.local'))).read_text().splitlines():
 if '=' in line and not line.lstrip().startswith('#'):
  k,v=line.split('=',1);CFG[k.strip()]=v.strip().strip('"').strip("'")
BASE=CFG.get('FRESHCHAT_BASE_URL','https://api.freshchat.com').rstrip('/')
def api(path,payload=None):
 req=urllib.request.Request(BASE+path,data=json.dumps(payload).encode() if payload else None,headers={'Authorization':'Bearer '+CFG['FRESHCHAT_API_TOKEN'],'Content-Type':'application/json'})
 for attempt in range(8):
  try:
   with urllib.request.urlopen(req,timeout=90) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code not in (429,500,502,503):raise RuntimeError('Freshchat HTTP '+str(e.code))
   time.sleep(min(60,20*(attempt+1)))
 raise RuntimeError('Freshchat retries exhausted')
def redact(t):
 t=re.sub(r'https?://\S+','[link removed]',t)
 t=re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}','[email removed]',t)
 t=re.sub(r'(?<!\w)(?:\+?\d[\d ()-]{8,}\d)(?!\w)','[number removed]',t)
 t=re.sub(r'\b(?:sk-(?:proj-)?|Bearer\s+)[A-Za-z0-9_-]{12,}','[secret removed]',t,flags=re.I)
 return t

def flatten(v):
 if isinstance(v,str):return [v]
 if isinstance(v,list):return sum((flatten(x) for x in v),[])
 if isinstance(v,dict):
  return sum((flatten(x) for k,x in v.items() if k not in ('url','name','file_name','size','id','content_type')),[])
 return []
def fetch_window(start,end):
 key=start.strftime('%Y-%m-%d');p=DATA/(key+'.json')
 if p.exists():
  cached=json.loads(p.read_text())
  if cached.get('download_parts'):return cached
 state=DATA/(key+'.job')
 if state.exists():rid=state.read_text().strip()
 else:
  r=api('/v2/reports/raw',{'start':start.isoformat(timespec='milliseconds').replace('+00:00','Z'),'end':end.isoformat(timespec='milliseconds').replace('+00:00','Z'),'event':'Chat-Transcript','format':'csv'})
  rid=r['id'];state.write_text(rid)
 deadline=time.time()+1200
 while time.time()<deadline:
  r=api('/v2/reports/raw/'+rid)
  if r.get('status')=='COMPLETED':break
  if r.get('status')=='FAILED':raise RuntimeError('Report generation failed '+key)
  time.sleep(35)
 else:raise RuntimeError('Report timed out '+key)
 contents=[]
 links=[x for x in r.get('links',[]) if x.get('link',{}).get('href')]
 if not links:raise RuntimeError('No export download links '+key)
 for link in links:
  url=link['link']['href']
  raw=urllib.request.urlopen(url,timeout=120).read()
  if raw.startswith(b'PK'):
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    for n in z.namelist():
     if n.lower().endswith('.csv'):contents.append(z.read(n).decode('utf-8-sig'))
  else:contents.append(raw.decode('utf-8-sig'))
 conv={};total=0
 for content in contents:
  for row in csv.DictReader(io.StringIO(content)):
   total+=1;cid=row.get('conversation_id','');role=row.get('actor_type','').lower()
   if not cid or role not in ('agent','user'):continue
   # Exclude private notes and automation/system events from knowledge.
   if any(w in (row.get('message_type','')+' '+row.get('detailed_message_type','')).lower() for w in ('private','note','system','bot')):continue
   try:text='\n'.join(dict.fromkeys(flatten(json.loads(row.get('message_parts') or '[]'))))
   except ValueError:text=row.get('message_parts','')
   text=redact(text).strip()
   if not text:continue
   c=conv.setdefault(cid,{'id':cid,'messages':[]})
   c['messages'].append({'id':row.get('message_id') or hashlib.sha256((row.get('created_time','')+role+text).encode()).hexdigest(),'role':role,'text':text[:5000],'time':row.get('created_time','')})
 result={'start':start.isoformat(),'end':end.isoformat(),'rows':total,'download_parts':len(links),'conversations':list(conv.values())}
 p.write_text(json.dumps(result,ensure_ascii=False))
 print(json.dumps({'window':key,'rows':total,'download_parts':len(links),'conversations':len(conv)}),flush=True)
 return result
if __name__=='__main__':
 start=datetime(2025,11,13,tzinfo=timezone.utc);end=datetime.now(timezone.utc);windows=[]
 while start<end:
  stop=min(start+timedelta(days=30),end);windows.append((start,stop));start=stop
 results=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
  tasks={pool.submit(fetch_window,a,b):(a,b) for a,b in windows}
  for task in concurrent.futures.as_completed(tasks):
   try:results.append(task.result())
   except Exception as e:
    a,b=tasks[task];errors.append({'start':a.isoformat(),'end':b.isoformat(),'error':str(e)[:200]});print(json.dumps({'failed':a.isoformat(),'error':str(e)[:200]}),flush=True)
 merged={}
 for result in results:
  for c in result['conversations']:
   item=merged.setdefault(c['id'],{'id':c['id'],'messages':{}})
   for m in c['messages']:item['messages'][m['id']]=m
 shards={}
 for item in merged.values():
  msgs=sorted(item['messages'].values(),key=lambda m:m['time'])
  # Keep customer questions and substantive human answers; greetings alone are not evidence.
  users=[m for m in msgs if m['role']=='user'];agents=[m for m in msgs if m['role']=='agent' and len(m['text'])>35 and not re.search(r'hello and welcome|my name is|thank you for|rate your|how may i|how can i|hi.*welcome',m['text'],re.I)]
  if not users or not agents:continue
  month=msgs[-1]['time'][:7];item={'id':item['id'],'updated':msgs[-1]['time'],'messages':msgs}
  shards.setdefault(month,[]).append(item)
 manifest={'requested_start':'2025-11-13T00:00:00Z','requested_end':end.isoformat(),'imported_at':datetime.now(timezone.utc).isoformat(),'conversation_count':len(merged),'searchable_count':sum(map(len,shards.values())),'message_count':sum(len(c['messages']) for c in merged.values()),'completed_windows':[{'start':r['start'],'end':r['end'],'rows':r['rows']} for r in results],'failed_windows':errors,'months':[]}
 for month,items in sorted(shards.items()):
  out=DATA/('shard-'+month+'.json');out.write_text(json.dumps(items,ensure_ascii=False));manifest['months'].append(month)
 (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps(manifest),flush=True)

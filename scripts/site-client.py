"""One-shot owner-private Site client. Receives service credentials on hidden stdin only."""
import sys,json,urllib.request,urllib.error,termios
from pathlib import Path
if sys.stdin.isatty():
 state=termios.tcgetattr(sys.stdin.fileno());state[3]&=~termios.ECHO;termios.tcsetattr(sys.stdin.fileno(),termios.TCSANOW,state)
print('Ready for private Site request JSON on hidden stdin.',flush=True)
config=json.loads(sys.stdin.readline());origin=config['origin'].rstrip('/');token=config['token'];root=Path(__file__).resolve().parents[1]
def call(path,payload=None):
 headers={'OAI-Sites-Authorization':'Bearer '+token,'Content-Type':'application/json'}
 req=urllib.request.Request(origin+path,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=180) as r:return json.load(r)
 except urllib.error.HTTPError as e:
  try:d=json.load(e)
  except:d={'error':'HTTP '+str(e.code)}
  return {'http_status':e.code,**d}
if config['op']=='upload':
 import concurrent.futures
 seed=root/'data/seed';m=json.loads((seed/'manifest.json').read_text())
 if m.get('failed_windows'):raise SystemExit('Refusing full-history import while batches are missing.')
 def upload(part):
  records=json.loads((seed/(part['key']+'.json')).read_text())
  result=call('/admin/import',{'part':part['key'],'conversations':records})
  if result.get('error'):raise RuntimeError(str(result))
  return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for i,result in enumerate(pool.map(upload,m['parts'])):
   if i%20==0:print(json.dumps({'uploaded_parts':i+1,'total_parts':len(m['parts'])}),flush=True)
 for month in m['months']:
  rows=json.loads((seed/('index-'+month+'.json')).read_text())
  result=call('/admin/import',{'month':month,'index':rows})
  if result.get('error'):raise RuntimeError(str(result))
  print(json.dumps(result),flush=True)
 print(json.dumps(call('/admin/import',{'manifest':m})),flush=True)
 print(json.dumps(call('/api/status')),flush=True)
elif config['op']=='get':print(json.dumps(call(config.get('path','/api/status'))),flush=True)
else:print(json.dumps(call(config.get('path','/api/sync'),config.get('body',{}))),flush=True)

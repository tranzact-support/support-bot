"""Read daily Freshchat exports; credentials remain in environment variables."""
import sys,os,json
from pathlib import Path
from datetime import datetime,timedelta,timezone
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from import_history import fetch_window
meta=json.loads((ROOT/'docs/knowledge/manifest.json').read_text())
end=datetime.now(timezone.utc)
since=datetime.fromisoformat(meta['last_successful_sync'].replace('Z','+00:00'))
start=max(datetime(2025,11,13,tzinfo=timezone.utc),since-timedelta(days=2))
conversations=[]
while start<end:
 stop=min(start+timedelta(days=30),end)
 # Each run uses fresh temporary downloads; never reuse an incomplete daily export.
 cache=ROOT/'data'/(start.strftime('%Y-%m-%d')+'.json')
 if cache.exists():cache.unlink()
 result=fetch_window(start,stop);conversations.extend(result['conversations']);start=stop
(ROOT/'data/refresh-incoming.json').write_text(json.dumps({'end':end.isoformat(),'conversations':conversations},ensure_ascii=False))
print('Freshchat download completed; plaintext exports stay outside the published folder.')

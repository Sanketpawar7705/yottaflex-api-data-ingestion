import json,uuid,logging
from datetime import datetime,timedelta,timezone
from app.config import *
from app.validation import validate
from app.client import APIClient
from app.storage import connect
logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger('pipeline')
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def run(path=None):
    path=path or DATABASE_PATH;c=connect(path);rid=str(uuid.uuid4());m={'pages':0,'received':0,'loaded':0,'rejected':0,'duplicates':0}
    c.execute('INSERT INTO runs(run_id,started_at,status) VALUES(?,?,?)',(rid,now(),'running'));c.commit()
    try:
        cp=c.execute("SELECT last_updated_at FROM checkpoints WHERE source='mock_api'").fetchone();after=None
        if cp:
            d=datetime.fromisoformat(cp[0].replace('Z','+00:00'))-timedelta(seconds=LOOKBACK_SECONDS);after=d.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
        page=1;seen=set();max_updated=cp[0] if cp else None;api=APIClient(API_BASE_URL,API_TOKEN,MAX_RETRIES,10)
        while True:
            status,body,p=api.fetch_page(page,PAGE_SIZE,after)
            c.execute('INSERT INTO raw_responses(run_id,page,fetched_at,status,body) VALUES(?,?,?,?,?)',(rid,page,now(),status,body));m['pages']+=1
            if not isinstance(p,dict) or not isinstance(p.get('records'),list):raise ValueError('unexpected API response shape')
            rows=p['records'];m['received']+=len(rows)
            for raw in rows:
                source=f'mock_api_page_{page}'
                try:
                    r=validate(raw);eid=r['event_id']
                    if eid in seen:m['duplicates']+=1;continue
                    seen.add(eid)
                    old=c.execute('SELECT updated_at FROM events WHERE event_id=?',(eid,)).fetchone()
                    if old and old['updated_at']>r['updated_at']:m['duplicates']+=1;continue
                    c.execute('''INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET customer_id=excluded.customer_id,amount=excluded.amount,amount_minor=excluded.amount_minor,currency=excluded.currency,status=excluded.status,event_time=excluded.event_time,updated_at=excluded.updated_at,source_file=excluded.source_file,run_id=excluded.run_id,ingested_at=excluded.ingested_at WHERE excluded.updated_at>=events.updated_at''',
                    (eid,r['customer_id'],r['amount'],round(r['amount']*100),r['currency'],r['status'],r['event_time'],r['updated_at'],source,rid,now()));m['loaded']+=1
                    if max_updated is None or r['updated_at']>max_updated:max_updated=r['updated_at']
                except (ValueError,TypeError) as e:
                    m['rejected']+=1;c.execute('INSERT INTO rejects(run_id,source_file,event_id,reason,raw_record,rejected_at) VALUES(?,?,?,?,?,?)',(rid,source,raw.get('event_id') if isinstance(raw,dict) else None,str(e),json.dumps(raw,sort_keys=True),now()))
            c.commit();log.info('run_id=%s page=%s rows=%s',rid,page,len(rows))
            if page>=int(p.get('total_pages',page)) or not rows:break
            page+=1
        if max_updated:c.execute("INSERT INTO checkpoints VALUES('mock_api',?) ON CONFLICT(source) DO UPDATE SET last_updated_at=excluded.last_updated_at",(max_updated,))
        c.execute('UPDATE runs SET ended_at=?,status=?,pages=?,received=?,loaded=?,rejected=?,duplicates=? WHERE run_id=?',(now(),'success',m['pages'],m['received'],m['loaded'],m['rejected'],m['duplicates'],rid));c.commit()
        return {'run_id':rid,'status':'success',**m}
    except Exception as e:
        c.rollback();c.execute('UPDATE runs SET ended_at=?,status=?,pages=?,received=?,loaded=?,rejected=?,duplicates=?,error=? WHERE run_id=?',(now(),'failed',m['pages'],m['received'],m['loaded'],m['rejected'],m['duplicates'],str(e),rid));c.commit();raise
    finally:c.close()
if __name__=='__main__':print(json.dumps(run(),indent=2))

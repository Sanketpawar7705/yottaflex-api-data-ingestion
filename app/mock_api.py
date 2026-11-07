"""Local deterministic paginated API with authentication and fault injection."""
import os, math
from datetime import datetime,timedelta,timezone
from fastapi import FastAPI,Header,HTTPException,Query
from pydantic import BaseModel
app=FastAPI(title='YottaFlex Mock Source API')
TOKEN=os.getenv('API_TOKEN','local-demo-token')
COUNT=int(os.getenv('MOCK_RECORD_COUNT','250'))
request_count=0; rate_limit_every=0; fail_once=False; failed=False; schema_drift=False

def generate(n):
    base=datetime(2026,1,1,tzinfo=timezone.utc); out=[]
    for i in range(n):
        t=base+timedelta(minutes=i)
        r={'event_id':f'EVT-{i+1:07d}','customer_id':f'CUST-{i%100+1:04d}',
           'amount':round((i%50000+1)/100,2),'currency':'INR' if i%3 else 'USD',
           'status':('pending','completed','cancelled')[i%3],
           'event_time':(t-timedelta(minutes=i%7)).isoformat().replace('+00:00','Z'),
           'updated_at':t.isoformat().replace('+00:00','Z')}
        if i and i%97==0:r['customer_id']='CUST-INVALID'
        if i and i%89==0:r['amount']=-1
        if i and i%83==0:r['event_id']=f'EVT-{i:07d}'
        if i and i%79==0:r['amount']=None
        out.append(r)
    return out
records=generate(COUNT)
def auth(key):
    if key!=TOKEN: raise HTTPException(401,'Invalid API key')
@app.get('/health')
def health():return {'status':'ok','records':len(records)}
@app.get('/records')
def get_records(page:int=Query(1,ge=1),page_size:int=Query(100,ge=1,le=5000),updated_after:str|None=None,x_api_key:str|None=Header(None)):
    global request_count,failed
    auth(x_api_key);request_count+=1
    if rate_limit_every and request_count%rate_limit_every==0:raise HTTPException(429,'Rate limit injected',headers={'Retry-After':'0'})
    if fail_once and not failed:failed=True;raise HTTPException(503,'One-time transient failure')
    rows=records
    if updated_after:
        cutoff=datetime.fromisoformat(updated_after.replace('Z','+00:00'))
        rows=[r for r in rows if datetime.fromisoformat(r['updated_at'].replace('Z','+00:00'))>cutoff]
    start=(page-1)*page_size; chunk=[dict(x) for x in rows[start:start+page_size]]
    if schema_drift and chunk:chunk[0]['unexpected_vendor_field']='drift'
    return {'page':page,'page_size':page_size,'total':len(rows),'total_pages':math.ceil(len(rows)/page_size),'records':chunk}
class Faults(BaseModel):
    rate_limit_every:int=0;fail_once:bool=False;schema_drift:bool=False
@app.post('/admin/configure')
def configure(c:Faults):
    global rate_limit_every,fail_once,failed,schema_drift,request_count
    rate_limit_every=c.rate_limit_every;fail_once=c.fail_once;failed=False;schema_drift=c.schema_drift;request_count=0
    return {'configured':True}
@app.post('/admin/reset')
def reset():
    global records,request_count,failed
    records=generate(COUNT);request_count=0;failed=False
    return {'reset':True,'records':len(records)}

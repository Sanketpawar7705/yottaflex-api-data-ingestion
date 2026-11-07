import threading,time,requests,uvicorn
import pytest
from app.mock_api import app
from app.pipeline import run
from app.storage import connect
@pytest.fixture(scope='module')
def server():
 s=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=8765,log_level='error'));t=threading.Thread(target=s.run,daemon=True);t.start()
 for _ in range(60):
  try:requests.get('http://127.0.0.1:8765/health',timeout=.2);break
  except requests.RequestException:time.sleep(.1)
 yield 'http://127.0.0.1:8765';s.should_exit=True;t.join(3)
def setup(url,**kwargs):
 x={'rate_limit_every':0,'fail_once':False,'schema_drift':False};x.update(kwargs);requests.post(url+'/admin/configure',json=x,timeout=3).raise_for_status()
def test_ingest_and_rerun(server,tmp_path,monkeypatch):
 import app.pipeline as p
 monkeypatch.setattr(p,'API_BASE_URL',server);monkeypatch.setattr(p,'PAGE_SIZE',60);monkeypatch.setattr(p,'MAX_RETRIES',4)
 setup(server);path=str(tmp_path/'t.db');a=run(path);c=connect(path);n=c.execute('select count(*) from events').fetchone()[0];b=run(path);n2=c.execute('select count(*) from events').fetchone()[0]
 assert a['status']==b['status']=='success' and n==n2
 assert c.execute('select count(*) from raw_responses').fetchone()[0]>0
 assert c.execute('select count(*) from rejects').fetchone()[0]>0;c.close()
def test_retry_429_and_503(server,tmp_path,monkeypatch):
 import app.pipeline as p
 monkeypatch.setattr(p,'API_BASE_URL',server);monkeypatch.setattr(p,'PAGE_SIZE',500);monkeypatch.setattr(p,'MAX_RETRIES',5)
 setup(server,rate_limit_every=2,fail_once=True);assert run(str(tmp_path/'retry.db'))['status']=='success'
def test_empty_batch(server,tmp_path,monkeypatch):
 import app.pipeline as p, app.mock_api as mock
 monkeypatch.setattr(p,'API_BASE_URL',server);old=mock.records;mock.records=[]
 try:setup(server);assert run(str(tmp_path/'empty.db'))['received']==0
 finally:mock.records=old
def test_schema_drift_quarantined(server,tmp_path,monkeypatch):
 import app.pipeline as p
 monkeypatch.setattr(p,'API_BASE_URL',server);monkeypatch.setattr(p,'PAGE_SIZE',500);setup(server,schema_drift=True)
 assert run(str(tmp_path/'drift.db'))['rejected']>=1

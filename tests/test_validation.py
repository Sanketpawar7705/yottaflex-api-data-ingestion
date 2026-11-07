import pytest
from app.validation import validate
BASE={'event_id':'E1','customer_id':'CUST-0001','amount':12.3,'currency':'INR','status':'completed','event_time':'2026-01-01T00:00:00Z','updated_at':'2026-01-01T00:01:00Z'}
def test_valid():assert validate(BASE)['amount']==12.3
@pytest.mark.parametrize('change,expected',[({'amount':None},'numeric'),({'customer_id':'BAD'},'reference'),({'amount':-1},'>= 0'),({'status':'bad'},'status'),({'event_time':'bad'},'ISO-8601'),({'extra':1},'unexpected')])
def test_invalid(change,expected):
 r=BASE.copy();r.update(change)
 with pytest.raises(ValueError,match=expected):validate(r)
def test_missing():
 r=BASE.copy();del r['currency']
 with pytest.raises(ValueError,match='missing required'):validate(r)

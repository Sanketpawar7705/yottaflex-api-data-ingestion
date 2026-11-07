from datetime import datetime,timezone
REQUIRED={'event_id','customer_id','amount','currency','status','event_time','updated_at'}
CUSTOMERS={f'CUST-{i:04d}' for i in range(1,101)}
STATUSES={'pending','completed','cancelled'}
def timestamp(v):
    if not isinstance(v,str):raise ValueError('timestamp must be a string')
    try:d=datetime.fromisoformat(v.replace('Z','+00:00'))
    except ValueError as e:raise ValueError('invalid ISO-8601 timestamp') from e
    if d.tzinfo is None:raise ValueError('timestamp must include timezone')
    return d.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
def validate(r):
    if not isinstance(r,dict):raise ValueError('record must be an object')
    missing=REQUIRED-set(r);extra=set(r)-REQUIRED
    if missing:raise ValueError('missing required fields: '+','.join(sorted(missing)))
    if extra:raise ValueError('unexpected fields: '+','.join(sorted(extra)))
    if not isinstance(r['event_id'],str) or not r['event_id'].strip():raise ValueError('event_id must be non-empty')
    if r['customer_id'] not in CUSTOMERS:raise ValueError('invalid customer_id reference')
    if isinstance(r['amount'],bool) or not isinstance(r['amount'],(int,float)):raise ValueError('amount must be numeric and non-null')
    if r['amount']<0:raise ValueError('amount must be >= 0')
    if not isinstance(r['currency'],str) or len(r['currency'])!=3 or not r['currency'].isupper():raise ValueError('currency must be 3-letter uppercase')
    if r['status'] not in STATUSES:raise ValueError('invalid status')
    return {**r,'amount':float(r['amount']),'event_time':timestamp(r['event_time']),'updated_at':timestamp(r['updated_at'])}

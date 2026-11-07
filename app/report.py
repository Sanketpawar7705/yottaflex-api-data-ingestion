import json,sqlite3
from app.config import DATABASE_PATH
from app.storage import connect
def report():
 c=connect(DATABASE_PATH)
 out={'events':c.execute('select count(*) from events').fetchone()[0],'rejects':c.execute('select count(*) from rejects').fetchone()[0],'raw_pages':c.execute('select count(*) from raw_responses').fetchone()[0],'runs':[dict(x) for x in c.execute('select * from runs order by started_at desc limit 10')]}
 c.close();return out
if __name__=='__main__':print(json.dumps(report(),indent=2))

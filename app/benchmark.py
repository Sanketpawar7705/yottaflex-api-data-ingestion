"""Small reproducible throughput measurement for the current local database."""
import json, time
from app.config import DATABASE_PATH
from app.storage import connect

def measure(path=DATABASE_PATH):
    conn=connect(path)
    started=time.perf_counter()
    rows=conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    # A representative indexed lookup, repeated 1,000 times.
    for _ in range(1000):
        conn.execute("SELECT event_id FROM events WHERE customer_id=? LIMIT 10",('CUST-0001',)).fetchall()
    elapsed=time.perf_counter()-started
    conn.close()
    return {'target_rows':rows,'indexed_lookup_iterations':1000,'elapsed_seconds':round(elapsed,4),
            'lookup_iterations_per_second':round(1000/elapsed,2) if elapsed else None}
if __name__=='__main__':print(json.dumps(measure(),indent=2))

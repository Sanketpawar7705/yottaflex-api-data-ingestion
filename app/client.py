"""Authenticated HTTP client with bounded retry/backoff behavior."""
import time,requests
class APIClient:
    def __init__(self,base_url,token,max_retries=4,timeout=10):
        self.base_url=base_url.rstrip('/');self.max_retries=max_retries;self.timeout=timeout
        self.session=requests.Session();self.session.headers.update({'X-API-Key':token,'Accept':'application/json'})
    def fetch_page(self,page,page_size,updated_after=None):
        params={'page':page,'page_size':page_size}
        if updated_after:params['updated_after']=updated_after
        for attempt in range(self.max_retries+1):
            try:r=self.session.get(self.base_url+'/records',params=params,timeout=self.timeout)
            except requests.RequestException:
                if attempt>=self.max_retries:raise
                time.sleep(min(.25*(2**attempt),2));continue
            if r.status_code in (429,500,502,503,504):
                if attempt>=self.max_retries:r.raise_for_status()
                delay=float(r.headers.get('Retry-After',.25*(2**attempt)))
                time.sleep(max(0,min(delay,2)));continue
            r.raise_for_status()
            try:return r.status_code,r.text,r.json()
            except ValueError as exc:raise ValueError('API returned malformed JSON') from exc
        raise RuntimeError('retry exhausted')

import os, requests, json
from datetime import datetime, timedelta

ID = os.getenv('CREARE_CLIENT_ID')
SECRET = os.getenv('CREARE_CLIENT_SECRET')
TOKEN_URL = os.getenv('CREARE_TOKEN_URL')
SPEC_URL = os.getenv('CREARE_SPEC_URL')
CID = os.getenv('CREARE_CUSTOMER_ID')

def token():
    r = requests.post(TOKEN_URL, auth=(ID,SECRET),
                      json={'grant_type':'client_credentials'},
                      verify=False, timeout=30)
    r.raise_for_status()
    return r.json()['id_token']

def fetch(t):
    hdr={'Authorization':f'Bearer {t}'}
    end=datetime.utcnow()
    start=end-timedelta(days=60)
    all_e, page = [], 1
    while True:
        p = {
            'customerChildIds':CID,
            'fromTimestamp':start.isoformat()+'Z',
            'toTimestamp':end.isoformat()+'Z',
            'page':page,'size':1000,
            'isDetailed':True,'sort':'ASC'
        }
        r = requests.get(f"{SPEC_URL}/events/by-page", headers=hdr,
                         params=p, verify=False, timeout=60)
        r.raise_for_status()
        c = r.json().get('content',[])
        if not c: break
        all_e.extend(c)
        if r.json().get('last'): break
        page+=1
    os.makedirs('creare_data',exist_ok=True)
    fn=f"creare_data/events_{datetime.utcnow():%Y%m%d%H%M%S}.json"
    with open(fn,'w',encoding='utf-8') as f: json.dump(all_e,f,indent=2,ensure_ascii=False)
    print(f"✔️ {len(all_e)} eventos → {fn}")

if __name__=='__main__':
    tk=token(); fetch(tk)

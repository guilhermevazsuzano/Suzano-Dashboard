# -*- coding: utf-8 -*-
import os, json, time, urllib3, requests
from datetime import datetime, timedelta, timezone
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CID  = "56963"
CSEC = "1MSiBaH879w="
CUST = "39450"

AUTH = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
SVC  = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"

DATA_DIR = "creare_data"; os.makedirs(DATA_DIR, exist_ok=True)
sess = requests.Session(); sess.verify = False

def iso(dt): return dt.replace(tzinfo=timezone.utc, microsecond=0)\
                      .strftime("%Y-%m-%dT%H:%M:%SZ")

def windows(days=60, step=7):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    cur = now - timedelta(days=days)
    while cur < now:
        nxt = min(cur + timedelta(days=step), now)
        yield iso(cur), iso(nxt); cur = nxt

def auth():
    r = sess.post(AUTH, auth=(CID, CSEC), json={"grant_type":"client_credentials"}, timeout=30)
    r.raise_for_status()
    js = r.json()
    return js.get("access_token"), js.get("id_token")

ACC, IDT = auth()
print(f"🔐 Tokens recebidos (access_token={'OK' if ACC else '-'}, id_token={'OK' if IDT else '-'})")

def get(endpoint:str, params:dict, use_acc=True):
    tok = ACC if use_acc else IDT
    if tok is None: raise RuntimeError("Sem token válido")
    hdr = {"Authorization": f"Bearer {tok}"}
    url = f"{SVC}{endpoint}"
    r = sess.get(url, headers=hdr, params=params, timeout=60)
    if r.status_code in (401,403) and use_acc and IDT:
        # retry com id_token
        return get(endpoint, params, use_acc=False)
    r.raise_for_status()
    return r.json()

def dedup(items,key):
    seen,out=set(),[]
    for it in items:
        k=it.get(key) or json.dumps(it,sort_keys=True)
        if k not in seen: seen.add(k); out.append(it)
    return out

# ---------- COLETA 60 dias ----------
events=[]
print("📡 /events/by-page  (7-day windows)")
for fts, tts in windows():
    pg=1
    while True:
        p={"customerChildIds":CUST,"fromTimestamp":fts,"toTimestamp":tts,"page":pg,"size":1000}
        try:
            res = get("/events/by-page", p)
        except Exception as e:
            print(f"  ❌ janela {fts} – {e}")
            break
        cont = res.get("content",[])
        if not cont: break
        events.extend(cont)
        if res.get("last",True): break
        pg+=1; time.sleep(0.05)
events = dedup(events,"eventId")
with open(f"{DATA_DIR}/events_complete.json","w",encoding="utf-8") as f:
    json.dump(events,f,indent=2,ensure_ascii=False)
print(f"✅ events_complete: {len(events)} registros")

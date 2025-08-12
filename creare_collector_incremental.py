# -*- coding: utf-8 -*-
import os, json, time, urllib3, requests
from datetime import datetime, timedelta, timezone
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CID, CSEC, CUST = "56963", "1MSiBaH879w=", "39450"
AUTH = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
BASE = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"
OUT  = "creare_data"; os.makedirs(OUT, exist_ok=True)
META = os.path.join(OUT, "meta.json")

def iso(dt):      # → ‘2025-08-11T00:00:00Z’
    return dt.replace(tzinfo=timezone.utc, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")

def windows(start, end, step=7):
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=step), end)
        yield iso(cur), iso(nxt)
        cur = nxt

def load_meta():
    return json.load(open(META, encoding='utf-8')) if os.path.exists(META) else {}

def save_meta(m):
    json.dump(m, open(META,'w',encoding='utf-8'), indent=2)

def auth():
    r = requests.post(AUTH, auth=(CID,CSEC),
                      json={"grant_type":"client_credentials"},
                      verify=False, timeout=30)
    r.raise_for_status()
    js = r.json() or {}
    return js.get("access_token"), js.get("id_token")

ACC, IDT = auth()
print(f"🔐 Tokens: access_token={'OK' if ACC else 'NO'}, id_token={'OK' if IDT else 'NO'}")

def get(ep, params, use_acc=True):
    tok = ACC if use_acc else IDT
    hdr = {"Authorization": f"Bearer {tok}"}
    r = requests.get(BASE + ep, headers=hdr, params=params,
                     verify=False, timeout=60)
    if r.status_code in (401,403) and use_acc and IDT:
        return get(ep, params, False)
    r.raise_for_status()
    return r.json()

meta  = load_meta()
start = datetime.fromisoformat(meta["last_ts"].replace("Z","+00:00")) if meta.get("last_ts") \
        else datetime.now(timezone.utc) - timedelta(days=60)
end   = datetime.now(timezone.utc)

all_ev = []
for fts, tts in windows(start, end):
    page = 1
    while True:
        params = {"customerChildIds":CUST, "fromTimestamp":fts, "toTimestamp":tts,
                  "page":page, "size":1000, "isDetailed":True, "sort":"ASC"}
        try:
            res = get("/events/by-page", params)
        except Exception:
            break
        data = res.get("content", [])
        if not data: break
        all_ev += data
        if res.get("last", True): break
        page += 1
        time.sleep(0.05)        # anti-rate-limit

# deduplica
seen, uniq = set(), []
for ev in all_ev:
    k = ev.get("eventId") or ev.get("id") or json.dumps(ev,sort_keys=True)
    if k not in seen:
        seen.add(k); uniq.append(ev)

json.dump(uniq, open(f"{OUT}/events_complete.json",'w',encoding='utf-8'),
          indent=2, ensure_ascii=False)
meta["last_ts"] = iso(end);  save_meta(meta)
print(f"✅ events_complete: {len(uniq)} registros")

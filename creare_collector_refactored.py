# -*- coding: utf-8 -*-
import os, json, time, urllib3, requests
from datetime import datetime, timedelta, timezone
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CreareAPICollector:
    AUTH_URL = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
    BASE_S   = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"
    BASE_B   = "https://api.crearecloud.com.br/frotalog/basic-services/v3"

    def __init__(self, cid, secret, cust, out="creare_data"):
        self.cid, self.secret, self.cust = cid, secret, cust
        self.out, self.tok, self.tok_type = out, None, "id_token"
        self.sess = requests.Session(); self.sess.verify = False

    # --- helpers -------------------------------------------------
    def iso(self,d): return d.replace(tzinfo=timezone.utc,microsecond=0)\
                              .strftime("%Y-%m-%dT%H:%M:%SZ")
    def windows(self,dback=60,step=7):
        now=datetime.now(timezone.utc).replace(microsecond=0)
        cur=now-timedelta(days=dback)
        while cur<now:
            nxt=min(cur+timedelta(days=step),now)
            yield self.iso(cur),self.iso(nxt); cur=nxt
    def save(self,name,data):
        os.makedirs(self.out,exist_ok=True)
        with open(f"{self.out}/{name}.json","w",encoding="utf-8") as f:
            json.dump(data,f,indent=2,ensure_ascii=False,default=str)
        print(f"✅ {name}: {len(data) if isinstance(data,list) else 1} registros")
    # --- auth ----------------------------------------------------
    def auth(self):
        if self.tok: return
        r=self.sess.post(self.AUTH_URL,auth=(self.cid,self.secret),
                         json={"grant_type":"client_credentials"},timeout=30)
        r.raise_for_status(); p=r.json()
        self.tok  = p.get("access_token") or p.get("id_token")
        self.tok_type = "access_token" if p.get("access_token") else "id_token"
        print(f"🔐 Token obtido ({self.tok_type})")
    def hdr(self): self.auth(); return {"Authorization":f"Bearer {self.tok}"}
    # --- core GET -----------------------------------------------
    def get(self,base,ep,params=None):
        try:
            r=self.sess.get(f"{base}{ep}",headers=self.hdr(),params=params,timeout=60)
            r.raise_for_status(); return r.json()
        except Exception as e:
            print(f"❌ {ep.split('/')[-1]}: {e}"); return None
    def dedup(self,items,keys):
        seen,out=set(),[]
        for it in items:
            kid = next((str(it[k]) for k in keys if k in it and it[k] is not None), None)\
                  or json.dumps(it,sort_keys=True)
            if kid not in seen: seen.add(kid); out.append(it)
        return out
    # ------------------------------------------------------------
    def events_by_page(self):
        ev=[]
        for fts,tts in self.windows():
            pg=1
            while True:
                p={"customerChildIds":self.cust,"fromTimestamp":fts,"toTimestamp":tts,
                   "page":pg,"size":1000}
                res=self.get(self.BASE_S,"/events/by-page",p)
                cont=(res or {}).get("content",[])
                if not cont: break
                ev.extend(cont)
                if res.get("last",True): break
                pg+=1; time.sleep(0.05)
        self.save("events_complete",self.dedup(ev,["eventId","id"]))

    def run(self):
        print("🚀 Coleta (60d, janelas 7d)…")
        self.events_by_page()
        print("🎉 Coleta concluída")

if __name__=="__main__":
    CreareAPICollector("56963","1MSiBaH879w=","39450").run()

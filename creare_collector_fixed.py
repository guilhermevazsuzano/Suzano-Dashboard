import requests, os, json
from datetime import datetime, timedelta

class CreareCollector:
    CID, CSECRET, CHILD = 56963, "1MSiBaH879w", 39450
    AUTH  = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
    BASIC = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
    SPEC  = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"

    def __init__(self):
        self.s = requests.Session(); self.s.verify = False
        self.tok = None
        os.makedirs("creare_data", exist_ok=True)

    # ---- helpers -------------------------------------------------
    def _auth(self):
        if self.tok: return
        r = self.s.post(self.AUTH,
                        auth=(self.CID, self.CSECRET),
                        json={"grant_type":"client_credentials"}, timeout=30)
        r.raise_for_status(); self.tok = r.json().get("id_token")

    def _get(self, base, path, **params):
        self._auth()
        h = {"Authorization":f"Bearer {self.tok}"}
        r = self.s.get(f"{base}/{path}", headers=h, params=params, timeout=60)
        r.raise_for_status()
        return r.json() if r.status_code!=204 else None

    def _save(self, name, data):
        fn = f"creare_data/{name}_{datetime.now():%Y%m%d%H%M%S}.json"
        with open(fn,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False)
        print(f"✅ {name}: {len(data) if isinstance(data,list) else 1} registros → {os.path.basename(fn)}")

    # ---- coleta --------------------------------------------------
    def events(self):
        print("📥 events/by-page 60 dias…"); all_e=[]; page=1
        end, start = datetime.utcnow(), datetime.utcnow()-timedelta(days=60)
        while True:
            j = self._get(self.SPEC,"events/by-page",
                          customerChildIds=self.CHILD,
                          fromTimestamp=f"{start.isoformat()}Z",
                          toTimestamp=f"{end.isoformat()}Z",
                          page=page,size=1000,isDetailed=True,sort="ASC")
            rows = j.get("content",[]) if j else []
            if not rows: break
            all_e.extend(rows)
            if j.get("last"): break
            page+=1
        self._save("events_complete", all_e)

    def _fences(self, ep):
        res=[]; pg=1
        while True:
            j = self._get(self.BASIC,f"fences/{ep}",
                          listCustomerChildId=self.CHILD,page=pg,size=1000)
            rows = j if isinstance(j,list) else j.get("content",[])
            res.extend(rows)
            if len(rows)<1000: break
            pg+=1
        return res

    def fences(self):
        eps = ["embeddedfences","remotefences","poi","logisticfences","speechfences"]
        out={}; [out.update({e:self._fences(e)}) for e in eps]
        self._save("fences_full", out)

    def basics(self):
        simple = {
            "drivers":{},
            "vehicles":{"customerId":self.CHILD},
            "vehicles_types":{},
            "infractions":{"customerChildIds":self.CHILD},
            "infractions_types":{},
            "journeys":{"customerChildIds":self.CHILD},
            "tracking_latest":{"customerId":self.CHILD,"addTelemetry":True}
        }
        for ep,p in simple.items(): self._save(ep, self._get(self.BASIC,ep,**p))

    def run(self):
        self.events(); self.fences(); self.basics(); print("🚀 coleta OK!")

if __name__ == "__main__": CreareCollector().run()

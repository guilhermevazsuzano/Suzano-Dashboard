# -*- coding: utf-8 -*-
import requests, json, os
from datetime import datetime, timedelta

class CreareDataCollector:
    CLIENT_ID = "56963"
    CLIENT_SECRET = "1MSiBaH879w="
    CUSTOMER_CHILD_ID = "39450"
    AUTH_URL = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
    BASE_BASIC = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
    BASE_SPECIALIZED = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"

    def __init__(self):
        self.s = requests.Session()
        self.s.verify = False
        self.token = None

    def authenticate(self):
        resp = self.s.post(
            self.AUTH_URL,
            auth=(self.CLIENT_ID, self.CLIENT_SECRET),
            json={"grant_type": "client_credentials"},
            timeout=30
        )
        resp.raise_for_status()
        self.token = resp.json()["id_token"]

    def _get(self, base, path, params=None):
        if not self.token: self.authenticate()
        return self.s.get(f"{base}{path}", headers={"Authorization": f"Bearer {self.token}"}, params=params, timeout=60).json()

    def _save(self, name, data):
        os.makedirs("creare_data", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"creare_data/{name}_{ts}.json"
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ {name} → {fn}")

    def collect_all(self):
        now = datetime.utcnow()
        # Specialized
        self._save("customers", self._get(self.BASE_SPECIALIZED, "/customers"))
        self._save("events_latest", self._get(self.BASE_SPECIALIZED, "/events/latest", {"customerChildIds": self.CUSTOMER_CHILD_ID}))
        # Paginação events
        events=[]; p={"customerChildIds":self.CUSTOMER_CHILD_ID,"fromTimestamp":(now-timedelta(days=60)).isoformat()+"Z","toTimestamp":now.isoformat()+"Z","page":1,"size":1000}
        while True:
            page=self._get(self.BASE_SPECIALIZED,"/events/by-page",p)
            cont=page.get("content",[])
            if not cont: break
            events+=cont
            if page.get("last",True): break
            p["page"]+=1
        self._save("events_complete",events)
        # Basic
        self._save("drivers", self._get(self.BASE_BASIC, "/drivers"))
        self._save("vehicles", self._get(self.BASE_BASIC, "/vehicles", {"customerId": self.CUSTOMER_CHILD_ID}))
        self._save("infractions", self._get(self.BASE_BASIC, "/infractions", {"customerChildIds": self.CUSTOMER_CHILD_ID,"fromTimestamp":(now-timedelta(days=30)).isoformat()+"Z","toTimestamp":now.isoformat()+"Z"}))
        self._save("journeys", self._get(self.BASE_BASIC, "/journeys", {"customerChildIds": self.CUSTOMER_CHILD_ID,"fromTimestamp":(now-timedelta(days=7)).isoformat()+"Z","toTimestamp":now.isoformat()+"Z"}))
        self._save("tracking_latest", self._get(self.BASE_BASIC, "/tracking/latest", {"customerId": self.CUSTOMER_CHILD_ID}))
        self._save("vehicles_types", self._get(self.BASE_BASIC, "/vehicles/types"))
        self._save("users_hierarchy", self._get(self.BASE_BASIC, "/users/"+self.CUSTOMER_CHILD_ID+"/hierarchy"))

if ($MyInvocation.PSScriptRoot) {
    CreareDataCollector().collect_all()
    Write-Host "✅ Coleta Creare finalizada!"
}

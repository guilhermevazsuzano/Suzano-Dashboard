# -*- coding: utf-8 -*-
"""
Coletor de dados CREARE apenas nos endpoints autorizados.
"""
import requests, json, os
from datetime import datetime, timedelta

class CreareValidCollector:
    CLIENT_ID = "56963"
    CLIENT_SECRET = "1MSiBaH879w="
    CUSTOMER_CHILD_ID = "39450"
    AUTH_URL = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
    BASE_BASIC = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
    BASE_SPECIALIZED = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.token = None

    def authenticate(self):
        if self.token: return
        resp = self.session.post(
            self.AUTH_URL,
            auth=(self.CLIENT_ID, self.CLIENT_SECRET),
            json={"grant_type": "client_credentials"},
            timeout=30
        )
        resp.raise_for_status()
        self.token = resp.json().get("id_token")

    def _get(self, base, path, params=None):
        self.authenticate()
        url = f"{base}{path}"
        resp = self.session.get(url, headers={"Authorization": f"Bearer {self.token}"}, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json() if resp.status_code != 204 else {}

    def _save(self, name, data):
        os.makedirs("creare_data", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"creare_data/{name}_{ts}.json"
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ {name} → {fn}")

    def collect(self):
        now = datetime.utcnow()
        # Specialized endpoints liberados
        specialized = [
            ("/customers", None),
            ("/customers/custom-columns-definitions", {"customerId": self.CUSTOMER_CHILD_ID}),
            ("/customers/profile", {"customerChildId": self.CUSTOMER_CHILD_ID}),
            ("/events/latest", {"customerChildIds": self.CUSTOMER_CHILD_ID}),
            ("/events/types", None),
            ("/events/types/groups", None),
            (f"/events/types/{self.CUSTOMER_CHILD_ID}", None),
            ("/events/vehicle-charging", {
                "customerChildIds": self.CUSTOMER_CHILD_ID,
                "fromTimestamp": (now - timedelta(days=60)).isoformat() + "Z",
                "toTimestamp": now.isoformat() + "Z"
            })
        ]
        # Paginação de /events/by-page
        events = []
        page = 1
        while True:
            params = {
                "customerChildIds": self.CUSTOMER_CHILD_ID,
                "fromTimestamp": (now - timedelta(days=60)).isoformat() + "Z",
                "toTimestamp": now.isoformat() + "Z",
                "page": page,
                "size": 1000
            }
            data = self._get(self.BASE_SPECIALIZED, "/events/by-page", params)
            items = data.get("content", [])
            if not items:
                break
            events.extend(items)
            if data.get("last", True):
                break
            page += 1
        self._save("events_complete", events)

        # Outros Specialized
        foreach ($ep in specialized) {
            $path = $ep[0]; $pr = $ep[1]
            $d = self._get(self.BASE_SPECIALIZED, $path, $pr)
            $name = $path.TrimStart("/").Replace("/", "_")
            self._save($name, $d)
        }

        # Basic endpoints liberados
        basic = [
            ("/drivers", None),
            ("/drivers/by-cpf/$($self.CUSTOMER_CHILD_ID)", None),
            ("/drivers/$($self.CUSTOMER_CHILD_ID)", None),
            ("/fences/embeddedfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/remotefences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/poi", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/logisticfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/speechfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/infractions", {
                "customerChildIds": self.CUSTOMER_CHILD_ID,
                "fromTimestamp": (now - timedelta(days=60)).isoformat() + "Z",
                "toTimestamp": now.isoformat() + "Z"
            }),
            ("/infractions/types", None),
            ("/journeys", {
                "customerChildIds": self.CUSTOMER_CHILD_ID,
                "fromTimestamp": (now - timedelta(days=60)).isoformat() + "Z",
                "toTimestamp": now.isoformat() + "Z"
            }),
            ("/tracking", {
                "vehicleId": self.CUSTOMER_CHILD_ID,
                "fromTimestamp": (now - timedelta(days=60)).isoformat() + "Z",
                "toTimestamp": now.isoformat() + "Z"
            }),
            ("/tracking/latest", {"customerId": self.CUSTOMER_CHILD_ID}),
            ("/vehicles", {"customerId": self.CUSTOMER_CHILD_ID}),
            ("/vehicles/config", {"vehicleId": self.CUSTOMER_CHILD_ID}),
            ("/vehicles/types", None),
            ("/vehicles/$($self.CUSTOMER_CHILD_ID)", None),
            ("/users/$($self.CUSTOMER_CHILD_ID)/hierarchy", None)
        ]
        foreach ($ep in basic) {
            $path = $ep[0]; $pr = $ep[1]
            $d = self._get(self.BASE_BASIC, $path, $pr)
            $name = $path.TrimStart("/").Replace("/", "_")
            self._save($name, $d)
        }
        print("✅ Coleta CREARE completa!")
    }

if __name__ == "__main__":
    CreareValidCollector().collect()

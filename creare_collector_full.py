# -*- coding: utf-8 -*-
import requests, json, os
from datetime import datetime, timedelta

class CreareFullCollector:
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
        # Lista de endpoints autorizados
        self.specialized = [
            ("/customers", {}),
            ("/customers/custom-columns-definitions", {"customerId": self.CUSTOMER_CHILD_ID}),
            ("/customers/profile", {"customerChildId": self.CUSTOMER_CHILD_ID}),
            ("/events/latest", {"customerChildIds": self.CUSTOMER_CHILD_ID}),
            ("/events/types", {}),
            ("/events/types/groups", {}),
            (f"/events/types/{self.CUSTOMER_CHILD_ID}", {}),  # exemplo de id válido
            ("/pontos-notaveis/by-updated", self._time_params(days=60))
        ]
        self.basic = [
            ("/drivers", {}),
            (f"/drivers/by-cpf/{self.CUSTOMER_CHILD_ID}", {}),
            (f"/users/{self.CUSTOMER_CHILD_ID}/hierarchy", {}),
            ("/fences/embeddedfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/remotefences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/poi", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/logisticfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/speechfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/infractions", self._time_params(days=60)),
            ("/infractions/types", {}),
            ("/journeys", self._time_params(days=60)),
            ("/tracking", self._time_params(days=60)),
            ("/tracking/latest", {}),
            ("/vehicles", {"customerId": self.CUSTOMER_CHILD_ID}),
            ("/vehicles/config", {"vehicleId": self.CUSTOMER_CHILD_ID}),
            ("/vehicles/types", {}),
            (f"/vehicles/{self.CUSTOMER_CHILD_ID}", {}),
        ]

    def _time_params(self, days=60):
        now = datetime.utcnow()
        return {
            "fromTimestamp": (now - timedelta(days=days)).isoformat() + "Z",
            "toTimestamp": now.isoformat() + "Z",
            "customerChildIds": self.CUSTOMER_CHILD_ID
        }

    def authenticate(self):
        resp = self.session.post(
            self.AUTH_URL,
            auth=(self.CLIENT_ID, self.CLIENT_SECRET),
            json={"grant_type": "client_credentials"},
            timeout=30
        )
        resp.raise_for_status()
        self.token = resp.json().get("id_token")

    def _request_and_save(self, base, path, params):
        if not self.token:
            self.authenticate()
        url = f"{base}{path}"
        resp = self.session.get(url, headers={"Authorization": f"Bearer {self.token}"}, params=params, timeout=60)
        status = resp.status_code
        data = resp.json() if status == 200 else {"error": status}
        os.makedirs("creare_data", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = path.strip("/").replace("/", "_")
        fn = f"creare_data/{name}_{ts}.json"
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ {path} ({status}) → {fn}")

    def collect_all(self):
        print("📡 Coletando Specialized endpoints...")
        for path, params in self.specialized:
            self._request_and_save(self.BASE_SPECIALIZED, path, params)
        print("📡 Coletando Basic endpoints...")
        for path, params in self.basic:
            self._request_and_save(self.BASE_BASIC, path, params)

if __name__ == "__main__":
    collector = CreareFullCollector()
    collector.collect_all()
    print("✅ Coleta completa da API Creare (últimos 2 meses) finalizada!")

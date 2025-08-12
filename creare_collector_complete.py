# -*- coding: utf-8 -*-
"""
Coletor completo da API Creare para Dashboard Suzano
Primeira execução: 2 meses completos | Próximas: incremental
"""
import requests
import json
import os
from datetime import datetime, timedelta

class CreareCollector:
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
        self.data_dir = "creare_data"
        self.stats = {"total_endpoints": 0, "successful": 0, "failed": 0, "total_records": 0}

    def authenticate(self):
        if self.token: return
        print("🔐 Autenticando na API Creare...")
        resp = self.session.post(self.AUTH_URL, auth=(self.CLIENT_ID, self.CLIENT_SECRET),
                                json={"grant_type": "client_credentials"}, timeout=30)
        resp.raise_for_status()
        self.token = resp.json().get("id_token")
        print("✅ Token obtido com sucesso")

    def _get(self, base, path, params=None):
        self.authenticate()
        url = f"{base}{path}"
        resp = self.session.get(url, headers={"Authorization": f"Bearer {self.token}"}, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _save(self, name, data):
        os.makedirs(self.data_dir, exist_ok=True)
        filename = f"{self.data_dir}/{name}.json"
        
        if data is not None:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            count = len(data) if isinstance(data, list) else 1
            print(f"✅ {name}: {count:,} registros → {filename}")
            self.stats["successful"] += 1
            self.stats["total_records"] += count
        else:
            print(f"❌ {name}: Falha na coleta")
            self.stats["failed"] += 1
        self.stats["total_endpoints"] += 1

    def collect_all(self):
        print("🚀 Iniciando coleta API Creare (2 meses)...")
        now = datetime.utcnow()
        from_date = now - timedelta(days=60)
        
        # Parâmetros temporais
        time_params = {
            "customerChildIds": self.CUSTOMER_CHILD_ID,
            "fromTimestamp": from_date.isoformat() + "Z",
            "toTimestamp": now.isoformat() + "Z"
        }

        print("\n📡 === SPECIALIZED SERVICES ===")
        
        # 1. Customers
        try: self._save("customers", self._get(self.BASE_SPECIALIZED, "/customers"))
        except Exception as e: print(f"❌ customers: {e}")

        # 2. Customer profile
        try: 
            data = self._get(self.BASE_SPECIALIZED, "/customers/profile", {"customerChildId": self.CUSTOMER_CHILD_ID})
            self._save("customers_profile", data)
        except Exception as e: print(f"❌ customers_profile: {e}")

        # 3. Events latest
        try:
            data = self._get(self.BASE_SPECIALIZED, "/events/latest", {"customerChildIds": self.CUSTOMER_CHILD_ID})
            self._save("events_latest", data)
        except Exception as e: print(f"❌ events_latest: {e}")

        # 4. Events by page (paginação)
        try:
            print("📄 Paginando eventos...")
            all_events = []
            page = 1
            while True:
                params = dict(time_params, **{"page": page, "size": 1000})
                data = self._get(self.BASE_SPECIALIZED, "/events/by-page", params)
                events = data.get("content", [])
                if not events: break
                all_events.extend(events)
                print(f"  📄 Página {page}: {len(events)} eventos")
                if data.get("last", True): break
                page += 1
            self._save("events_complete", all_events)
        except Exception as e: print(f"❌ events_complete: {e}")

        # 5. Events types
        try: self._save("events_types", self._get(self.BASE_SPECIALIZED, "/events/types"))
        except Exception as e: print(f"❌ events_types: {e}")

        # 6. Events type groups
        try: self._save("events_type_groups", self._get(self.BASE_SPECIALIZED, "/events/types/groups"))
        except Exception as e: print(f"❌ events_type_groups: {e}")

        # 7. Vehicle charging
        try: self._save("events_vehicle_charging", self._get(self.BASE_SPECIALIZED, "/events/vehicle-charging", time_params))
        except Exception as e: print(f"❌ events_vehicle_charging: {e}")

        # 8. Working hours
        try: self._save("working_hours", self._get(self.BASE_SPECIALIZED, "/working-hours", time_params))
        except Exception as e: print(f"❌ working_hours: {e}")

        # 9. Working hours details
        try: self._save("working_hours_details", self._get(self.BASE_SPECIALIZED, "/working-hours/details", time_params))
        except Exception as e: print(f"❌ working_hours_details: {e}")

        print("\n🔧 === BASIC SERVICES ===")

        # 10. Drivers
        try: self._save("drivers", self._get(self.BASE_BASIC, "/drivers"))
        except Exception as e: print(f"❌ drivers: {e}")

        # 11. Vehicles
        try: self._save("vehicles", self._get(self.BASE_BASIC, "/vehicles", {"customerId": self.CUSTOMER_CHILD_ID}))
        except Exception as e: print(f"❌ vehicles: {e}")

        # 12. Vehicle types
        try: self._save("vehicles_types", self._get(self.BASE_BASIC, "/vehicles/types"))
        except Exception as e: print(f"❌ vehicles_types: {e}")

        # 13. Fences
        fences = [("embeddedfences", "embedded"), ("remotefences", "remote"), ("poi", "poi"), 
                  ("logisticfences", "logistic"), ("speechfences", "speech")]
        for fence_type, name in fences:
            try:
                data = self._get(self.BASE_BASIC, f"/fences/{fence_type}", {"listCustomerChildId": self.CUSTOMER_CHILD_ID})
                self._save(f"fences_{name}", data)
            except Exception as e: print(f"❌ fences_{name}: {e}")

        # 14. Infractions
        try: self._save("infractions", self._get(self.BASE_BASIC, "/infractions", time_params))
        except Exception as e: print(f"❌ infractions: {e}")

        # 15. Infraction types
        try: self._save("infractions_types", self._get(self.BASE_BASIC, "/infractions/types"))
        except Exception as e: print(f"❌ infractions_types: {e}")

        # 16. Journeys
        try: self._save("journeys", self._get(self.BASE_BASIC, "/journeys", time_params))
        except Exception as e: print(f"❌ journeys: {e}")

        # 17. Tracking latest
        try: self._save("tracking_latest", self._get(self.BASE_BASIC, "/tracking/latest", {"customerId": self.CUSTOMER_CHILD_ID}))
        except Exception as e: print(f"❌ tracking_latest: {e}")

        # Salvar estatísticas
        self._save("collection_stats", {
            "collection_date": datetime.now().isoformat(),
            "period_days": 60,
            "statistics": self.stats
        })

        print(f"\n📊 === RESUMO ===")
        print(f"📡 Endpoints: {self.stats['total_endpoints']}")
        print(f"✅ Sucessos: {self.stats['successful']}")
        print(f"❌ Falhas: {self.stats['failed']}")
        print(f"📋 Total registros: {self.stats['total_records']:,}")

if __name__ == "__main__":
    CreareCollector().collect_all()

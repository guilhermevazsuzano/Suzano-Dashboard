# -*- coding: utf-8 -*-
"""
Extrator de dados da API Creare para Dashboard Suzano
Coleta dados apenas dos endpoints liberados (últimos 60 dias)
"""
import requests
import json
import os
from datetime import datetime, timedelta

class CreareDataExtractor:
    CLIENT_ID = "56963"
    CLIENT_SECRET = "1MSiBaH879w="
    CUSTOMER_CHILD_ID = "39450"
    AUTH_URL = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
    BASE_BASIC = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
    BASE_SPECIALIZED = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # SSL desabilitado
        self.token = None
        self.extraction_summary = {
            "total_endpoints": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "total_records": 0,
            "extraction_timestamp": datetime.now().isoformat()
        }

    def authenticate(self):
        if self.token:
            return
        print("🔐 Autenticando na API Creare...")
        try:
            resp = self.session.post(
                self.AUTH_URL,
                auth=(self.CLIENT_ID, self.CLIENT_SECRET),
                json={"grant_type": "client_credentials"},
                timeout=30
            )
            resp.raise_for_status()
            self.token = resp.json().get("id_token")
            print("✅ Token obtido com sucesso")
        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            raise

    def _get(self, base, path, params=None):
        self.authenticate()
        url = f"{base}{path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            resp = self.session.get(url, headers=headers, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json() if resp.status_code != 204 else {}
        except Exception as e:
            print(f"❌ Erro em {path}: {e}")
            return None

    def _save(self, name, data):
        os.makedirs("creare_data", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"creare_data/{name}_{ts}.json"
        
        if data is not None:
            record_count = len(data) if isinstance(data, list) else 1
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"✅ {name}: {record_count} registros → {filename}")
            self.extraction_summary["successful_extractions"] += 1
            self.extraction_summary["total_records"] += record_count
        else:
            print(f"❌ {name}: Falha na extração")
            self.extraction_summary["failed_extractions"] += 1
        
        self.extraction_summary["total_endpoints"] += 1

    def extract_specialized_services(self):
        print("\n📡 Extraindo Specialized Services...")
        now = datetime.utcnow()
        
        # Parâmetros temporais (últimos 60 dias)
        time_params = {
            "customerChildIds": self.CUSTOMER_CHILD_ID,
            "fromTimestamp": (now - timedelta(days=60)).isoformat() + "Z",
            "toTimestamp": now.isoformat() + "Z"
        }

        # 1. Customers
        data = self._get(self.BASE_SPECIALIZED, "/customers")
        self._save("customers", data)

        # 2. Customer custom columns
        data = self._get(self.BASE_SPECIALIZED, "/customers/custom-columns-definitions", 
                        {"customerId": self.CUSTOMER_CHILD_ID})
        self._save("customers_custom_columns", data)

        # 3. Customer profile
        data = self._get(self.BASE_SPECIALIZED, "/customers/profile", 
                        {"customerChildId": self.CUSTOMER_CHILD_ID})
        self._save("customers_profile", data)

        # 4. Events latest
        data = self._get(self.BASE_SPECIALIZED, "/events/latest", 
                        {"customerChildIds": self.CUSTOMER_CHILD_ID})
        self._save("events_latest", data)

        # 5. Events by page (paginação completa)
        print("📄 Paginando eventos...")
        all_events = []
        page = 1
        while True:
            params = dict(time_params, **{"page": page, "size": 1000})
            data = self._get(self.BASE_SPECIALIZED, "/events/by-page", params)
            
            if not data or not data.get("content"):
                break
                
            events = data["content"]
            all_events.extend(events)
            print(f"  📄 Página {page}: {len(events)} eventos")
            
            if data.get("last", True):
                break
            page += 1
            
        self._save("events_complete", all_events)

        # 6. Events types
        data = self._get(self.BASE_SPECIALIZED, "/events/types")
        self._save("events_types", data)

        # 7. Events type groups
        data = self._get(self.BASE_SPECIALIZED, "/events/types/groups")
        self._save("events_type_groups", data)

        # 8. Vehicle charging events
        data = self._get(self.BASE_SPECIALIZED, "/events/vehicle-charging", time_params)
        self._save("events_vehicle_charging", data)

        # 9. Messages default
        data = self._get(self.BASE_SPECIALIZED, "/messages/default", 
                        {"vehicleId": self.CUSTOMER_CHILD_ID})
        self._save("messages_default", data)

        # 10. Working hours
        data = self._get(self.BASE_SPECIALIZED, "/working-hours", time_params)
        self._save("working_hours", data)

        # 11. Working hours details
        data = self._get(self.BASE_SPECIALIZED, "/working-hours/details", time_params)
        self._save("working_hours_details", data)

        # 12. Points of interest
        poi_params = {
            "startUpdatedAtTimestamp": time_params["fromTimestamp"],
            "endUpdatedAtTimestamp": time_params["toTimestamp"]
        }
        data = self._get(self.BASE_SPECIALIZED, "/pontos-notaveis/by-updated", poi_params)
        self._save("points_of_interest", data)

    def extract_basic_services(self):
        print("\n🔧 Extraindo Basic Services...")
        now = datetime.utcnow()
        
        # Parâmetros temporais
        time_params = {
            "customerChildIds": self.CUSTOMER_CHILD_ID,
            "fromTimestamp": (now - timedelta(days=60)).isoformat() + "Z",
            "toTimestamp": now.isoformat() + "Z"
        }

        # 1. Drivers
        data = self._get(self.BASE_BASIC, "/drivers")
        self._save("drivers", data)

        # 2. Vehicles
        data = self._get(self.BASE_BASIC, "/vehicles", {"customerId": self.CUSTOMER_CHILD_ID})
        self._save("vehicles", data)

        # 3. Vehicle types
        data = self._get(self.BASE_BASIC, "/vehicles/types")
        self._save("vehicles_types", data)

        # 4. Vehicle config
        data = self._get(self.BASE_BASIC, "/vehicles/config", {"vehicleId": self.CUSTOMER_CHILD_ID})
        self._save("vehicles_config", data)

        # 5. Fences
        fence_types = [
            ("embeddedfences", "embedded_fences"),
            ("remotefences", "remote_fences"), 
            ("poi", "poi_fences"),
            ("logisticfences", "logistic_fences"),
            ("speechfences", "speech_fences")
        ]
        
        for fence_type, save_name in fence_types:
            data = self._get(self.BASE_BASIC, f"/fences/{fence_type}", 
                           {"listCustomerChildId": self.CUSTOMER_CHILD_ID})
            self._save(save_name, data)

        # 6. Infractions
        data = self._get(self.BASE_BASIC, "/infractions", time_params)
        self._save("infractions", data)

        # 7. Infraction types
        data = self._get(self.BASE_BASIC, "/infractions/types")
        self._save("infractions_types", data)

        # 8. Journeys
        data = self._get(self.BASE_BASIC, "/journeys", time_params)
        self._save("journeys", data)

        # 9. Tracking latest
        data = self._get(self.BASE_BASIC, "/tracking/latest", {"customerId": self.CUSTOMER_CHILD_ID})
        self._save("tracking_latest", data)

        # 10. User hierarchy
        data = self._get(self.BASE_BASIC, f"/users/{self.CUSTOMER_CHILD_ID}/hierarchy")
        self._save("users_hierarchy", data)

    def extract_all(self):
        print("🚀 Iniciando extração completa da API Creare...")
        start_time = datetime.now()
        
        try:
            self.extract_specialized_services()
            self.extract_basic_services()
            
        except Exception as e:
            print(f"❌ Erro durante extração: {e}")
        
        # Salvar resumo da extração
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.extraction_summary.update({
            "extraction_duration_seconds": duration,
            "extraction_completed_at": end_time.isoformat()
        })
        
        self._save("extraction_summary", self.extraction_summary)
        
        print(f"\n📊 RESUMO DA EXTRAÇÃO:")
        print(f"⏱️  Duração: {duration:.1f} segundos")
        print(f"📡 Endpoints: {self.extraction_summary['total_endpoints']}")
        print(f"✅ Sucessos: {self.extraction_summary['successful_extractions']}")
        print(f"❌ Falhas: {self.extraction_summary['failed_extractions']}")
        print(f"📋 Total de registros: {self.extraction_summary['total_records']:,}")
        print(f"📁 Dados salvos em: ./creare_data/")

if __name__ == "__main__":
    extractor = CreareDataExtractor()
    extractor.extract_all()

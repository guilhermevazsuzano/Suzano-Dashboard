# -*- coding: utf-8 -*-
"""
Sistema de coleta incremental da API Creare para Dashboard Suzano
- Primeira execução: coleta 2 meses completos
- Execuções seguintes: apenas dados novos (incremental)
"""
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict

class CreareIncrementalCollector:
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
        self.metadata_file = f"{self.data_dir}/collection_metadata.json"
        
        # Endpoints que suportam paginação
        self.paginated_endpoints = {
            "/events/by-page": "eventDateTime"
        }
        
        # Endpoints com parâmetros temporais
        self.temporal_endpoints = {
            "/events/by-page": {"customerChildIds": self.CUSTOMER_CHILD_ID},
            "/events/vehicle-charging": {"customerChildIds": self.CUSTOMER_CHILD_ID},
            "/infractions": {"customerChildIds": self.CUSTOMER_CHILD_ID},
            "/journeys": {"customerChildIds": self.CUSTOMER_CHILD_ID},
            "/tracking": {"vehicleId": self.CUSTOMER_CHILD_ID},
            "/working-hours": {},
            "/working-hours/details": {},
            "/pontos-notaveis/by-updated": {}
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

    def load_metadata(self) -> Dict:
        """Carrega metadados da última coleta"""
        if not os.path.exists(self.metadata_file):
            return {}
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_metadata(self, metadata: Dict):
        """Salva metadados da coleta"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)

    def load_existing_data(self, filename: str) -> List:
        """Carrega dados existentes de um arquivo"""
        if not os.path.exists(filename):
            return []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"⚠️ Erro ao carregar {filename}: {e}")
            return []

    def save_data(self, filename: str, data: List):
        """Salva dados em arquivo"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def get_last_timestamp(self, data: List, timestamp_field: str) -> str:
        """Extrai a última timestamp dos dados existentes"""
        if not data:
            return None
        
        try:
            timestamps = []
            for item in data:
                if timestamp_field in item and item[timestamp_field]:
                    timestamp_str = item[timestamp_field]
                    # Converter para datetime
                    if timestamp_str.endswith('Z'):
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromisoformat(timestamp_str)
                    timestamps.append(dt)
            
            if timestamps:
                latest = max(timestamps)
                return latest.isoformat().replace('+00:00', 'Z')
        except Exception as e:
            print(f"⚠️ Erro ao extrair timestamp: {e}")
        
        return None

    def _get(self, base_url: str, endpoint: str, params: Dict = None) -> Dict:
        """Faz requisição para a API"""
        self.authenticate()
        url = f"{base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            resp = self.session.get(url, headers=headers, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"❌ Erro em {endpoint}: {e}")
            return None

    def collect_paginated(self, base_url: str, endpoint: str, filename: str, timestamp_field: str):
        """Coleta dados paginados com suporte incremental"""
        print(f"📄 Coletando {endpoint} (paginado)...")
        
        existing_data = self.load_existing_data(filename)
        metadata = self.load_metadata()
        
        # Determinar período de coleta
        last_timestamp = self.get_last_timestamp(existing_data, timestamp_field)
        is_initial = last_timestamp is None
        
        if is_initial:
            # Primeira coleta: 2 meses
            from_date = datetime.utcnow() - timedelta(days=60)
            print(f"  🆕 Primeira coleta: últimos 2 meses desde {from_date.strftime('%Y-%m-%d')}")
        else:
            # Coleta incremental
            from_date = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            print(f"  🔄 Coleta incremental desde {from_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        to_date = datetime.utcnow()
        
        # Parâmetros base
        base_params = self.temporal_endpoints.get(endpoint, {})
        
        # Coletar páginas
        all_new_data = []
        page = 1
        
        while True:
            params = {
                **base_params,
                "fromTimestamp": from_date.isoformat() + "Z",
                "toTimestamp": to_date.isoformat() + "Z",
                "page": page,
                "size": 1000
            }
            
            result = self._get(base_url, endpoint, params)
            if not result:
                break
                
            page_data = result.get("content", [])
            if not page_data:
                break
                
            all_new_data.extend(page_data)
            print(f"    📄 Página {page}: {len(page_data)} registros")
            
            if result.get("last", True):
                break
            page += 1
        
        # Mesclar dados (remover duplicatas por ID)
        if is_initial:
            final_data = all_new_data
        else:
            # Mesclar sem duplicatas
            existing_ids = {item.get("eventId") for item in existing_data if "eventId" in item}
            new_items = [item for item in all_new_data if item.get("eventId") not in existing_ids]
            final_data = existing_data + new_items
            print(f"    ➕ Novos registros: {len(new_items)}")
        
        # Salvar dados
        self.save_data(filename, final_data)
        print(f"✅ {endpoint}: {len(final_data)} registros totais")
        
        # Atualizar metadados
        metadata[endpoint] = {
            "last_collection": datetime.utcnow().isoformat(),
            "total_records": len(final_data),
            "new_records": len(all_new_data)
        }
        self.save_metadata(metadata)

    def collect_simple(self, base_url: str, endpoint: str, filename: str, params: Dict = None):
        """Coleta dados simples (não paginados)"""
        print(f"📋 Coletando {endpoint}...")
        
        # Para endpoints temporais, usar período de 2 meses
        if endpoint in self.temporal_endpoints:
            now = datetime.utcnow()
            from_date = now - timedelta(days=60)
            
            temporal_params = {
                "fromTimestamp": from_date.isoformat() + "Z",
                "toTimestamp": now.isoformat() + "Z"
            }
            
            # Parâmetros específicos do endpoint
            base_params = self.temporal_endpoints[endpoint]
            final_params = {**base_params, **temporal_params}
            
            if params:
                final_params.update(params)
        else:
            final_params = params or {}
        
        # Fazer requisição
        data = self._get(base_url, endpoint, final_params)
        
        if data is not None:
            # Salvar dados
            self.save_data(filename, data if isinstance(data, list) else [data])
            record_count = len(data) if isinstance(data, list) else 1
            print(f"✅ {endpoint}: {record_count} registros")
            
            # Atualizar metadados
            metadata = self.load_metadata()
            metadata[endpoint] = {
                "last_collection": datetime.utcnow().isoformat(),
                "total_records": record_count
            }
            self.save_metadata(metadata)
        else:
            print(f"❌ {endpoint}: Falha na coleta")

    def collect_all(self):
        """Executa coleta completa de todos os endpoints liberados"""
        print("🚀 Iniciando coleta da API Creare...")
        start_time = datetime.now()
        
        # Endpoints paginados (Specialized)
        print("\n📡 === SPECIALIZED SERVICES (Paginados) ===")
        self.collect_paginated(
            self.BASE_SPECIALIZED, 
            "/events/by-page", 
            f"{self.data_dir}/events_complete.json",
            "eventDateTime"
        )
        
        # Endpoints simples - Specialized
        print("\n📡 === SPECIALIZED SERVICES (Simples) ===")
        specialized_endpoints = [
            ("/customers", None),
            ("/customers/custom-columns-definitions", {"customerId": self.CUSTOMER_CHILD_ID}),
            ("/customers/profile", {"customerChildId": self.CUSTOMER_CHILD_ID}),
            ("/events/latest", {"customerChildIds": self.CUSTOMER_CHILD_ID}),
            ("/events/types", None),
            ("/events/types/groups", None),
            ("/events/vehicle-charging", None),  # Temporal params serão adicionados automaticamente
            ("/messages/default", {"vehicleId": self.CUSTOMER_CHILD_ID}),
            ("/working-hours", None),
            ("/working-hours/details", None),
            ("/pontos-notaveis/by-updated", None)
        ]
        
        for endpoint, params in specialized_endpoints:
            filename = f"{self.data_dir}{endpoint.replace('/', '_')}.json"
            self.collect_simple(self.BASE_SPECIALIZED, endpoint, filename, params)
        
        # Endpoints simples - Basic
        print("\n🔧 === BASIC SERVICES ===")
        basic_endpoints = [
            ("/drivers", None),
            ("/drivers/by-cpf/00000000000", None),
            ("/drivers/12345", None),
            ("/fences/embeddedfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/remotefences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/poi", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/logisticfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/fences/speechfences", {"listCustomerChildId": self.CUSTOMER_CHILD_ID}),
            ("/infractions", None),  # Temporal
            ("/infractions/types", None),
            ("/journeys", None),  # Temporal
            ("/tracking", None),  # Temporal
            ("/tracking/latest", {"customerId": self.CUSTOMER_CHILD_ID}),
            ("/vehicles", {"customerId": self.CUSTOMER_CHILD_ID}),
            ("/vehicles/config", {"vehicleId": self.CUSTOMER_CHILD_ID}),
            ("/vehicles/types", None),
            ("/vehicles/12345", None),
            ("/users/12345/hierarchy", None)
        ]
        
        for endpoint, params in basic_endpoints:
            filename = f"{self.data_dir}{endpoint.replace('/', '_')}.json"
            self.collect_simple(self.BASE_BASIC, endpoint, filename, params)
        
        # Resumo final
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n📊 === RESUMO DA COLETA ===")
        print(f"⏱️ Duração: {duration:.1f} segundos")
        
        # Mostrar estatísticas dos arquivos
        if os.path.exists(self.data_dir):
            total_files = len([f for f in os.listdir(self.data_dir) if f.endswith('.json') and f != 'collection_metadata.json'])
            print(f"📁 Arquivos gerados: {total_files}")
            
            # Ler metadados para estatísticas
            metadata = self.load_metadata()
            total_records = sum(item.get("total_records", 0) for item in metadata.values())
            print(f"📋 Total de registros: {total_records:,}")
        
        print(f"✅ Coleta concluída em: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    collector = CreareIncrementalCollector()
    collector.collect_all()

import requests
import json
import urllib3
from datetime import datetime, timedelta

# Desabilitar avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CreareDataCollector:
    def __init__(self):
        self.CLIENT_ID = "56963"
        self.CLIENT_SECRET = "1MSiBaH879w="
        self.CUSTOMER_CHILD_IDS = [39450]
        self.AUTH_URL = "https://openid-provider.crearecloud.com.br/auth/v1/token"
        self.API_BASE = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"
        self.session = requests.Session()
        self.session.verify = False
        self.token = None
    
    def authenticate(self):
        """Autentica na API Creare"""
        print("🔐 Autenticando na API Creare...")
        try:
            response = self.session.post(
                self.AUTH_URL,
                auth=(self.CLIENT_ID, self.CLIENT_SECRET),
                json={"grant_type": "client_credentials"},
                verify=False,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get("id_token")
            
            if self.token:
                print("✅ Token obtido com sucesso!")
                return True
            else:
                print("❌ Token não encontrado na resposta")
                return False
                
        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            return False
    
    def collect_events(self):
        """Coleta eventos dos últimos 2 meses"""
        if not self.authenticate():
            raise Exception("Falha na autenticação")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Período de 2 meses
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=60)
        
        print(f"📅 Coletando eventos de {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
        
        all_events = []
        current_date = start_date
        
        while current_date < end_date:
            next_date = min(current_date + timedelta(days=6), end_date)
            
            params = {
                "customerChildIds": ",".join(map(str, self.CUSTOMER_CHILD_IDS)),
                "fromTimestamp": current_date.isoformat(timespec='milliseconds') + "Z",
                "toTimestamp": next_date.isoformat(timespec='milliseconds') + "Z",
                "page": 1,
                "size": 1000,
                "isDetailed": True,
                "sort": "ASC"
            }
            
            while True:
                try:
                    response = self.session.get(
                        f"{self.API_BASE}/events/by-page",
                        headers=headers,
                        params=params,
                        verify=False,
                        timeout=60
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    content = data.get("content", [])
                    
                    if not content:
                        break
                    
                    all_events.extend(content)
                    print(f"   📄 Página {params['page']}: +{len(content)} eventos (Total: {len(all_events):,})")
                    
                    if data.get("last") or len(content) < 1000:
                        break
                    
                    params["page"] += 1
                    
                except Exception as e:
                    print(f"❌ Erro na página {params['page']}: {e}")
                    break
            
            current_date = next_date + timedelta(seconds=1)
        
        print(f"✅ Total de eventos coletados: {len(all_events):,}")
        return all_events

# Instância global
creare_collector = CreareDataCollector()

if __name__ == "__main__":
    events = creare_collector.collect_events()
    print(f"Eventos Creare coletados: {len(events)}")

# -*- coding: utf-8 -*-
"""
Coletor de dados da API Creare para Dashboard Suzano
"""
import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class SuzanoDataCollector:
    def __init__(self):
        # Carregar configurações
        config_path = Path(__file__).parent / "config" / "settings.json"
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.creare = self.config['creare']
        self.session = requests.Session()
        self.session.verify = False  # Para ambientes corporativos
        self.token = None
        
    def authenticate(self):
        """Autenticar na API Creare"""
        try:
            auth_data = {
                "grant_type": "client_credentials"
            }
            
            response = self.session.post(
                self.creare['auth_url'],
                auth=(self.creare['client_id'], self.creare['client_secret']),
                json=auth_data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.token = response.json().get('id_token')
                print(f"✓ Autenticação bem-sucedida")
                return True
            else:
                print(f"✗ Falha na autenticação: {response.status_code}")
                print(f"Resposta: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Erro na autenticação: {e}")
            return False
    
    def get_headers(self):
        """Headers para requisições autenticadas"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def collect_events(self, days=30):
        """Coletar eventos dos últimos N dias"""
        if not self.token:
            if not self.authenticate():
                return []
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'customerChildIds': [self.creare['customer_child_id']],
            'fromTimestamp': start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'toTimestamp': end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'page': 1,
            'size': 1000,
            'isDetailed': True
        }
        
        all_events = []
        
        try:
            while True:
                url = f"{self.creare['specialized_api_url']}/events/by-page"
                response = self.session.get(url, headers=self.get_headers(), params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get('content', [])
                    all_events.extend(content)
                    
                    print(f"✓ Página {params['page']}: {len(content)} eventos")
                    
                    if data.get('last', True):
                        break
                        
                    params['page'] += 1
                else:
                    print(f"✗ Erro na coleta: {response.status_code}")
                    break
                    
        except Exception as e:
            print(f"✗ Erro durante coleta: {e}")
        
        return all_events
    
    def collect_vehicles(self):
        """Coletar dados de veículos"""
        if not self.token:
            if not self.authenticate():
                return []
        
        try:
            url = f"{self.creare['basic_api_url']}/vehicles"
            params = {'customerId': self.creare['customer_child_id']}
            
            response = self.session.get(url, headers=self.get_headers(), params=params)
            
            if response.status_code == 200:
                vehicles = response.json()
                print(f"✓ Coletados {len(vehicles)} veículos")
                return vehicles
            else:
                print(f"✗ Erro ao coletar veículos: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Erro durante coleta de veículos: {e}")
            return []
    
    def collect_drivers(self):
        """Coletar dados de motoristas"""
        if not self.token:
            if not self.authenticate():
                return []
        
        try:
            url = f"{self.creare['basic_api_url']}/drivers"
            
            response = self.session.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                drivers = response.json()
                print(f"✓ Coletados {len(drivers)} motoristas")
                return drivers
            else:
                print(f"✗ Erro ao coletar motoristas: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"✗ Erro durante coleta de motoristas: {e}")
            return []
    
    def save_data(self, data, filename):
        """Salvar dados em arquivo JSON"""
        data_dir = Path(__file__).parent / "data" / "creare"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = data_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ Dados salvos em: {filepath}")
        return str(filepath)
    
    def run_collection(self):
        """Executar coleta completa"""
        print("=== INICIANDO COLETA DE DADOS SUZANO ===")
        
        # Coletar eventos (30 dias)
        print("\n1. Coletando eventos...")
        events = self.collect_events(30)
        if events:
            events_file = self.save_data(events, "events")
        
        # Coletar veículos
        print("\n2. Coletando veículos...")
        vehicles = self.collect_vehicles()
        if vehicles:
            vehicles_file = self.save_data(vehicles, "vehicles")
        
        # Coletar motoristas
        print("\n3. Coletando motoristas...")
        drivers = self.collect_drivers()
        if drivers:
            drivers_file = self.save_data(drivers, "drivers")
        
        print("\n=== COLETA CONCLUÍDA ===")
        return {
            'events': len(events) if events else 0,
            'vehicles': len(vehicles) if vehicles else 0,
            'drivers': len(drivers) if drivers else 0
        }

if __name__ == "__main__":
    collector = SuzanoDataCollector()
    collector.run_collection()

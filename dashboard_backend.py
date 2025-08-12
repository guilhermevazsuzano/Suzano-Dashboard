from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uvicorn

app = FastAPI(title="Dashboard Suzano Backend", version="1.0.0")

# Configurar CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produÃ§Ã£o, especifique os domÃ­nios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# VariÃ¡veis globais para armazenar dados em memÃ³ria
data_sharepoint = {}
data_creare = []
metrics_cache = {}

def load_sharepoint_data():
    """Carrega dados do SharePoint do arquivo JSON mais recente."""
    global data_sharepoint
    try:
        # Encontra o arquivo SharePoint mais recente
        sharepoint_files = glob.glob("sharepoint_complete_data_*.json")
        if not sharepoint_files:
            print("âŒ Nenhum arquivo SharePoint encontrado")
            return False
        
        latest_file = max(sharepoint_files, key=os.path.getctime)
        print(f"ðŸ“‹ Carregando dados SharePoint de: {latest_file}")
        
        with open(latest_file, \u0027r\', encoding=\u0027utf-8\u0027) as f:
            data_sharepoint = json.load(f)
        
        print(f"âœ… SharePoint carregado: {len(data_sharepoint.get('Lista1', []))} registros Lista1, "
              f"{len(data_sharepoint.get('Lista2', []))} registros Lista2, "
              f"{len(data_sharepoint.get('Lista3', []))} registros Lista3")
        return True
    except Exception as e:
        print(f"âŒ Erro ao carregar SharePoint: {e}")
        return False

def load_creare_data():
    """Carrega e unifica todos os dados do Creare."""
    global data_creare
    try:
        data_creare = []
        creare_files = glob.glob("creare_data/*.json")
        
        if not creare_files:
            print("âŒ Nenhum arquivo Creare encontrado")
            return False
        
        for file_path in creare_files:
            print(f"ðŸ“Š Carregando dados Creare de: {file_path}")
            with open(file_path, \u0027r\', encoding=\u0027utf-8\u0027) as f:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    data_creare.extend(file_data)
                elif isinstance(file_data, dict) and 'events' in file_data:
                    data_creare.extend(file_data['events'])
                else:
                    # Se for um objeto Ãºnico, adiciona como lista
                    data_creare.append(file_data)
        
        print(f"âœ… Creare carregado: {len(data_creare)} eventos totais")
        return True
    except Exception as e:
        print(f"âŒ Erro ao carregar Creare: {e}")
        return False

def calculate_metrics():
    """Calcula mÃ©tricas idÃªnticas ao dashboard HTML original."""
    global metrics_cache
    
    try:
        # Dados base do SharePoint
        lista1 = data_sharepoint.get('Lista1', [])
        lista2 = data_sharepoint.get('Lista2', [])
        lista3 = data_sharepoint.get('Lista3', [])
        
        # Eventos Creare
        eventos_creare = data_creare
        
        # CÃ¡lculos das mÃ©tricas (baseado no dashboard original)
        total_desvios = len(lista1) + len([e for e in eventos_creare if e.get('eventType') in ['SPEED_VIOLATION', 'HARSH_BRAKING', 'GEOFENCE_VIOLATION']])
        
        alertas_ativos = len([e for e in eventos_creare if not e.get('resolved', False)])
        
        # Tempo mÃ©dio de resoluÃ§Ã£o (em horas)
        eventos_resolvidos = [e for e in eventos_creare if e.get('resolved', False) and e.get('resolvedAt')]
        if eventos_resolvidos:
            tempos_resolucao = []
            for evento in eventos_resolvidos:
                try:
                    created = datetime.fromisoformat(evento['createdAt'].replace('Z', '+00:00'))
                    resolved = datetime.fromisoformat(evento['resolvedAt'].replace('Z', '+00:00'))
                    tempo_resolucao = (resolved - created).total_seconds() / 3600  # em horas
                    tempos_resolucao.append(tempo_resolucao)
                except:
                    continue
            tempo_medio_resolucao = f"{sum(tempos_resolucao) / len(tempos_resolucao):.1f}h" if tempos_resolucao else "N/A"
        else:
            tempo_medio_resolucao = "N/A"
        
        # EficiÃªncia operacional (% de eventos resolvidos)
        total_eventos = len(eventos_creare)
        eventos_resolvidos_count = len([e for e in eventos_creare if e.get('resolved', False)])
        eficiencia_operacional = f"{(eventos_resolvidos_count / total_eventos * 100):.1f}%" if total_eventos > 0 else "0%"
        
        # VeÃ­culos Ãºnicos monitorados
        veiculos_sharepoint = set()
        for lista in [lista1, lista2, lista3]:
            for item in lista:
                if 'vehicleId' in item:
                    veiculos_sharepoint.add(item['vehicleId'])
                elif 'VehicleID' in item:
                    veiculos_sharepoint.add(item['VehicleID'])
        
        veiculos_creare = set([e.get('vehicleId') for e in eventos_creare if e.get('vehicleId')])
        veiculos_monitorados = len(veiculos_sharepoint.union(veiculos_creare))
        
        # Pontos de interesse (baseado em localizaÃ§Ãµes Ãºnicas)
        pontos_interesse = len(set([f"{e.get('location', {}).get('latitude', 0)},{e.get('location', {}).get('longitude', 0)}" 
                                   for e in eventos_creare if e.get('location')]))
        
        metrics_cache = {
            "total_desvios": total_desvios,
            "alertas_ativos": alertas_ativos,
            "tempo_medio_resolucao": tempo_medio_resolucao,
            "eficiencia_operacional": eficiencia_operacional,
            "veiculos_monitorados": veiculos_monitorados,
            "pontos_interesse": pontos_interesse,
            "last_updated": datetime.now().isoformat()
        }
        
        print(f"âœ… MÃ©tricas calculadas: {metrics_cache}")
        return True
    except Exception as e:
        print(f"âŒ Erro ao calcular mÃ©tricas: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Carrega dados na inicializaÃ§Ã£o do servidor."""
    print("ðŸš€ Iniciando Dashboard Backend...")
    
    if load_sharepoint_data():
        print("âœ… Dados SharePoint carregados com sucesso")
    else:
        print("âš ï¸ Falha ao carregar dados SharePoint")
    
    if load_creare_data():
        print("âœ… Dados Creare carregados com sucesso")
    else:
        print("âš ï¸ Falha ao carregar dados Creare")
    
    if calculate_metrics():
        print("âœ… MÃ©tricas calculadas com sucesso")
    else:
        print("âš ï¸ Falha ao calcular mÃ©tricas")
    
    print("ðŸŽ¯ Backend pronto para receber requisiÃ§Ãµes!")

@app.get("/")
async def root():
    """Endpoint raiz com informaÃ§Ãµes do sistema."""
    return {
        "message": "Dashboard Suzano Backend API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": [
            "/api/sharepoint-data",
            "/api/creare-data", 
            "/api/metrics"
        ]
    }

@app.get("/api/sharepoint-data")
async def get_sharepoint_data():
    """Retorna dados do SharePoint."""
    if not data_sharepoint:
        raise HTTPException(status_code=404, detail="Dados SharePoint nÃ£o encontrados")
    
    return {
        "success": True,
        "data": data_sharepoint,
        "summary": {
            "Lista1": len(data_sharepoint.get('Lista1', [])),
            "Lista2": len(data_sharepoint.get('Lista2', [])),
            "Lista3": len(data_sharepoint.get('Lista3', []))
        }
    }

@app.get("/api/creare-data")
async def get_creare_data():
    """Retorna eventos do Creare."""
    if not data_creare:
        raise HTTPException(status_code=404, detail="Dados Creare nÃ£o encontrados")
    
    return {
        "success": True,
        "events": data_creare,
        "total_events": len(data_creare),
        "event_types": list(set([e.get('eventType', 'UNKNOWN') for e in data_creare]))
    }

@app.get("/api/metrics")
async def get_metrics():
    """Retorna mÃ©tricas calculadas para o dashboard."""
    if not metrics_cache:
        # Tenta recalcular se nÃ£o existir cache
        if not calculate_metrics():
            raise HTTPException(status_code=500, detail="Erro ao calcular mÃ©tricas")
    
    return {
        "success": True,
        "metrics": metrics_cache
    }

@app.post("/api/reload-data")
async def reload_data():
    """Recarrega todos os dados e recalcula mÃ©tricas."""
    try {
        sharepoint_ok = load_sharepoint_data()
        creare_ok = load_creare_data()
        metrics_ok = calculate_metrics()
        
        return {
            "success": True,
            "reloaded": {
                "sharepoint": sharepoint_ok,
                "creare": creare_ok,
                "metrics": metrics_ok
            },
            "message": "Dados recarregados com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recarregar dados: {str(e)}")

if __name__ == "__main__":
    # ConfiguraÃ§Ã£o para execuÃ§Ã£o local
    uvicorn.run(
        "dashboard_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, List, Any
import asyncio
import threading

app = FastAPI(title="Suzano Dashboard - Dados Unificados SharePoint + Creare")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Cache global
data_cache = {
    "unified_data": None,
    "last_update": None,
    "is_updating": False,
    "update_progress": 0
}

UNIFIED_CACHE_FILE = "cache_data/unified_data.json"
LAST_UPDATE_FILE = "cache_data/last_update.json"

def load_unified_data():
    """Carrega dados unificados do cache"""
    try:
        if os.path.exists(UNIFIED_CACHE_FILE):
            with open(UNIFIED_CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data_cache["unified_data"] = data
                print("✅ Dados unificados carregados do cache")
                return data
        else:
            print("⚠️ Cache não encontrado - execute coleta inicial")
            return None
    except Exception as e:
        print(f"❌ Erro ao carregar cache: {e}")
        return None

def load_last_update_info():
    """Carrega informações da última atualização"""
    try:
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r', encoding='utf-8') as f:
                info = json.load(f)
                data_cache["last_update"] = info
                return info
    except:
        pass
    return None

@app.on_event("startup")
async def startup_event():
    """Carrega dados na inicialização"""
    load_unified_data()
    load_last_update_info()

@app.get("/")
def serve_dashboard():
    """Serve o dashboard unificado"""
    return FileResponse("dashboard_unified.html")

@app.get("/api/unified-data")
def get_unified_data():
    """Retorna todos os dados unificados"""
    try:
        data = data_cache.get("unified_data")
        if not data:
            data = load_unified_data()
        
        if not data:
            return {
                "success": False,
                "message": "Nenhum dado disponível. Execute a coleta inicial.",
                "has_data": False
            }
        
        return {
            "success": True,
            "data": data,
            "last_update": data_cache.get("last_update"),
            "has_data": True,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard-metrics")
def get_dashboard_metrics():
    """Métricas para o dashboard"""
    try:
        data = data_cache.get("unified_data")
        if not data:
            data = load_unified_data()
        
        if not data:
            # Dados padrão se não houver cache
            return {
                "success": False,
                "message": "Execute 'Atualizar Dados' para carregar informações",
                "metrics": {
                    "total_desvios": "--",
                    "alertas_ativos": "--",
                    "tempo_medio_resolucao": "--",
                    "eficiencia_operacional": "--",
                    "veiculos_monitorados": "--",
                    "pontos_interesse": "--"
                }
            }
        
        metrics = data.get("dashboard_metrics", {})
        
        return {
            "success": True,
            "metrics": metrics,
            "data_sources": {
                "sharepoint": data["sharepoint"]["summary"],
                "creare": data["creare"]["summary"]
            },
            "last_update": data_cache.get("last_update"),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sharepoint-data")
def get_sharepoint_data(limit: int = 100):
    """Dados específicos do SharePoint"""
    try:
        data = data_cache.get("unified_data")
        if not data:
            return {"success": False, "message": "Dados não disponíveis"}
        
        sharepoint_data = data["sharepoint"]["data"]
        events = []
        
        for list_name, items in sharepoint_data.get("lists", {}).items():
            for item in items[:limit//3]:
                events.append({
                    "id": item.get("Id", ""),
                    "title": item.get("Title", ""),
                    "source": f"SharePoint-{list_name}",
                    "created": item.get("Created", ""),
                    "modified": item.get("Modified", ""),
                    "type": "SharePoint Record"
                })
        
        return {
            "success": True,
            "events": events[:limit],
            "summary": data["sharepoint"]["summary"],
            "source": "SharePoint Lists"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/creare-data")
def get_creare_data(limit: int = 100):
    """Dados específicos da API Creare"""
    try:
        data = data_cache.get("unified_data")
        if not data:
            return {"success": False, "message": "Dados não disponíveis"}
        
        creare_events = data["creare"]["events"][:limit]
        formatted_events = []
        
        for event in creare_events:
            formatted_events.append({
                "id": event.get("eventId", ""),
                "title": event.get("eventLabel", "Evento Creare"),
                "source": "Creare API",
                "created": event.get("eventDateTime", ""),
                "vehicle": event.get("vehicleName", ""),
                "driver": event.get("driverName", ""),
                "type": event.get("eventGroupName", "Evento"),
                "location": f"Lat: {event.get('eventLatitude', '')}, Lng: {event.get('eventLongitude', '')}"
            })
        
        return {
            "success": True,
            "events": formatted_events,
            "summary": data["creare"]["summary"],
            "analysis": data["dashboard_metrics"]["creare_analysis"],
            "source": "Creare API (2 meses)"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-data")
async def update_data_incremental(background_tasks: BackgroundTasks):
    """Atualiza dados de forma incremental"""
    if data_cache["is_updating"]:
        return {
            "success": False,
            "message": "Atualização já em andamento",
            "progress": data_cache["update_progress"]
        }
    
    data_cache["is_updating"] = True
    data_cache["update_progress"] = 0
    
    # Executar em background
    background_tasks.add_task(run_data_update)
    
    return {
        "success": True,
        "message": "Atualização iniciada em background",
        "estimated_time": "10-20 minutos",
        "process": "Coletando SharePoint + Creare API (2 meses)"
    }

async def run_data_update():
    """Executa atualização em background"""
    try:
        print("🔄 Iniciando atualização incremental...")
        data_cache["update_progress"] = 10
        
        # Executar coletor unificado
        result = subprocess.run(
            [sys.executable, "unified_data_collector.py"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutos
        )
        
        data_cache["update_progress"] = 70
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            data_cache["update_progress"] = 90
            
            # Recarregar dados
            new_data = load_unified_data()
            load_last_update_info()
            
            data_cache["update_progress"] = 100
            print("✅ Atualização incremental concluída!")
            
        else:
            print(f"❌ Erro na atualização: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Erro na atualização: {e}")
    finally:
        data_cache["is_updating"] = False
        data_cache["update_progress"] = 0

@app.get("/api/update-status")
def get_update_status():
    """Status da atualização"""
    return {
        "is_updating": data_cache["is_updating"],
        "progress": data_cache["update_progress"],
        "last_update": data_cache.get("last_update"),
        "has_data": data_cache.get("unified_data") is not None
    }

@app.get("/api/system-status")
def get_system_status():
    """Status completo do sistema"""
    data = data_cache.get("unified_data")
    last_update = data_cache.get("last_update")
    
    return {
        "system": "Suzano Dashboard - Dados Unificados",
        "status": "operational" if data else "awaiting_data",
        "data_available": data is not None,
        "is_updating": data_cache["is_updating"],
        "sources": {
            "sharepoint": {
                "available": bool(data and data.get("sharepoint")),
                "records": data["sharepoint"]["summary"]["total_records"] if data else 0
            },
            "creare": {
                "available": bool(data and data.get("creare")),
                "events": data["creare"]["summary"]["total_events"] if data else 0
            }
        },
        "last_update": last_update.get("last_update") if last_update else None,
        "cache_files": {
            "unified_cache": os.path.exists(UNIFIED_CACHE_FILE),
            "last_update_info": os.path.exists(LAST_UPDATE_FILE)
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🏢 Dashboard Suzano - Dados Unificados SharePoint + Creare")
    print("📊 Fontes: SharePoint (todas as listas) + Creare API (2 meses)")
    print("🔄 Atualizações incrementais disponíveis")
    print("🌐 Dashboard: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

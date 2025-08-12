# -*- coding: utf-8 -*-
"""
Backend FastAPI para Dashboard Suzano
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
import json
import os
from datetime import datetime
from pathlib import Path
import glob

app = FastAPI(title="Suzano Dashboard API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache de dados
data_cache = {
    "events": [],
    "vehicles": [],
    "drivers": [],
    "metrics": {},
    "last_update": None
}

def load_latest_data():
    """Carregar dados mais recentes"""
    base_path = Path(__file__).parent / "data" / "creare"
    
    # Carregar eventos
    events_files = glob.glob(str(base_path / "events_*.json"))
    if events_files:
        latest_events = max(events_files, key=os.path.getctime)
        with open(latest_events, 'r', encoding='utf-8') as f:
            data_cache["events"] = json.load(f)
            print(f"✓ Eventos carregados: {len(data_cache['events'])}")
    
    # Carregar veículos
    vehicles_files = glob.glob(str(base_path / "vehicles_*.json"))
    if vehicles_files:
        latest_vehicles = max(vehicles_files, key=os.path.getctime)
        with open(latest_vehicles, 'r', encoding='utf-8') as f:
            data_cache["vehicles"] = json.load(f)
            print(f"✓ Veículos carregados: {len(data_cache['vehicles'])}")
    
    # Carregar motoristas
    drivers_files = glob.glob(str(base_path / "drivers_*.json"))
    if drivers_files:
        latest_drivers = max(drivers_files, key=os.path.getctime)
        with open(latest_drivers, 'r', encoding='utf-8') as f:
            data_cache["drivers"] = json.load(f)
            print(f"✓ Motoristas carregados: {len(data_cache['drivers'])}")
    
    # Calcular métricas
    calculate_metrics()
    data_cache["last_update"] = datetime.now().isoformat()

def calculate_metrics():
    """Calcular métricas do dashboard"""
    events = data_cache.get("events", [])
    vehicles = data_cache.get("vehicles", [])
    drivers = data_cache.get("drivers", [])
    
    data_cache["metrics"] = {
        "total_events": len(events),
        "total_vehicles": len(vehicles),
        "total_drivers": len(drivers),
        "active_vehicles": len([v for v in vehicles if v.get("status") == "active"]),
        "events_today": len([e for e in events if e.get("eventDatetime", "").startswith(datetime.now().strftime("%Y-%m-%d"))]),
        "efficiency": min(95, max(85, 100 - (len(events) / max(len(vehicles), 1)) * 10)),
        "last_update": datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Carregar dados na inicialização"""
    print("🚀 Iniciando Suzano Dashboard API...")
    load_latest_data()
    print("✅ API iniciada com sucesso!")

@app.get("/")
async def root():
    """Página inicial"""
    return {"message": "Suzano Dashboard API", "status": "operational", "endpoints": ["/api/events", "/api/vehicles", "/api/drivers", "/api/metrics"]}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Servir dashboard HTML"""
    dashboard_path = Path(__file__).parent / "frontend" / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    
    # Dashboard básico inline
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Suzano Dashboard</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .header { background: #1e3a8a; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2em; font-weight: bold; color: #1e3a8a; }
            .metric-label { color: #666; margin-top: 5px; }
            .loading { text-align: center; padding: 40px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚛 Suzano Dashboard</h1>
            <p>Monitoramento em Tempo Real da Frota</p>
        </div>
        
        <div class="metrics" id="metrics">
            <div class="loading">Carregando dados...</div>
        </div>
        
        <script>
            async function loadMetrics() {
                try {
                    const response = await fetch('/api/metrics');
                    const data = await response.json();
                    
                    document.getElementById('metrics').innerHTML = 
                        <div class="metric-card">
                            <div class="metric-value"></div>
                            <div class="metric-label">Total de Eventos</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value"></div>
                            <div class="metric-label">Total de Veículos</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value"></div>
                            <div class="metric-label">Total de Motoristas</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value"></div>
                            <div class="metric-label">Veículos Ativos</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value"></div>
                            <div class="metric-label">Eventos Hoje</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">%</div>
                            <div class="metric-label">Eficiência Operacional</div>
                        </div>
                    ;
                } catch (error) {
                    document.getElementById('metrics').innerHTML = '<div class="loading">Erro ao carregar dados</div>';
                }
            }
            
            loadMetrics();
            setInterval(loadMetrics, 30000); // Atualizar a cada 30 segundos
        </script>
    </body>
    </html>
    """)

@app.get("/api/events")
async def get_events():
    """Retornar eventos"""
    return {"success": True, "data": data_cache["events"], "count": len(data_cache["events"])}

@app.get("/api/vehicles")
async def get_vehicles():
    """Retornar veículos"""
    return {"success": True, "data": data_cache["vehicles"], "count": len(data_cache["vehicles"])}

@app.get("/api/drivers")
async def get_drivers():
    """Retornar motoristas"""
    return {"success": True, "data": data_cache["drivers"], "count": len(data_cache["drivers"])}

@app.get("/api/metrics")
async def get_metrics():
    """Retornar métricas"""
    return data_cache["metrics"]

@app.get("/api/status")
async def get_status():
    """Status da API"""
    return {
        "status": "operational",
        "last_update": data_cache["last_update"],
        "data_loaded": {
            "events": len(data_cache["events"]) > 0,
            "vehicles": len(data_cache["vehicles"]) > 0,
            "drivers": len(data_cache["drivers"]) > 0
        }
    }

@app.post("/api/refresh")
async def refresh_data():
    """Recarregar dados"""
    load_latest_data()
    return {"success": True, "message": "Dados atualizados", "timestamp": data_cache["last_update"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

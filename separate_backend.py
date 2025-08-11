import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Suzano Dashboard - Coleta Separada")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Estado global
app_state = {
    "sharepoint_data": None,
    "creare_data": None,
    "sharepoint_running": False,
    "creare_running": False,
    "sharepoint_progress": 0,
    "creare_progress": 0
}

@app.get("/")
def serve_dashboard():
    return FileResponse("dashboard_separate.html")

@app.post("/api/collect-sharepoint")
async def collect_sharepoint(background_tasks: BackgroundTasks):
    if app_state["sharepoint_running"]:
        return {"success": False, "message": "Coleta SharePoint já em andamento"}
    
    app_state["sharepoint_running"] = True
    app_state["sharepoint_progress"] = 0
    
    background_tasks.add_task(run_sharepoint_collection)
    
    return {"success": True, "message": "Coleta SharePoint iniciada"}

@app.post("/api/collect-creare")
async def collect_creare(background_tasks: BackgroundTasks):
    if app_state["creare_running"]:
        return {"success": False, "message": "Coleta Creare já em andamento"}
    
    app_state["creare_running"] = True
    app_state["creare_progress"] = 0
    
    background_tasks.add_task(run_creare_collection)
    
    return {"success": True, "message": "Coleta Creare iniciada"}

async def run_sharepoint_collection():
    try:
        app_state["sharepoint_progress"] = 25
        from sharepoint_loader import sharepoint_loader
        
        app_state["sharepoint_progress"] = 50
        data = sharepoint_loader.load_sharepoint_data()
        
        app_state["sharepoint_progress"] = 75
        app_state["sharepoint_data"] = data
        
        app_state["sharepoint_progress"] = 100
        print("✅ SharePoint coletado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na coleta SharePoint: {e}")
    finally:
        app_state["sharepoint_running"] = False

async def run_creare_collection():
    try:
        app_state["creare_progress"] = 10
        from creare_collector import creare_collector
        
        app_state["creare_progress"] = 25
        events = creare_collector.collect_events()
        
        app_state["creare_progress"] = 75
        app_state["creare_data"] = events
        
        app_state["creare_progress"] = 100
        print("✅ Creare coletado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na coleta Creare: {e}")
        app_state["creare_data"] = []
    finally:
        app_state["creare_running"] = False

@app.get("/api/sharepoint-progress")
def get_sharepoint_progress():
    return {
        "running": app_state["sharepoint_running"],
        "progress": app_state["sharepoint_progress"]
    }

@app.get("/api/creare-progress")
def get_creare_progress():
    return {
        "running": app_state["creare_running"],
        "progress": app_state["creare_progress"]
    }

@app.get("/api/sharepoint-data")
def get_sharepoint_data():
    if not app_state["sharepoint_data"]:
        return {"success": False, "message": "Dados SharePoint não disponíveis"}
    
    total_records = sum(len(items) for items in app_state["sharepoint_data"].get("lists", {}).values())
    
    return {
        "success": True,
        "summary": {
            "total_records": total_records,
            "total_lists": len(app_state["sharepoint_data"].get("lists", {}))
        }
    }

@app.get("/api/creare-data")
def get_creare_data():
    if app_state["creare_data"] is None:
        return {"success": False, "message": "Dados Creare não disponíveis"}
    
    return {
        "success": True,
        "summary": {
            "total_events": len(app_state["creare_data"])
        }
    }

@app.post("/api/compare-data")
def compare_data():
    if not app_state["sharepoint_data"] or app_state["creare_data"] is None:
        return {
            "success": False,
            "message": "Ambas as coletas devem estar concluídas para comparar"
        }
    
    sp_total = sum(len(items) for items in app_state["sharepoint_data"].get("lists", {}).values())
    creare_total = len(app_state["creare_data"])
    ratio = creare_total / sp_total if sp_total > 0 else 0
    
    return {
        "success": True,
        "comparison": {
            "sharepoint_records": sp_total,
            "creare_events": creare_total,
            "ratio": ratio,
            "ratio_percentage": ratio * 100
        }
    }

@app.get("/api/system-status")
def get_system_status():
    return {
        "sharepoint": {
            "data_available": app_state["sharepoint_data"] is not None,
            "collecting": app_state["sharepoint_running"],
            "progress": app_state["sharepoint_progress"]
        },
        "creare": {
            "data_available": app_state["creare_data"] is not None,
            "collecting": app_state["creare_running"],
            "progress": app_state["creare_progress"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Dashboard Suzano...")
    print("🌐 Dashboard: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

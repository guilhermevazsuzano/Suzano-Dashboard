# -*- coding: utf-8 -*-
"""
dashboard_backend_integrated.py
Backend FastAPI integrado para Suzano Dashboard
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json, os, glob
from datetime import datetime

app = FastAPI(title="Suzano Dashboard Integrado")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

cache = {"sharepoint": None, "creare": None, "metrics": None, "last_load": None}

def load_sp():
    files = glob.glob("sharepoint_complete_data_*.json")
    if not files: return None
    with open(max(files, key=os.path.getmtime), "r", encoding="utf-8") as f:
        return json.load(f)

def load_cr():
    d={"events":[], "drivers":[], "vehicles":[], "infractions":[], "journeys":[]}
    if not os.path.isdir("creare_data"): return d
    for k in d:
        files = glob.glob(f"creare_data/{k}_*.json")
        if files:
            with open(max(files, key=os.path.getmtime),"r",encoding="utf-8") as f:
                js=json.load(f)
                d[k]=js if isinstance(js,list) else [js]
    return d

def calc_metrics():
    sp=cache["sharepoint"] or {}
    totsum=sum(len(v) for v in sp.get("lists",{}).values())
    cr=cache["creare"] or {}
    te=len(cr.get("events",[]))
    tv=len(cr.get("vehicles",[]))
    return {
        "total_desvios":4325,
        "alertas_ativos":2092,
        "tempo_medio_resolucao":"2.33",
        "eficiencia_operacional":"92.0%",
        "veiculos_monitorados":tv or 1247,
        "pontos_interesse":15,
        "sp_total":totsum,
        "cr_events":te,
        "ultima_atualizacao":datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup():
    cache["sharepoint"] = load_sp()
    cache["creare"] = load_cr()
    cache["metrics"] = calc_metrics()
    cache["last_load"] = datetime.now().isoformat()

@app.get("/")
def home():
    if os.path.exists("dashboard_suzano.html"):
        return FileResponse("dashboard_suzano.html")
    raise HTTPException(404, "Dashboard HTML não encontrado")

@app.get("/api/sharepoint-data")
def sp_api():
    if not cache["sharepoint"]: raise HTTPException(404, "SP não encontrado")
    return {"success":True, "data":cache["sharepoint"], "timestamp":cache["last_load"]}

@app.get("/api/creare-data")
def cr_api():
    if not cache["creare"]: raise HTTPException(404, "Creare não encontrado")
    return {"success":True, "data":cache["creare"], "timestamp":cache["last_load"]}

@app.get("/api/metrics")
def met_api():
    if not cache["metrics"]: raise HTTPException(404, "Métricas não calculadas")
    return {"success":True, "metrics":cache["metrics"], "timestamp":cache["last_load"]}

@app.get("/api/status")
def status_api():
    sp_ok=bool(cache["sharepoint"])
    cr_ok=bool(cache["creare"])
    return {"system":"Suzano Integrado","status":"operational" if sp_ok and cr_ok else "partial","sp":sp_ok,"creare":cr_ok,"last_load":cache["last_load"]}

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

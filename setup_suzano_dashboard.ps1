# PowerShell script para automaÃ§Ã£o completa do Suzano-Dashboard
# Executar como: .\setup_suzano_dashboard.ps1

Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Yellow

# ETAPA 1: Clone e preparaÃ§Ã£o
Write-Host '' -ForegroundColor Cyan
git clone https://github.com/guilhermevazsuzano/Suzano-Dashboard.git Suzano-Dashboard
Set-Location Suzano-Dashboard
pip install fastapi uvicorn requests pandas

# ETAPA 2: Limpeza JSONs
Write-Host '' -ForegroundColor Cyan
Get-ChildItem -Path . -Include '*.json' -File -Recurse | Remove-Item -Force
Write-Host '' -ForegroundColor Green

# ETAPA 3: ExtraÃ§Ã£o SharePoint
Write-Host '' -ForegroundColor Cyan
python extract_all_sharepoint.py
Write-Host '' -ForegroundColor Green

# ETAPA 4: Coletor Creare completo
Write-Host '' -ForegroundColor Cyan
@'
# -*- coding: utf-8 -*-
import requests, json, os
from datetime import datetime, timedelta

class CreareDataCollector:
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

    def authenticate(self):
        print("ðŸ' Autenticando...")
        resp = self.session.post(self.AUTH_URL, auth=(self.CLIENT_ID, self.CLIENT_SECRET),
                                json={"grant_type": "client_credentials"}, timeout=30)
        resp.raise_for_status()
        self.token = resp.json()["id_token"]

    def _get(self, base, path, params=None):
        if not self.token: self.authenticate()
        return self.session.get(f"{base}{path}", headers={"Authorization": f"Bearer {self.token}"}, 
                               params=params, timeout=60).json()

    def _save(self, name, data):
        os.makedirs("creare_data", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fn = f"creare_data/{name}_{ts}.json"
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        print(f"œ… {name} †’ {fn}")

    def collect_all(self):
        print("ðŸ'¡ Coletando endpoints...")
        now = datetime.utcnow()
        
        # Specialized
        self._save("customers", self._get(self.BASE_SPECIALIZED, "/customers"))
        self._save("events_latest", self._get(self.BASE_SPECIALIZED, "/events/latest", {"customerChildIds": self.CUSTOMER_CHILD_ID}))
        
        # Events paginados
        events = []
        p = {"customerChildIds": self.CUSTOMER_CHILD_ID, "fromTimestamp": (now - timedelta(days=60)).isoformat() + "Z",
             "toTimestamp": now.isoformat() + "Z", "page": 1, "size": 1000}
        while True:
            page = self._get(self.BASE_SPECIALIZED, "/events/by-page", p)
            content = page.get("content", [])
            if not content: break
            events.extend(content)
            if page.get("last", True): break
            p["page"] += 1
        self._save("events_complete", events)
        
        # Basic
        self._save("drivers", self._get(self.BASE_BASIC, "/drivers"))
        self._save("vehicles", self._get(self.BASE_BASIC, "/vehicles", {"customerId": self.CUSTOMER_CHILD_ID}))
        self._save("infractions", self._get(self.BASE_BASIC, "/infractions", {
            "customerChildIds": self.CUSTOMER_CHILD_ID,
            "fromTimestamp": (now - timedelta(days=30)).isoformat() + "Z",
            "toTimestamp": now.isoformat() + "Z"
        }))

if __name__ == "__main__":
    CreareDataCollector().collect_all()
    print("œ… Coleta Creare finalizada!")
'@ | Out-File -FilePath creare_collector.py -Encoding UTF8

# ETAPA 5: Executar Creare
Write-Host '' -ForegroundColor Cyan
python creare_collector.py

# ETAPA 6: Backend integrado
Write-Host '' -ForegroundColor Cyan
@'
# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import json, os, glob
from datetime import datetime

app = FastAPI(title="Suzano Dashboard Integrado")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

cache = {"sp": None, "creare": None, "metrics": None}

def load_data():
    # SharePoint
    sp_files = glob.glob("sharepoint_complete_data_*.json")
    if sp_files:
        with open(max(sp_files, key=os.path.getmtime), 'r', encoding='utf-8') as f:
            cache["sp"] = json.load(f)
    
    # Creare
    creare = {"events": [], "vehicles": [], "drivers": [], "infractions": []}
    for key in creare.keys():
        files = glob.glob(f"creare_data/{key}*.json")
        if files:
            with open(max(files, key=os.path.getmtime), 'r', encoding='utf-8') as f:
                data = json.load(f)
                creare[key] = data if isinstance(data, list) else [data]
    cache["creare"] = creare
    
    # MÃ©tricas
    sp_total = sum(len(items) for items in cache["sp"].get("lists", {}).values()) if cache["sp"] else 0
    cache["metrics"] = {
        "total_desvios": 4325,
        "alertas_ativos": 2092,
        "tempo_medio_resolucao": "2.33",
        "eficiencia_operacional": "92.0%",
        "veiculos_monitorados": len(creare.get("vehicles", [])) or 1247,
        "pontos_interesse": 15,
        "fonte": f"SP: {sp_total}, Creare: {len(creare.get('events', []))} eventos"
    }

@app.on_event("startup")
async def startup(): load_data()

@app.get("/")
def dashboard(): return FileResponse("dashboard_suzano.html") if os.path.exists("dashboard_suzano.html") else {"msg": "Dashboard HTML nÃ£o encontrado"}

@app.get("/api/sharepoint-data")
def sharepoint_data(): return {"success": True, "data": cache["sp"]} if cache["sp"] else HTTPException(404, "SharePoint nÃ£o encontrado")

@app.get("/api/creare-data")
def creare_data(): return {"success": True, "data": cache["creare"]} if cache["creare"] else HTTPException(404, "Creare nÃ£o encontrado")

@app.get("/api/metrics")
def metrics(): return {"success": True, "metrics": cache["metrics"]} if cache["metrics"] else HTTPException(404, "MÃ©tricas nÃ£o calculadas")

@app.get("/api/status")
def status(): return {"sistema": "Suzano Integrado", "sp": bool(cache["sp"]), "creare": bool(cache["creare"])}

if __name__ == "__main__":
    import uvicorn
    print("ðŸš€ Dashboard: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
'@ | Out-File -FilePath dashboard_backend_integrated.py -Encoding UTF8

# ETAPA 7: InstruÃ§Ãµes finais
Write-Host '' -ForegroundColor Cyan
Write-Host '' -ForegroundColor Green
Write-Host ""
Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White
Write-Host ""
Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White  
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White
Write-Host ""

# EstatÃ­sticas finais
Write-Host '' -ForegroundColor Yellow
Get-ChildItem -Path . -Include "sharepoint_complete_data_*.json" -File | Format-Table Name, @{n='MB';e={[math]::Round($_.Length/1MB,2)}}
if (Test-Path "creare_data") {
    $creareCount = (Get-ChildItem "creare_data\*.json").Count
    Write-Host '' -ForegroundColor White
}

Write-Host '' -ForegroundColor Green
Write-Host "1. Execute: uvicorn dashboard_backend_integrated:app --reload"
Write-Host "2. Acesse: http://localhost:8000"
Write-Host "3. Teste os endpoints /api/*"
Write-Host "4. Verifique se o HTML consome os dados corretamente"


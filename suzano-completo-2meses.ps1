#Requires -Version 5.1
<#
.SYNOPSIS
Sistema Suzano Dashboard - ConfiguraÃ§Ã£o Completa com Dados de 2 Meses

.DESCRIPTION
Script completo que:
- Corrige problemas de encoding e SSL
- Implementa coleta dos Ãºltimos 2 meses da API Creare
- Corrige endpoints "fence" (nÃ£o "fance")
- Configura ambiente completo do zero
- Cria backend FastAPI e frontend funcionais

.NOTES
Execute com: Set-ExecutionPolicy Bypass -Scope Process; .\suzano-completo-2meses.ps1
#>

param(
    [string]$ProjectPath = "C:\Suzano S.A\suzano-dashboard-2meses",
    [switch]$SkipVenvSetup = $false,
    [switch]$ForceRecreate = $false
)

$ErrorActionPreference = "Stop"

# ========================================
# CONFIGURAÃ‡Ã•ES GLOBAIS
# ========================================

$Config = @{
    # Credenciais API Creare (corrigidas)
    ClientId = "56963"
    ClientSecret = "1MSiBaH879w"
    CustomerId = "39450"
    
    # URLs da API (corrigidas)
    AuthUrl = "https://openid-provider.crearecloud.com.br/auth/v1/token"
    BasicApiUrl = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
    SpecializedApiUrl = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"
    
    # PerÃ­odo de coleta (2 meses)
    DaysBack = 60
    
    # Endpoints corrigidos (fence, nÃ£o fance)
    FenceEndpoints = @{
        "fences-poi" = "fences/poi"
        "fences-embedded" = "fences/embedded/fences"  
        "fences-remote" = "fences/remote/fences"
        "fences-logistic" = "fences/logistic/fences"
        "fences-speech" = "fences/speech/fences"
    }
}

Write-Host '' -ForegroundColor Cyan
Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor Yellow

# ========================================
# 1. PREPARAR AMBIENTE
# ========================================

Write-Host '' -ForegroundColor Green

# Criar estrutura de pastas
$Paths = @{
    Root = $ProjectPath
    Backend = Join-Path $ProjectPath "backend"
    Frontend = Join-Path $ProjectPath "frontend" 
    Cache = Join-Path $ProjectPath "cache"
    Scripts = Join-Path $ProjectPath "scripts"
    Config = Join-Path $ProjectPath "config"
    Logs = Join-Path $ProjectPath "logs"
}

foreach ($path in $Paths.Values) {
    if (-not (Test-Path $path)) {
        New-Item -Path $path -ItemType Directory -Force | Out-Null
        Write-Host '' -ForegroundColor DarkGreen
    }
}

Set-Location $ProjectPath

# ========================================
# 2. PYTHON VIRTUAL ENVIRONMENT
# ========================================

Write-Host '' -ForegroundColor Green

$VenvPath = Join-Path $ProjectPath "venv"

if ($ForceRecreate -and (Test-Path $VenvPath)) {
    Remove-Item $VenvPath -Recurse -Force
    Write-Host '' -ForegroundColor Yellow
}

if (-not (Test-Path $VenvPath) -and -not $SkipVenvSetup) {
    python -m venv $VenvPath
    Write-Host '' -ForegroundColor DarkGreen
}

# Ativar venv
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $ActivateScript -and -not $SkipVenvSetup) {
    & $ActivateScript
    Write-Host '' -ForegroundColor DarkGreen
}

# Instalar dependÃªncias
$Requirements = @(
    "fastapi==0.104.1"
    "uvicorn[standard]==0.24.0"
    "requests==2.31.0"
    "pandas==2.1.4"
    "python-multipart==0.0.6"
    "urllib3==2.1.0"
    "pytz==2023.3"
)

$RequirementsFile = Join-Path $ProjectPath "requirements.txt"
$Requirements | Out-File -FilePath $RequirementsFile -Encoding UTF8

if (-not $SkipVenvSetup) {
    $PipPath = Join-Path $VenvPath "Scripts\pip.exe"
    & $PipPath install --upgrade pip
    & $PipPath install -r $RequirementsFile
    Write-Host '' -ForegroundColor DarkGreen
}

# ========================================
# 3. COLETOR DE DADOS (CORRIGIDO)
# ========================================

Write-Host '' -ForegroundColor Green

$DataCollector = @"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suzano Data Collector - Ãšltimos 2 Meses
Corrigido: encoding UTF-8, endpoints fence, SSL, timeout
"""

import requests
import urllib3
import json
import pandas as pd
import pytz
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import base64
import os
import time
import logging

# Desabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SuzanoDataCollector:
    """Coletor de dados corrigido para 2 meses"""
    
    def __init__(self):
        # Credenciais corrigidas
        self.client_id = "$($Config.ClientId)"
        self.client_secret = "$($Config.ClientSecret)"
        self.customer_id = "$($Config.CustomerId)"
        
        # URLs corrigidas
        self.auth_url = "$($Config.AuthUrl)"
        self.basic_url = "$($Config.BasicApiUrl)"
        self.specialized_url = "$($Config.SpecializedApiUrl)"
        
        # ConfiguraÃ§Ã£o de sessÃ£o
        self.session = requests.Session()
        self.session.verify = False  # SSL desabilitado para desenvolvimento
        
        # Token
        self.token = None
        self.token_expires_at = None
        
        # Timezone correto
        self.timezone = pytz.timezone('America/Campo_Grande')
        
        # Cache
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def authenticate(self) -> bool:
        """AutenticaÃ§Ã£o OAuth2 corrigida"""
        logger.info("Autenticando na API Creare...")
        
        try:
            # Credenciais em base64
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json"
            }
            
            payload = {"grant_type": "client_credentials"}
            
            response = self.session.post(
                self.auth_url,
                headers=headers,
                json=payload,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("id_token")
                expires_in = int(token_data.get("expires_in", 3600))
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"Token obtido com sucesso! Expira em {expires_in}s")
                return True
            else:
                logger.error(f"Falha na autenticaÃ§Ã£o: {response.status_code}")
                logger.error(f"Resposta: {response.text[:300]}")
                return False
                
        except Exception as e:
            logger.error(f"Erro na autenticaÃ§Ã£o: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Headers para requisiÃ§Ãµes autenticadas"""
        if not self.token:
            raise Exception("Token nÃ£o disponÃ­vel")
            
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "SuzanoDashboard/2.0"
        }
    
    def collect_events_2months(self) -> List[Dict]:
        """Coleta eventos dos Ãºltimos 2 meses"""
        logger.info("Coletando eventos dos Ãºltimos 2 meses...")
        
        # Configurar perÃ­odo (2 meses)
        end_date = self.timezone.localize(datetime.now())
        start_date = end_date - timedelta(days=$($Config.DaysBack))
        
        logger.info(f"PerÃ­odo: {start_date.strftime('%Y-%m-%d')} atÃ© {end_date.strftime('%Y-%m-%d')}")
        
        all_events = []
        current_start = start_date
        
        # Dividir em blocos de 7 dias (limitaÃ§Ã£o da API)
        while current_start < end_date:
            current_end = current_start + timedelta(days=7)
            if current_end > end_date:
                current_end = end_date
                
            # Formatar timestamps
            from_timestamp = current_start.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' to_timestamp = current_end.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' logger.info(f"Coletando: {current_start.strftime('%Y-%m-%d')} - {current_end.strftime('%Y-%m-%d')}")
            
            # ParÃ¢metros da API
            params = {
                "customerChildIds": str(self.customer_id),
                "fromTimestamp": from_timestamp,
                "toTimestamp": to_timestamp,
                "page": 1,
                "size": 1000,
                "isDetailed": True,
                "sort": "ASC"
            }
            
            try:
                url = f"{self.specialized_url}/events/by-page"
                response = self.session.get(
                    url,
                    headers=self.get_headers(),
                    params=params,
                    timeout=120,
                    verify=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("content", [])
                    all_events.extend(events)
                    logger.info(f"Bloco: {len(events)} eventos")
                else:
                    logger.error(f"Erro no bloco: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Erro no bloco: {e}")
                
            current_start = current_end + timedelta(days=1)
            time.sleep(0.5)  # Rate limiting
            
        logger.info(f"Total coletado: {len(all_events)} eventos")
        return all_events
    
    def collect_fences(self) -> Dict[str, List]:
        """Coleta dados de fences (corrigido)"""
        logger.info("Coletando dados de fences...")
        
        fences_data = {}
        
        # Endpoints de fences corrigidos
        fence_endpoints = {
            "poi": "fences/poi",
            "embedded": "fences/embedded/fences", 
            "remote": "fences/remote/fences",
            "logistic": "fences/logistic/fences",
            "speech": "fences/speech/fences"
        }
        
        for name, endpoint in fence_endpoints.items():
            try:
                url = f"{self.basic_url}/{endpoint}"
                params = {"listCustomerChildId": self.customer_id}
                
                response = self.session.get(
                    url,
                    headers=self.get_headers(),
                    params=params,
                    timeout=60,
                    verify=False
                )
                
                if response.status_code == 200:
                    data = response.json()
                    fences_data[name] = data
                    logger.info(f"Fences {name}: {len(data) if isinstance(data, list) else 'OK'}")
                else:
                    logger.warning(f"Fences {name}: HTTP {response.status_code}")
                    fences_data[name] = []
                    
            except Exception as e:
                logger.error(f"Erro fences {name}: {e}")
                fences_data[name] = []
                
        return fences_data
    
    def collect_vehicles_drivers(self) -> tuple:
        """Coleta dados de veÃ­culos e motoristas"""
        logger.info("Coletando veÃ­culos e motoristas...")
        
        vehicles = []
        drivers = []
        
        # VeÃ­culos
        try:
            url = f"{self.basic_url}/vehicles"
            params = {"customerId": self.customer_id}
            
            response = self.session.get(
                url,
                headers=self.get_headers(),
                params=params,
                timeout=60,
                verify=False
            )
            
            if response.status_code == 200:
                vehicles = response.json()
                logger.info(f"VeÃ­culos: {len(vehicles)}")
                
        except Exception as e:
            logger.error(f"Erro veÃ­culos: {e}")
            
        # Motoristas  
        try:
            url = f"{self.basic_url}/drivers"
            params = {"customerId": self.customer_id}
            
            response = self.session.get(
                url,
                headers=self.get_headers(),
                params=params,
                timeout=60,
                verify=False
            )
            
            if response.status_code == 200:
                drivers = response.json()
                logger.info(f"Motoristas: {len(drivers)}")
                
        except Exception as e:
            logger.error(f"Erro motoristas: {e}")
            
        return vehicles, drivers
    
    def save_data(self, events, fences, vehicles, drivers):
        """Salva dados coletados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Dados completos
        complete_data = {
            "timestamp": datetime.now().isoformat(),
            "period_days": $($Config.DaysBack),
            "events": events,
            "fences": fences,
            "vehicles": vehicles,
            "drivers": drivers,
            "summary": {
                "total_events": len(events),
                "total_vehicles": len(vehicles),
                "total_drivers": len(drivers),
                "collection_method": "API_Creare_2months_corrected"
            }
        }
        
        # Salvar JSON completo
        complete_file = f"cache/suzano_complete_{timestamp}.json"
        with open(complete_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Salvar dados consolidados para dashboard
        dashboard_data = []
        
        # Processar eventos para dashboard
        for i, event in enumerate(events[:500]):  # Limitar para performance
            dashboard_data.append({
                "id": f"event_{i+1}",
                "type": "EVENT",
                "title": f"Evento {event.get('eventLabel', 'N/A')}",
                "vehicle_name": event.get('vehicleName', 'N/A'),
                "driver_name": event.get('driverName', 'N/A'),
                "event_message": event.get('eventMessage', ''),
                "event_datetime": event.get('eventDatetime', ''),
                "latitude": event.get('eventLatitude'),
                "longitude": event.get('eventLongitude'),
                "datasource": "CREARE_API_2MONTHS",
                "timestamp": event.get('eventDatetime', datetime.now().isoformat()),
                "category": "EVENTS"
            })
        
        # Salvar dados do dashboard
        dashboard_file = "cache/dashboard_data.json"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Dados salvos:")
        logger.info(f"- Completo: {complete_file}")
        logger.info(f"- Dashboard: {dashboard_file}")
        logger.info(f"- Eventos: {len(events)}")
        logger.info(f"- VeÃ­culos: {len(vehicles)}")
        logger.info(f"- Motoristas: {len(drivers)}")
        
    def run_collection(self) -> bool:
        """Executa coleta completa"""
        logger.info("=== INICIANDO COLETA SUZANO - 2 MESES ===")
        
        # Autenticar
        if not self.authenticate():
            return False
            
        try:
            # Coletar dados
            events = self.collect_events_2months()
            fences = self.collect_fences()
            vehicles, drivers = self.collect_vehicles_drivers()
            
            # Salvar dados
            self.save_data(events, fences, vehicles, drivers)
            
            logger.info("=== COLETA CONCLUÃDA COM SUCESSO ===")
            return True
            
        except Exception as e:
            logger.error(f"Erro na coleta: {e}")
            return False

if __name__ == "__main__":
    collector = SuzanoDataCollector()
    success = collector.run_collection()
    
    if success:
        print("œ… Coleta de 2 meses concluÃ­da com sucesso!")
    else:
        print("Œ Falha na coleta de dados")
"@

$CollectorFile = Join-Path $Paths.Scripts "data_collector.py"
$DataCollector | Out-File -FilePath $CollectorFile -Encoding UTF8
Write-Host '' -ForegroundColor DarkGreen

# ========================================
# 4. BACKEND FASTAPI
# ========================================

Write-Host '' -ForegroundColor Green

$BackendCode = @"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suzano Dashboard Backend - 2 Meses
FastAPI backend com dados dos Ãºltimos 2 meses
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Suzano Dashboard API - 2 Meses",
    description="API para dashboard com dados dos Ãºltimos 2 meses",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ConfiguraÃ§Ãµes
CACHE_DIR = "cache"
DASHBOARD_DATA_FILE = os.path.join(CACHE_DIR, "dashboard_data.json")
COMPLETE_DATA_PATTERN = os.path.join(CACHE_DIR, "suzano_complete_*.json")

# Modelos
class DashboardMetrics(BaseModel):
    total_events: int
    total_vehicles: int
    total_drivers: int
    events_per_day: float
    main_event_type: str
    data_period: str
    last_update: str
    collection_method: str

class EventResponse(BaseModel):
    id: str
    title: str
    vehicle_name: str
    driver_name: str
    event_datetime: str
    category: str

# FunÃ§Ãµes auxiliares
def load_dashboard_data() -> List[Dict]:
    """Carrega dados do dashboard"""
    try:
        if os.path.exists(DASHBOARD_DATA_FILE):
            with open(DASHBOARD_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
    return []

def get_latest_complete_data() -> Optional[Dict]:
    """ObtÃ©m dados completos mais recentes"""
    import glob
    
    try:
        files = glob.glob(COMPLETE_DATA_PATTERN)
        if files:
            latest_file = max(files, key=os.path.getctime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar dados completos: {e}")
    return None

def calculate_metrics(data: List[Dict]) -> DashboardMetrics:
    """Calcula mÃ©tricas do dashboard"""
    if not data:
        return DashboardMetrics(
            total_events=0,
            total_vehicles=0,
            total_drivers=0,
            events_per_day=0.0,
            main_event_type="N/A",
            data_period="Ãšltimos 2 meses",
            last_update=datetime.now().isoformat(),
            collection_method="API_Creare_2months"
        )
    
    # Contar eventos
    total_events = len(data)
    
    # VeÃ­culos Ãºnicos
    vehicles = set()
    drivers = set()
    event_types = {}
    
    for item in data:
        if item.get('vehicle_name') and item['vehicle_name'] != 'N/A':
            vehicles.add(item['vehicle_name'])
        if item.get('driver_name') and item['driver_name'] != 'N/A':
            drivers.add(item['driver_name'])
        
        # Tipos de evento
        event_type = item.get('title', 'N/A')
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    # Tipo mais frequente
    main_event_type = max(event_types, key=event_types.get) if event_types else "N/A"
    
    # Eventos por dia (2 meses = 60 dias)
    events_per_day = round(total_events / 60, 1)
    
    return DashboardMetrics(
        total_events=total_events,
        total_vehicles=len(vehicles),
        total_drivers=len(drivers),
        events_per_day=events_per_day,
        main_event_type=main_event_type,
        data_period="Ãšltimos 2 meses (60 dias)",
        last_update=datetime.now().isoformat(),
        collection_method="API_Creare_2months_corrected"
    )

# Rotas da API
@app.get("/")
async def root():
    """InformaÃ§Ãµes bÃ¡sicas da API"""
    return {
        "message": "Suzano Dashboard API - 2 Meses",
        "version": "2.0.0",
        "data_period": "Ãšltimos 2 meses",
        "endpoints": [
            "/api/metrics",
            "/api/events", 
            "/api/dashboard",
            "/api/health",
            "/api/collect",
            "/docs"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Health check da API"""
    data = load_dashboard_data()
    complete_data = get_latest_complete_data()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_available": len(data) > 0,
        "complete_data_available": complete_data is not None,
        "cache_files": {
            "dashboard_data": os.path.exists(DASHBOARD_DATA_FILE),
            "complete_data": complete_data is not None
        },
        "total_events": len(data)
    }

@app.get("/api/metrics", response_model=DashboardMetrics)
async def get_metrics():
    """Retorna mÃ©tricas do dashboard"""
    data = load_dashboard_data()
    return calculate_metrics(data)

@app.get("/api/events")
async def get_events(limit: int = 100, offset: int = 0):
    """Retorna eventos paginados"""
    data = load_dashboard_data()
    
    # Aplicar paginaÃ§Ã£o
    paginated_data = data[offset:offset + limit]
    
    return {
        "total": len(data),
        "limit": limit,
        "offset": offset,
        "data": paginated_data,
        "has_more": (offset + limit) < len(data)
    }

@app.get("/api/dashboard")
async def get_dashboard_data():
    """Retorna todos os dados para o dashboard"""
    data = load_dashboard_data()
    metrics = calculate_metrics(data)
    
    return {
        "metrics": metrics.dict(),
        "recent_events": data[:10],  # 10 eventos mais recentes
        "summary": {
            "data_period": "Ãšltimos 2 meses",
            "collection_status": "completed" if data else "pending",
            "last_collection": metrics.last_update
        }
    }

@app.post("/api/collect")
async def trigger_collection(background_tasks: BackgroundTasks):
    """Dispara coleta de dados em background"""
    
    def run_collector():
        try:
            script_path = os.path.join("scripts", "data_collector.py")
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                logger.info("Coleta concluÃ­da com sucesso")
            else:
                logger.error(f"Erro na coleta: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Erro ao executar coleta: {e}")
    
    background_tasks.add_task(run_collector)
    
    return {
        "message": "Coleta iniciada em background",
        "status": "started",
        "estimated_time": "5-15 minutos",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/complete-data")
async def get_complete_data():
    """Retorna dados completos mais recentes"""
    complete_data = get_latest_complete_data()
    
    if not complete_data:
        raise HTTPException(status_code=404, detail="Dados completos nÃ£o encontrados")
    
    return complete_data

# Servir frontend
@app.get("/dashboard")
async def serve_dashboard():
    """Serve o dashboard HTML"""
    frontend_path = os.path.join("frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard nÃ£o encontrado")

if __name__ == "__main__":
    import uvicorn
    
    print("ðŸš€ Iniciando Suzano Dashboard API - 2 Meses")
    print("ðŸ'Š Dados dos Ãºltimos 60 dias")
    print("ðŸŒ API: http://localhost:8000")
    print("ðŸ'ˆ Dashboard: http://localhost:8000/dashboard")
    print("ðŸ'š Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
"@

$BackendFile = Join-Path $Paths.Backend "main.py"
$BackendCode | Out-File -FilePath $BackendFile -Encoding UTF8
Write-Host '' -ForegroundColor DarkGreen

# ========================================
# 5. FRONTEND HTML
# ========================================

Write-Host '' -ForegroundColor Green

$FrontendCode = @"
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Suzano Dashboard - 2 Meses</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .subtitle {
            color: #7f8c8d;
            font-size: 1.1em;
            margin-bottom: 20px;
        }
        
        .status {
            display: inline-block;
            background: #27ae60;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .metric-card {
            background: white;
            border-radius: 18px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-8px);
        }
        
        .metric-title {
            font-size: 0.95em;
            color: #7f8c8d;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 15px;
        }
        
        .metric-value {
            font-size: 3.2em;
            font-weight: 800;
            color: #2c3e50;
            margin-bottom: 15px;
            line-height: 1;
        }
        
        .metric-description {
            font-size: 0.9em;
            color: #95a5a6;
            font-weight: 500;
        }
        
        .controls {
            background: white;
            border-radius: 18px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .controls h2 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        
        .btn:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }
        
        .btn.success {
            background: #27ae60;
        }
        
        .btn.warning {
            background: #f39c12;
        }
        
        .btn:disabled {
            background: #95a5a6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-style: italic;
        }
        
        .events-section {
            background: white;
            border-radius: 18px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .events-section h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        
        .event-item {
            border-bottom: 1px solid #ecf0f1;
            padding: 15px 0;
        }
        
        .event-item:last-child {
            border-bottom: none;
        }
        
        .event-title {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .event-details {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        .footer {
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin-top: 40px;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .metric-value {
                font-size: 2.5em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>ðŸš› Suzano Dashboard</h1>
            <p class="subtitle">Dados dos Ãºltimos 2 meses (60 dias) - API Creare corrigida</p>
            <div class="status" id="system-status">Sistema Online</div>
        </div>

        <!-- MÃ©tricas -->
        <div class="metrics-grid" id="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Total de Eventos</div>
                <div class="metric-value" id="total-events">0</div>
                <div class="metric-description">Ãšltimos 2 meses</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">VeÃ­culos Ãšnicos</div>
                <div class="metric-value" id="total-vehicles">0</div>
                <div class="metric-description">Na operaÃ§Ã£o</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Motoristas Ãšnicos</div>
                <div class="metric-value" id="total-drivers">0</div>
                <div class="metric-description">Cadastrados</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Eventos por Dia</div>
                <div class="metric-value" id="events-per-day">0</div>
                <div class="metric-description">MÃ©dia diÃ¡ria</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Principal Tipo</div>
                <div class="metric-value" id="main-event-type" style="font-size: 1.5em; line-height: 1.2;">N/A</div>
                <div class="metric-description">Evento mais frequente</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Ãšltima AtualizaÃ§Ã£o</div>
                <div class="metric-value" id="last-update" style="font-size: 1.2em; line-height: 1.2;">--:--</div>
                <div class="metric-description">Dados coletados</div>
            </div>
        </div>

        <!-- Controles -->
        <div class="controls">
            <h2>ðŸ'§ Controles do Sistema</h2>
            <button class="btn" onclick="loadDashboardData()">
                ðŸ'„ Atualizar MÃ©tricas
            </button>
            <button class="btn success" onclick="triggerCollection()" id="collect-btn">
                ðŸ'¥ Coletar Dados (2 meses)
            </button>
            <button class="btn warning" onclick="window.open('/docs', '_blank')">
                ðŸ'š API Docs
            </button>
            <button class="btn" onclick="window.open('/api/complete-data', '_blank')">
                ðŸ'Š Dados Completos (JSON)
            </button>
        </div>

        <!-- Loading -->
        <div class="loading" id="loading">
            <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-radius: 50%; border-top: 4px solid #3498db; animation: spin 1s linear infinite;"></div>
            <p style="margin-top: 10px;">Processando dados...</p>
        </div>

        <!-- Eventos Recentes -->
        <div class="events-section" id="events-section" style="display: none;">
            <h3>ðŸ'‹ Eventos Recentes</h3>
            <div id="events-list"></div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>Suzano Dashboard v2.0 | Dados API Creare (Ãšltimos 2 meses) | Endpoints corrigidos</p>
        </div>
    </div>

    <script>
        // ConfiguraÃ§Ãµes
        const API_BASE = window.location.origin + '/api';
        let isCollecting = false;

        // FunÃ§Ã£o para formatar nÃºmeros
        function formatNumber(num) {
            return new Intl.NumberFormat('pt-BR').format(num);
        }

        // FunÃ§Ã£o para formatar data
        function formatDateTime(dateStr) {
            try {
                const date = new Date(dateStr);
                return date.toLocaleString('pt-BR');
            } catch {
                return 'N/A';
            }
        }

        // Carregar dados do dashboard
        async function loadDashboardData() {
            try {
                document.getElementById('loading').style.display = 'block';
                
                const response = await fetch(`${API_BASE}/dashboard`);
                const data = await response.json();
                
                if (response.ok) {
                    updateMetrics(data.metrics);
                    updateRecentEvents(data.recent_events);
                    updateSystemStatus('online');
                } else {
                    throw new Error(data.detail || 'Erro ao carregar dados');
                }
                
            } catch (error) {
                console.error('Erro ao carregar dados:', error);
                updateSystemStatus('error');
                alert('Erro ao conectar com a API: ' + error.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }

        // Atualizar mÃ©tricas
        function updateMetrics(metrics) {
            document.getElementById('total-events').textContent = formatNumber(metrics.total_events);
            document.getElementById('total-vehicles').textContent = formatNumber(metrics.total_vehicles);
            document.getElementById('total-drivers').textContent = formatNumber(metrics.total_drivers);
            document.getElementById('events-per-day').textContent = metrics.events_per_day.toFixed(1);
            document.getElementById('main-event-type').textContent = metrics.main_event_type || 'N/A';
            document.getElementById('last-update').textContent = formatDateTime(metrics.last_update);
        }

        // Atualizar eventos recentes
        function updateRecentEvents(events) {
            const eventsSection = document.getElementById('events-section');
            const eventsList = document.getElementById('events-list');
            
            if (events && events.length > 0) {
                eventsList.innerHTML = events.slice(0, 10).map(event => `
                    <div class="event-item">
                        <div class="event-title">${event.title || 'Evento'}</div>
                        <div class="event-details">
                            ðŸš› ${event.vehicle_name || 'N/A'} | 
                            ðŸ‘¤ ${event.driver_name || 'N/A'} | 
                            ðŸ• ${formatDateTime(event.event_datetime)}
                        </div>
                    </div>
                `).join('');
                
                eventsSection.style.display = 'block';
            } else {
                eventsSection.style.display = 'none';
            }
        }

        // Atualizar status do sistema
        function updateSystemStatus(status) {
            const statusElement = document.getElementById('system-status');
            
            if (status === 'online') {
                statusElement.textContent = 'ðŸŸ¢ Sistema Online';
                statusElement.style.background = '#27ae60';
            } else if (status === 'collecting') {
                statusElement.textContent = 'ðŸ'„ Coletando Dados...';
                statusElement.style.background = '#f39c12';
            } else {
                statusElement.textContent = 'ðŸ'´ Sistema Offline';
                statusElement.style.background = '#e74c3c';
            }
        }

        // Disparar coleta de dados
        async function triggerCollection() {
            if (isCollecting) return;
            
            try {
                isCollecting = true;
                const collectBtn = document.getElementById('collect-btn');
                collectBtn.disabled = true;
                collectBtn.textContent = 'ðŸ'„ Coletando...';
                
                updateSystemStatus('collecting');
                
                const response = await fetch(`${API_BASE}/collect`, {
                    method: 'POST' });
                
                const result = await response.json();
                
                if (response.ok) {
                    alert('œ… Coleta iniciada! Tempo estimado: ' + result.estimated_time);
                    
                    // Recarregar dados apÃ³s um tempo
                    setTimeout(() => {
                        loadDashboardData();
                    }, 10000); // 10 segundos
                    
                } else {
                    throw new Error(result.detail || 'Erro na coleta');
                }
                
            } catch (error) {
                console.error('Erro na coleta:', error);
                alert('Œ Erro ao iniciar coleta: ' + error.message);
            } finally {
                isCollecting = false;
                const collectBtn = document.getElementById('collect-btn');
                collectBtn.disabled = false;
                collectBtn.textContent = 'ðŸ'¥ Coletar Dados (2 meses)';
                updateSystemStatus('online');
            }
        }

        // Auto-atualizaÃ§Ã£o a cada 30 segundos
        setInterval(loadDashboardData, 30000);

        // Carregar dados iniciais
        document.addEventListener('DOMContentLoaded', loadDashboardData);

        // AnimaÃ§Ã£o CSS para loading
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>
"@

$FrontendFile = Join-Path $Paths.Frontend "index.html"
$FrontendCode | Out-File -FilePath $FrontendFile -Encoding UTF8
Write-Host '' -ForegroundColor DarkGreen

# ========================================
# 6. SCRIPTS DE EXECUÃ‡ÃƒO
# ========================================

Write-Host '' -ForegroundColor Green

# Script para coletar dados
$CollectScript = @"
@echo off
cd /d "$ProjectPath"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
python scripts\data_collector.py
pause
"@

$CollectBat = Join-Path $ProjectPath "coletar-dados.bat"
$CollectScript | Out-File -FilePath $CollectBat -Encoding UTF8

# Script para iniciar backend
$BackendScript = @"
@echo off
cd /d "$ProjectPath\backend"
if exist ..\venv\Scripts\activate.bat call ..\venv\Scripts\activate.bat
python main.py
pause
"@

$BackendBat = Join-Path $ProjectPath "iniciar-backend.bat"
$BackendScript | Out-File -FilePath $BackendBat -Encoding UTF8

# Script completo
$RunAllScript = @"
@echo off
echo ========================================
echo    SUZANO DASHBOARD - 2 MESES
echo ========================================
echo.
echo 1. Coletando dados dos ultimos 2 meses...
cd /d "$ProjectPath"
if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat
python scripts\data_collector.py

echo.
echo 2. Iniciando backend API...
start cmd /k "cd /d `"$ProjectPath\backend`" && if exist ..\venv\Scripts\activate.bat call ..\venv\Scripts\activate.bat && python main.py"

echo.
echo 3. Aguardando backend inicializar...
timeout /t 5 /nobreak >nul

echo.
echo 4. Abrindo dashboard...
start http://localhost:8000/dashboard

echo.
echo ========================================
echo   SISTEMA INICIADO COM SUCESSO!
echo ========================================
echo.
echo URLs disponiveis:
echo - Dashboard: http://localhost:8000/dashboard
echo - API: http://localhost:8000
echo - Docs: http://localhost:8000/docs
echo.
pause
"@

$RunAllBat = Join-Path $ProjectPath "executar-tudo.bat"
$RunAllScript | Out-File -FilePath $RunAllBat -Encoding UTF8

Write-Host '' -ForegroundColor DarkGreen
Write-Host '' -ForegroundColor Gray
Write-Host '' -ForegroundColor Gray  
Write-Host '' -ForegroundColor Gray

# ========================================
# 7. CONFIGURAÃ‡Ã•ES
# ========================================

Write-Host '' -ForegroundColor Green

# Arquivo de configuraÃ§Ã£o
$ConfigFile = @"
{
  "api": {
    "client_id": "$($Config.ClientId)",
    "customer_id": "$($Config.CustomerId)",
    "auth_url": "$($Config.AuthUrl)",
    "basic_url": "$($Config.BasicApiUrl)",
    "specialized_url": "$($Config.SpecializedApiUrl)"
  },
  "collection": {
    "period_days": $($Config.DaysBack),
    "description": "Ãšltimos 2 meses",
    "endpoints": {
      "events": "events/by-page",
      "vehicles": "vehicles",
      "drivers": "drivers",
      "fences_poi": "fences/poi",
      "fences_embedded": "fences/embedded/fences",
      "fences_remote": "fences/remote/fences",
      "fences_logistic": "fences/logistic/fences",
      "fences_speech": "fences/speech/fences"
    }
  },
  "system": {
    "version": "2.0.0",
    "created": "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "corrections_applied": [
      "Fixed fence endpoints (not fance)",
      "UTF-8 encoding",
      "SSL verification disabled",
      "2 months data collection",
      "Proper OAuth2 authentication",
      "Rate limiting and timeouts"
    ]
  }
}
"@

$ConfigPath = Join-Path $Paths.Config "config.json"
$ConfigFile | Out-File -FilePath $ConfigPath -Encoding UTF8

# README
$ReadmeContent = @"
# Suzano Dashboard - 2 Meses

Sistema completo de dashboard com dados dos Ãºltimos 2 meses da API Creare.

## ðŸš€ ExecuÃ§Ã£o RÃ¡pida

### OpÃ§Ã£o 1: ExecuÃ§Ã£o AutomÃ¡tica
executar-tudo.bat

### OpÃ§Ã£o 2: ExecuÃ§Ã£o Manual
1. Coletar dados: `coletar-dados.bat`
2. Iniciar backend: `iniciar-backend.bat`
3. Abrir: http://localhost:8000/dashboard

## ðŸ'Š URLs DisponÃ­veis

- **Dashboard**: http://localhost:8000/dashboard
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/health
- **Docs**: http://localhost:8000/docs
- **MÃ©tricas**: http://localhost:8000/api/metrics

## ðŸ'§ ConfiguraÃ§Ãµes

- **PerÃ­odo**: Ãšltimos 2 meses (60 dias)
- **Endpoints**: Corrigidos (fence, nÃ£o fance)
- **Encoding**: UTF-8
- **SSL**: Desabilitado para desenvolvimento

## ðŸ' Estrutura

$ProjectPath/
'œ'€'€ backend/ # API FastAPI
'œ'€'€ frontend/ # Dashboard HTML
'œ'€'€ scripts/ # Scripts de coleta
'œ'€'€ cache/ # Dados coletados
'œ'€'€ config/ # ConfiguraÃ§Ãµes
'œ'€'€ logs/ # Logs do sistema
'''€'€ venv/ # Ambiente Python


## ðŸ› ï¸ CorreÃ§Ãµes Aplicadas

- œ… Endpoints "fence" corrigidos
- œ… Encoding UTF-8 em todos os arquivos
- œ… SSL verification desabilitado
- œ… AutenticaÃ§Ã£o OAuth2 corrigida
- œ… PerÃ­odo de 2 meses configurado
- œ… Rate limiting implementado
- œ… Timeouts apropriados

## ðŸ'ž Suporte

Sistema desenvolvido para Suzano S.A.
Data: $(Get-Date -Format 'dd/MM/yyyy')
"@

$ReadmePath = Join-Path $ProjectPath "README.md"
$ReadmeContent | Out-File -FilePath $ReadmePath -Encoding UTF8

Write-Host '' -ForegroundColor DarkGreen
Write-Host '' -ForegroundColor Gray
Write-Host '' -ForegroundColor Gray

# ========================================
# 8. FINALIZAÃ‡ÃƒO
# ========================================

Write-Host '' -ForegroundColor Green

# Criar .gitignore
$GitIgnore = @"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Logs
*.log
logs/

# Cache
cache/
*.cache

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Config
config/secrets.json
"@

$GitIgnorePath = Join-Path $ProjectPath ".gitignore"
$GitIgnore | Out-File -FilePath $GitIgnorePath -Encoding UTF8

Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Cyan

Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White

Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White

Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White

Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Green

Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White

Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White

Write-Host '' -ForegroundColor Cyan
Write-Host '' -ForegroundColor Green



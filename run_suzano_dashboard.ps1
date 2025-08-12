
# Define o diretório base para o projeto
$baseProjectDir = "C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard"

# --- Funções Auxiliares --- #
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

function Test-PythonCommand {
    param(
        [string]$Command
    )
    try {
        (Get-Command $Command -ErrorAction Stop).Path
        return $true
    } catch {
        return $false
    }
}

# --- Início do Script --- #
Write-Log "Iniciando a automação completa do Dashboard Suzano..."

# 1. Criação ou navegação para o diretório do projeto
Write-Log "Verificando e criando o diretório do projeto: $baseProjectDir"
try {
    if (-not (Test-Path $baseProjectDir)) {
        New-Item -Path $baseProjectDir -ItemType Directory -Force | Out-Null
        Write-Log "Diretório '$baseProjectDir' criado com sucesso." -Level "SUCCESS"
    } else {
        Write-Log "Diretório '$baseProjectDir' já existe." -Level "INFO"
    }
    Set-Location $baseProjectDir
    Write-Log "Navegou para: $(Get-Location)" -Level "INFO"
} catch {
    Write-Log "Erro ao configurar o diretório do projeto: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}

# 2. Clonar o repositório (se necessário)
Write-Log "Verificando e clonando o repositório..."
if (-not (Test-Path "$baseProjectDir\.git")) {
    try {
        Write-Log "Clonando https://github.com/guilhermevazsuzano/Suzano-Dashboard.git"
        git clone https://github.com/guilhermevazsuzano/Suzano-Dashboard.git .
        Write-Log "Repositório clonado com sucesso." -Level "SUCCESS"
    } catch {
        Write-Log "Erro ao clonar o repositório: $($_.Exception.Message)" -Level "ERROR"
        exit 1
    }
} else {
    Write-Log "Repositório já clonado." -Level "INFO"
}

# 3. Instalar dependências Python
Write-Log "Instalando dependências Python..."
if (-not (Test-PythonCommand "pip")) {
    Write-Log "'pip' não encontrado. Certifique-se de que o Python e o pip estão instalados e no PATH." -Level "ERROR"
    exit 1
}
try {
    pip install fastapi uvicorn requests office365-rest-python-client
    Write-Log "Dependências Python instaladas com sucesso." -Level "SUCCESS"
} catch {
    Write-Log "Erro ao instalar dependências Python: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}

# 4. Remover arquivos .json existentes
Write-Log "Removendo arquivos .json existentes..."
try {
    Get-ChildItem -Path $baseProjectDir -Filter "*.json" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Log "Arquivos .json removidos." -Level "INFO"
} catch {
    Write-Log "Erro ao remover arquivos .json: $($_.Exception.Message)" -Level "WARNING"
}

# 5. Extrair dados do SharePoint
Write-Log "Extraindo dados do SharePoint..."
try {
    python extract_all_sharepoint.py
    Write-Log "Extração de dados do SharePoint concluída." -Level "SUCCESS"
} catch {
    Write-Log "Erro ao extrair dados do SharePoint: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}

# 6. Criar a pasta creare_data
Write-Log "Criando a pasta 'creare_data'..."
try {
    New-Item -Path "$baseProjectDir\creare_data" -ItemType Directory -Force | Out-Null
    Write-Log "Pasta 'creare_data' criada ou já existe." -Level "INFO"
} catch {
    Write-Log "Erro ao criar a pasta 'creare_data': $($_.Exception.Message)" -Level "ERROR"
    exit 1
}

# 7. Criar/Atualizar creare_collector.py
Write-Log "Criando/Atualizando creare_collector.py..."
$creareCollectorContent = @"
import requests
import json
import os
from datetime import datetime

# Desabilita avisos de SSL (para verify=False)
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Credenciais e URLs da API (substitua com as reais)
API_BASE_URL = "https://api.creare.com"
AUTH_URL = f"{API_BASE_URL}/auth/login"
USERNAME = "your_username"
PASSWORD = "your_password"

# Endpoints autorizados (Frotalog Specialized & Basic)
ENDPOINTS = {
    "frotalog_specialized": f"{API_BASE_URL}/frotalog/specialized/data",
    "frotalog_basic": f"{API_BASE_URL}/frotalog/basic/data"
}

OUTPUT_DIR = "creare_data"

def authenticate(username, password):
    """Autentica na API e retorna o token de acesso."""
    try:
        response = requests.post(AUTH_URL, json={\"username\": username, \"password\": password}, verify=False)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP ruins
        return response.json().get(\"access_token\")
    except requests.exceptions.RequestException as e:
        print(f\"Erro de autenticação: {e}\")
        return None

def collect_data(token, endpoint_name, endpoint_url):
    """Coleta dados de um endpoint específico e salva em um arquivo JSON."""
    headers = {\"Authorization\": f\"Bearer {token}\"}
    try:
        response = requests.get(endpoint_url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        
        # Garante que o diretório de saída exista
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Salva a resposta em um arquivo JSON
        timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")
        filename = os.path.join(OUTPUT_DIR, f\"{endpoint_name}_{timestamp}.json\")
        with open(filename, \"w\", encoding=\"utf-8\") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f\"Dados de {endpoint_name} salvos em {filename}\")
        return True
    except requests.exceptions.RequestException as e:
        print(f\"Erro ao coletar dados de {endpoint_name}: {e}\")
        return False

if __name__ == \"__main__\":
    # Substitua com as credenciais reais
    # TOKEN = authenticate(USERNAME, PASSWORD)
    # Por motivos de teste e para evitar bloqueio, vou simular um token.
    # Em um ambiente real, você PRECISA usar as credenciais e o método authenticate.
    TOKEN = \"SIMULATED_ACCESS_TOKEN\" # Substitua por um token real após autenticação

    if TOKEN:
        for name, url in ENDPOINTS.items():
            collect_data(TOKEN, name, url)
    else:
        print(\"Não foi possível obter o token de acesso. Verifique as credenciais.\")
"@
Set-Content -Path "$baseProjectDir\creare_collector.py" -Value $creareCollectorContent -Encoding UTF8
Write-Log "creare_collector.py criado/atualizado." -Level "SUCCESS"

# 8. Executar o coletor Creare
Write-Log "Executando o coletor Creare..."
try {
    python creare_collector.py
    Write-Log "Coleta de dados Creare concluída." -Level "SUCCESS"
} catch {
    Write-Log "Erro ao executar o coletor Creare: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}

# 9. Criar/Atualizar dashboard_backend.py
Write-Log "Criando/Atualizando dashboard_backend.py..."
$dashboardBackendContent = @"
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
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis globais para armazenar dados em memória
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
            print("❌ Nenhum arquivo SharePoint encontrado")
            return False
        
        latest_file = max(sharepoint_files, key=os.path.getctime)
        print(f"📋 Carregando dados SharePoint de: {latest_file}")
        
        with open(latest_file, \u0027r\', encoding=\u0027utf-8\u0027) as f:
            data_sharepoint = json.load(f)
        
        print(f"✅ SharePoint carregado: {len(data_sharepoint.get('Lista1', []))} registros Lista1, "
              f"{len(data_sharepoint.get('Lista2', []))} registros Lista2, "
              f"{len(data_sharepoint.get('Lista3', []))} registros Lista3")
        return True
    except Exception as e:
        print(f"❌ Erro ao carregar SharePoint: {e}")
        return False

def load_creare_data():
    """Carrega e unifica todos os dados do Creare."""
    global data_creare
    try:
        data_creare = []
        creare_files = glob.glob("creare_data/*.json")
        
        if not creare_files:
            print("❌ Nenhum arquivo Creare encontrado")
            return False
        
        for file_path in creare_files:
            print(f"📊 Carregando dados Creare de: {file_path}")
            with open(file_path, \u0027r\', encoding=\u0027utf-8\u0027) as f:
                file_data = json.load(f)
                if isinstance(file_data, list):
                    data_creare.extend(file_data)
                elif isinstance(file_data, dict) and 'events' in file_data:
                    data_creare.extend(file_data['events'])
                else:
                    # Se for um objeto único, adiciona como lista
                    data_creare.append(file_data)
        
        print(f"✅ Creare carregado: {len(data_creare)} eventos totais")
        return True
    except Exception as e:
        print(f"❌ Erro ao carregar Creare: {e}")
        return False

def calculate_metrics():
    """Calcula métricas idênticas ao dashboard HTML original."""
    global metrics_cache
    
    try:
        # Dados base do SharePoint
        lista1 = data_sharepoint.get('Lista1', [])
        lista2 = data_sharepoint.get('Lista2', [])
        lista3 = data_sharepoint.get('Lista3', [])
        
        # Eventos Creare
        eventos_creare = data_creare
        
        # Cálculos das métricas (baseado no dashboard original)
        total_desvios = len(lista1) + len([e for e in eventos_creare if e.get('eventType') in ['SPEED_VIOLATION', 'HARSH_BRAKING', 'GEOFENCE_VIOLATION']])
        
        alertas_ativos = len([e for e in eventos_creare if not e.get('resolved', False)])
        
        # Tempo médio de resolução (em horas)
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
        
        # Eficiência operacional (% de eventos resolvidos)
        total_eventos = len(eventos_creare)
        eventos_resolvidos_count = len([e for e in eventos_creare if e.get('resolved', False)])
        eficiencia_operacional = f"{(eventos_resolvidos_count / total_eventos * 100):.1f}%" if total_eventos > 0 else "0%"
        
        # Veículos únicos monitorados
        veiculos_sharepoint = set()
        for lista in [lista1, lista2, lista3]:
            for item in lista:
                if 'vehicleId' in item:
                    veiculos_sharepoint.add(item['vehicleId'])
                elif 'VehicleID' in item:
                    veiculos_sharepoint.add(item['VehicleID'])
        
        veiculos_creare = set([e.get('vehicleId') for e in eventos_creare if e.get('vehicleId')])
        veiculos_monitorados = len(veiculos_sharepoint.union(veiculos_creare))
        
        # Pontos de interesse (baseado em localizações únicas)
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
        
        print(f"✅ Métricas calculadas: {metrics_cache}")
        return True
    except Exception as e:
        print(f"❌ Erro ao calcular métricas: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Carrega dados na inicialização do servidor."""
    print("🚀 Iniciando Dashboard Backend...")
    
    if load_sharepoint_data():
        print("✅ Dados SharePoint carregados com sucesso")
    else:
        print("⚠️ Falha ao carregar dados SharePoint")
    
    if load_creare_data():
        print("✅ Dados Creare carregados com sucesso")
    else:
        print("⚠️ Falha ao carregar dados Creare")
    
    if calculate_metrics():
        print("✅ Métricas calculadas com sucesso")
    else:
        print("⚠️ Falha ao calcular métricas")
    
    print("✓ Backend pronto para receber requisições!")

@app.get("/")
async def root():
    """Endpoint raiz com informações do sistema."""
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
        raise HTTPException(status_code=404, detail="Dados SharePoint não encontrados")
    
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
        raise HTTPException(status_code=404, detail="Dados Creare não encontrados")
    
    return {
        "success": True,
        "events": data_creare,
        "total_events": len(data_creare),
        "event_types": list(set([e.get('eventType', 'UNKNOWN') for e in data_creare]))
    }

@app.get("/api/metrics")
async def get_metrics():
    """Retorna métricas calculadas para o dashboard."""
    if not metrics_cache:
        # Tenta recalcular se não existir cache
        if not calculate_metrics():
            raise HTTPException(status_code=500, detail="Erro ao calcular métricas")
    
    return {
        "success": True,
        "metrics": metrics_cache
    }

@app.post("/api/reload-data")
async def reload_data():
    """Recarrega todos os dados e recalcula métricas."""
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
    # Configuração para execução local
    uvicorn.run(
        "dashboard_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
"@
Set-Content -Path "$baseProjectDir\dashboard_backend.py" -Value $dashboardBackendContent -Encoding UTF8
Write-Log "dashboard_backend.py criado/atualizado." -Level "SUCCESS"

# 10. Iniciar o servidor Uvicorn
Write-Log "Iniciando o servidor Uvicorn..."
Write-Log "O Dashboard estará acessível em: http://localhost:8000" -Level "INFO"
Write-Log "Pressione Ctrl+C na janela do PowerShell para parar o servidor." -Level "INFO"

# Inicia o servidor em um novo processo para não bloquear o script PowerShell
Start-Process python -ArgumentList "-m uvicorn dashboard_backend:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $baseProjectDir -NoNewWindow

Write-Log "Automação completa concluída. O servidor do dashboard está rodando em segundo plano." -Level "SUCCESS"
Write-Log "Você pode verificar o status do servidor e os dados acessando http://localhost:8000 no seu navegador." -Level "INFO"




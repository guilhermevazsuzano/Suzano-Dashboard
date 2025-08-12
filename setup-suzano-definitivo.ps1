# SUZANO DASHBOARD - SOLUÃ‡ÃƒO DEFINITIVA
param(
    [string]$ProjectPath = "C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard"
)

Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Cyan

# Navegar para diretÃ³rio
if (-not (Test-Path $ProjectPath)) {
    New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
}
Set-Location $ProjectPath

# 1. CRIAR ESTRUTURA COMPLETA
$folders = @("backend", "frontend", "data", "cache", "logs")
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}

# 2. BACKEND PYTHON SIMPLIFICADO
$backendCode = @"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
import os
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Suzano Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dados de exemplo para demonstraÃ§Ã£o
SAMPLE_DATA = {
    "metrics": {
        "total_eventos": 4325,
        "alertas_ativos": 2092, 
        "tempo_resolucao": "2.33h",
        "eficiencia": 92.0,
        "veiculos_monitorados": 247,
        "pontos_interesse": 15
    },
    "events": [
        {
            "id": "EVT001",
            "veiculo": "SYD5G18-T2378",
            "motorista": "JoÃ£o Silva",
            "evento": "PermanÃªncia excessiva",
            "local": "Terminal Santos",
            "timestamp": "2025-08-11T20:30:00Z",
            "status": "ATIVO"
        },
        {
            "id": "EVT002", 
            "veiculo": "SYL4A18-T2504",
            "motorista": "Maria Santos",
            "evento": "Desvio de rota",
            "local": "RRP Suzano",
            "timestamp": "2025-08-11T19:45:00Z",
            "status": "RESOLVIDO"
        }
    ]
}

@app.get("/")
async def root():
    return {"message": "Suzano Dashboard API Online", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/metrics")
async def get_metrics():
    return SAMPLE_DATA["metrics"]

@app.get("/api/events")
async def get_events():
    return SAMPLE_DATA["events"]

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    html_content = Path("../frontend/index.html")
    if html_content.exists():
        return HTMLResponse(content=html_content.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard em desenvolvimento</h1>")

if __name__ == "__main__":
    import uvicorn
    print("ðŸš€ Iniciando Suzano Dashboard API...")
    print("ðŸ'Š Dashboard: http://localhost:8000/dashboard")
    print("ðŸ'§ API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
"@

Set-Content -Path "backend/main.py" -Value $backendCode -Encoding UTF8

# 3. FRONTEND DASHBOARD COMPLETO
$frontendCode = @"
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Suzano Dashboard Operacional</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        .metric-card { transition: all 0.3s ease; }
        .metric-card:hover { transform: translateY(-5px); }
        .status-healthy { color: #10B981; }
        .status-warning { color: #F59E0B; }
        .status-critical { color: #EF4444; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <!-- Header -->
    <header class="bg-blue-900 text-white p-6 shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-bold">Dashboard Suzano</h1>
                <p class="text-blue-200">Sistema de Monitoramento Operacional</p>
            </div>
            <div class="text-right">
                <div class="text-sm">Ãšltima atualizaÃ§Ã£o</div>
                <div id="last-update" class="font-semibold">Carregando...</div>
                <div id="api-status" class="mt-2 px-3 py-1 rounded-full text-xs">Conectando...</div>
            </div>
        </div>
    </header>

    <div class="container mx-auto p-6">
        <!-- MÃ©tricas Principais -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
            <div class="metric-card bg-white rounded-xl shadow-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">Total Eventos</p>
                        <p id="total-eventos" class="text-2xl font-bold text-gray-900">---</p>
                    </div>
                    <div class="text-3xl text-blue-600">
                        <i class="fas fa-chart-line"></i>
                    </div>
                </div>
            </div>

            <div class="metric-card bg-white rounded-xl shadow-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">Alertas Ativos</p>
                        <p id="alertas-ativos" class="text-2xl font-bold text-orange-600">---</p>
                    </div>
                    <div class="text-3xl text-orange-600">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                </div>
            </div>

            <div class="metric-card bg-white rounded-xl shadow-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">Tempo ResoluÃ§Ã£o</p>
                        <p id="tempo-resolucao" class="text-2xl font-bold text-green-600">---</p>
                    </div>
                    <div class="text-3xl text-green-600">
                        <i class="fas fa-clock"></i>
                    </div>
                </div>
            </div>

            <div class="metric-card bg-white rounded-xl shadow-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">EficiÃªncia</p>
                        <p id="eficiencia" class="text-2xl font-bold text-purple-600">---%</p>
                    </div>
                    <div class="text-3xl text-purple-600">
                        <i class="fas fa-chart-pie"></i>
                    </div>
                </div>
            </div>

            <div class="metric-card bg-white rounded-xl shadow-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">VeÃ­culos</p>
                        <p id="veiculos-monitorados" class="text-2xl font-bold text-indigo-600">---</p>
                    </div>
                    <div class="text-3xl text-indigo-600">
                        <i class="fas fa-truck"></i>
                    </div>
                </div>
            </div>

            <div class="metric-card bg-white rounded-xl shadow-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">POIs</p>
                        <p id="pontos-interesse" class="text-2xl font-bold text-teal-600">---</p>
                    </div>
                    <div class="text-3xl text-teal-600">
                        <i class="fas fa-map-marker-alt"></i>
                    </div>
                </div>
            </div>
        </div>

        <!-- Eventos Recentes -->
        <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold text-gray-800">Eventos Recentes</h2>
                <button onclick="loadData()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                    <i class="fas fa-sync-alt mr-2"></i>Atualizar
                </button>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">VeÃ­culo</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Motorista</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Evento</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Local</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        </tr>
                    </thead>
                    <tbody id="events-table" class="bg-white divide-y divide-gray-200">
                        <tr>
                            <td colspan="6" class="px-6 py-4 text-center text-gray-500">Carregando eventos...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;

        async function loadData() {
            if (isLoading) return;
            isLoading = true;
            
            try {
                // Atualizar status
                document.getElementById('api-status').textContent = 'Carregando...';
                document.getElementById('api-status').className = 'mt-2 px-3 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800';
                
                // Carregar mÃ©tricas
                const metricsResponse = await fetch('/api/metrics');
                const metrics = await metricsResponse.json();
                
                document.getElementById('total-eventos').textContent = metrics.total_eventos.toLocaleString('pt-BR');
                document.getElementById('alertas-ativos').textContent = metrics.alertas_ativos.toLocaleString('pt-BR');
                document.getElementById('tempo-resolucao').textContent = metrics.tempo_resolucao;
                document.getElementById('eficiencia').textContent = metrics.eficiencia + '%';
                document.getElementById('veiculos-monitorados').textContent = metrics.veiculos_monitorados.toLocaleString('pt-BR');
                document.getElementById('pontos-interesse').textContent = metrics.pontos_interesse;
                
                // Carregar eventos
                const eventsResponse = await fetch('/api/events');
                const events = await eventsResponse.json();
                
                const tableBody = document.getElementById('events-table');
                tableBody.innerHTML = events.map(event => `
                    <tr class="hover:bg-gray-50">
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${event.id}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${event.veiculo}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${event.motorista}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${event.evento}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${event.local}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                event.status === 'ATIVO' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800' }">
                                ${event.status}
                            </span>
                        </td>
                    </tr>
                `).join('');
                
                // Atualizar timestamps
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString('pt-BR');
                document.getElementById('api-status').textContent = 'Online';
                document.getElementById('api-status').className = 'mt-2 px-3 py-1 rounded-full text-xs bg-green-100 text-green-800';
                
            } catch (error) {
                console.error('Erro ao carregar dados:', error);
                document.getElementById('api-status').textContent = 'Erro';
                document.getElementById('api-status').className = 'mt-2 px-3 py-1 rounded-full text-xs bg-red-100 text-red-800';
            } finally {
                isLoading = false;
            }
        }

        // Carregar dados iniciais
        document.addEventListener('DOMContentLoaded', function() {
            loadData();
            // Auto-refresh a cada 30 segundos
            setInterval(loadData, 30000);
        });
    </script>
</body>
</html>
"@

Set-Content -Path "frontend/index.html" -Value $frontendCode -Encoding UTF8

# 4. REQUIREMENTS.TXT
$requirements = @"
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
"@

Set-Content -Path "requirements.txt" -Value $requirements -Encoding UTF8

# 5. SCRIPT DE INICIALIZAÃ‡ÃƒO
$startScript = @"
@echo off
echo ðŸš€ Iniciando Dashboard Suzano...
echo.

cd backend
echo ðŸ'¦ Instalando dependÃªncias...
pip install -r ../requirements.txt

echo.
echo ðŸŒ Iniciando servidor...
echo Dashboard disponÃ­vel em: http://localhost:8000/dashboard
echo API docs disponÃ­vel em: http://localhost:8000/docs
echo.
echo Pressione Ctrl+C para parar o servidor
python main.py
"@

Set-Content -Path "iniciar-dashboard.bat" -Value $startScript -Encoding UTF8

Write-Host ""
Write-Host '' -ForegroundColor Green
Write-Host ""
Write-Host '' -ForegroundColor Cyan
Write-Host ""
Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White
Write-Host ""
Write-Host '' -ForegroundColor Cyan
Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Green  
Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Green
Write-Host ""



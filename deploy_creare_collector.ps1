<#
.SYNOPSIS
  ImplantaÃ§Ã£o e execuÃ§Ã£o do coletor refatorado API Creare (60d, janelas 7d, deduplicaÃ§Ã£o, fallback access_token)
#>

# 0) Definir repositÃ³rio/projeto
$repo = 'C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard' Set-Location $repo
Write-Host '' -ForegroundColor Green

# 1) Preparar ambiente
if (-not (Test-Path ".\venv")) {
  Write-Host '' -ForegroundColor Yellow
  python -m venv venv
}
Write-Host '' -ForegroundColor Green

# 2) Ativar venv
$activate = ".\venv\Scripts\Activate.ps1"
. $activate
Write-Host '' -ForegroundColor Green

# 3) DependÃªncias
$pkgs = @("requests","urllib3","fastapi","uvicorn")
foreach ($p in $pkgs) {
  if (-not (pip list | Select-String "^\s*$p\s")) {
    Write-Host '' -ForegroundColor Yellow
    pip install $p --quiet
  } else {
    Write-Host '' -ForegroundColor Green
  }
}

# 4) Gerar coletor refatorado
$collectorPy = @' PASTE_PY_HERE
'@
$collectorFixed = $collectorPy -replace 'PASTE_PY_HERE','' # ObservaÃ§Ã£o: substituiremos o marcador abaixo por conteÃºdo real programaticamente

# Como nÃ£o podemos colar o Python inteiro dentro do here-string acima com marcador,
# vamos escrever o arquivo diretamente (mais robusto para caracteres especiais):
$collectorFile = "creare_collector_refactor.py"
@"
# -*- coding: utf-8 -*-
$(Get-Content -Raw -Path "$PSScriptRoot\creare_collector_refactor.py.template" -ErrorAction SilentlyContinue)
"@ | Out-File -FilePath $collectorFile -Encoding UTF8

# Fallback: se o arquivo .template nÃ£o existir, gravar o conteÃºdo diretamente
if (-not (Test-Path $collectorFile) -or ((Get-Item $collectorFile).Length -lt 1000)) {
    @"
REPLACE_WITH_PY
"@ | Out-File -FilePath $collectorFile -Encoding UTF8
    (Get-Content $collectorFile) | Set-Content $collectorFile  # normalizar EOL
}

# 5) Se nÃ£o houver template, substitua com conteÃºdo inline agora
# Para simplificar: escreveremos direto o conteÃºdo do coletor aqui:
$pythonInline = @"
# -*- coding: utf-8 -*-
import os, json, time, urllib3, requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# ConteÃºdo substituÃ­do no passo final do assistente
"@
# Se o arquivo ainda estiver muito pequeno, alertar:
if ((Get-Item $collectorFile).Length -lt 2000) {
  Write-Host '' -ForegroundColor Yellow
} else {
  Write-Host '' -ForegroundColor Green
}

# 6) Executar coleta
Write-Host '' -ForegroundColor Cyan
python $collectorFile

# 7) Exibir resultado
if (Test-Path "creare_data\collection_summary.json") {
  $sum = Get-Content "creare_data\collection_summary.json" | ConvertFrom-Json
  Write-Host '' -ForegroundColor Yellow
  Write-Host '' -ForegroundColor White
  Write-Host '' -ForegroundColor White
  Write-Host '' -ForegroundColor White
  Write-Host '' -ForegroundColor White
} else {
  Write-Host '' -ForegroundColor Yellow
}

Write-Host '' -ForegroundColor Green



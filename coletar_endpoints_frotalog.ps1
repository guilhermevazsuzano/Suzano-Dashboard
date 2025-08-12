<#
.SYNOPSIS
    Coleta todos os endpoints Frotalog liberados e grava JSONs em data_api\

.EXAMPLE
    PS> Set-ExecutionPolicy -Scope Process Bypass -Force
    PS> .\coletar_endpoints_frotalog.ps1
#>

param(
    [string]$ClienteId     = "56963",
    [string]$ClienteSecret = "1MSiBaH879w=",
    [string]$ChildId       = "39450",
    [string]$VehicleId     = "12345"
)

# ”€”€ 0. Entrar na pasta do projeto ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
$projPath = "C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard"
Set-Location $projPath

# ”€”€ 1. PrÃ©-requisitos ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
Write-Host "`nðŸ” Verificando Python..." -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python nÃ£o encontrado no PATH."
}

# ”€”€ 2. Pasta de saÃ­da ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
$dataDir = Join-Path $PWD "data_api"
if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory $dataDir | Out-Null }

# ”€”€ 3. Gerar/atualizar collect_api_data.py ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
$pyFile = Join-Path $PWD "collect_api_data.py"
$pyContent = @"
import os, json, requests, base64, urllib3
from datetime import datetime, timedelta
urllib3.disable_warnings()                         # ignora SSL

CID   = "$($ClienteId)"
CSEC  = "$($ClienteSecret)"
CHILD = "$($ChildId)"
VEH   = "$($VehicleId)"

TOKEN_URL = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
URL_SPE   = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"
URL_BAS   = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
OUT_DIR   = "data_api"
os.makedirs(OUT_DIR, exist_ok=True)

def get_token():
    basic = base64.b64encode(f"{CID}:{CSEC}".encode()).decode()
    r = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {basic}"},
        json={"grant_type": "client_credentials"},
        timeout=30,
        verify=False               # ignora certificado
    )
    r.raise_for_status()
    return r.json()["id_token"]

now  = datetime.utcnow()
d30  = (now - timedelta(days=30)).isoformat() + "Z"
d07  = (now - timedelta(days=7 )).isoformat() + "Z"
nowZ =  now.isoformat() + "Z"

EP_SPE = {
    "/customers": {},
    "/customers/custom-columns-definitions": {"customerId": CHILD},
    "/customers/profile": {"customerChildId": CHILD},
    "/events/by-page": {
        "customerChildIds": CHILD, "fromTimestamp": d30, "toTimestamp": nowZ,
        "pageSize": 1000, "page": 1, "isDetailed": True
    },
    "/events/latest": {"customerChildIds": CHILD},
    "/events/types": {},
    "/events/types/groups": {},
    "/events/vehicle-charging": {"customerChildIds": CHILD, "fromTimestamp": d07, "toTimestamp": nowZ},
    "/working-hours": {"fromTimestamp": d07, "toTimestamp": nowZ},
    "/working-hours/details": {"fromTimestamp": d07, "toTimestamp": nowZ},
    "/pontos-notaveis/by-updated": {"startUpdatedAtTimestamp": d07, "endUpdatedAtTimestamp": nowZ}
}

EP_BAS = {
    "/drivers": {},
    "/fences/embeddedfences": {"listCustomerChildId": CHILD},
    "/fences/poi": {"listCustomerChildId": CHILD},
    "/infractions": {"customerChildIds": CHILD, "fromTimestamp": d30, "toTimestamp": nowZ},
    "/infractions/types": {},
    "/journeys": {"customerChildIds": CHILD, "fromTimestamp": d30, "toTimestamp": nowZ},
    "/tracking/latest": {"customerId": CHILD},
    "/vehicles": {"customerId": CHILD},
    "/vehicles/config": {"vehicleId": VEH},
    "/vehicles/types": {}
}

def fetch(base, ep, params, token):
    url = base + ep
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params,
                     timeout=60, verify=False)
    r.raise_for_status()
    fname = ep.strip("/").replace("/", "_") + ".json"
    with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
        json.dump(r.json(), f, ensure_ascii=False, indent=2)
    print(f"œ” {ep}")

def main():
    token = get_token()
    print("Token OK\\n€” Specialized €”")
    for ep, pr in EP_SPE.items():
        try:
            fetch(URL_SPE, ep, pr, token)
        except Exception as e:
            print(f"Erro em {ep}: {e}")
    print("€” Basic €”")
    for ep, pr in EP_BAS.items():
        try:
            fetch(URL_BAS, ep, pr, token)
        except Exception as e:
            print(f"Erro em {ep}: {e}")
    print(f"\\nœ… Coleta concluÃ­da †’ {OUT_DIR}")

if __name__ == "__main__":
    main()
"@

Set-Content -Path $pyFile -Value $pyContent -Encoding UTF8
Write-Host "ðŸ“ collect_api_data.py atualizado." -ForegroundColor Green

# ”€”€ 4. Executar o coletor ”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€”€
Write-Host "`nðŸš€ Coletando endpoints liberados..." -ForegroundColor Yellow
python $pyFile

Write-Host "`nFim da coleta. JSONs salvos com sucesso!" -ForegroundColor Green -ForegroundColor Green





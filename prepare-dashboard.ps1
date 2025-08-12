<#
.SYNOPSIS
    Prepara novo ambiente seguro do Suzano Dashboard
.DESCRIPTION
    Cria pasta nova, clona (ou copia) repositÃ³rio, aplica ajustes de seguranÃ§a,
    configura venv, Redis via Docker, gera .env e certificado self-signed.
.PARAMETER BasePath
    DiretÃ³rio base onde serÃ¡ criada a nova pasta.
.PARAMETER NewFolder
    Nome da nova pasta a ser criada.
#>
param(
    [string]$BasePath  = "C:\\Users\\guilhermevaz\\OneDrive - Suzano S A\\Documentos",
    [string]$NewFolder = "Suzano-Dashboard-Seguro",
    [string]$RepoUrl   = "https://github.com/guilhermevazsuzano/Suzano-Dashboard.git",
    [int]$RedisPort   = 6379,
    [int]$HttpsPort   = 443,
    [string]$PythonExe = "python"
)

function Assert-Admin {
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")) {
        Write-Error "Execute este script como Administrador."; exit 1
    }
}

$ProjectRoot = Join-Path $BasePath $NewFolder

Assert-Admin

# 1. Criar pasta
if (-not (Test-Path $ProjectRoot)) {
    New-Item -ItemType Directory -Path $ProjectRoot | Out-Null
}
Set-Location $ProjectRoot

# 2. Clonar ou copiar projeto
if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    git clone $RepoUrl .
}

# 3. Instalar Chocolatey & Redis (Docker)
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [Net.ServicePointManager]::SecurityProtocol = 3072
    Invoke-Expression (Invoke-WebRequest -UseBasicParsing 'https://chocolatey.org/install.ps1').Content
}

docker ps 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "Docker Desktop Ã© necessÃ¡rio."; exit 1 }
if (-not (docker ps -a --format "{{.Names}}" | Select-String -Pattern "^redis$")) {
    docker run -d --name redis -p $RedisPort:6379 redis:latest
}

# 4. Criar venv e instalar dependÃªncias
& $PythonExe -m venv .\venv
& .\venv\Scripts\activate

$requirements = @"fastapi
uvicorn[standard]
office365-rest-python-client
python-dotenv
redis
aiohttp
structlog
python-jose[cryptography]
pytest
pydantic
"@
$requirements | Out-File "requirements.txt" -Encoding utf8
pip install --upgrade pip
pip install -r requirements.txt

# 5. Gerar .env
if (-not (Test-Path ".env")) {
    $secret = [guid]::NewGuid().ToString("N")
    @"# Dashboard .env
SHAREPOINT_SITE_URL=https://suzano.sharepoint.com/sites/Controleoperacional
SHAREPOINT_USERNAME=
SHAREPOINT_PASSWORD=
CREARE_CLIENT_ID=
CREARE_CLIENT_SECRET=
CREARE_CUSTOMER_CHILD_ID=39450
JWT_SECRET=$secret
REDIS_HOST=localhost
REDIS_PORT=$RedisPort
SSL_CERT_PATH=certs\dashboard.crt
SSL_KEY_PATH=certs\dashboard.key
"@ | Out-File ".env" -Encoding utf8
}

# 6. Gerar certificado self-signed
if (-not (Test-Path "certs")) { New-Item -ItemType Directory -Path "certs" | Out-Null }
if (-not (Test-Path "certs\dashboard.crt")) {
    $cert = New-SelfSignedCertificate -DnsName "localhost" -CertStoreLocation "cert:\\LocalMachine\\My" -FriendlyName "SuzanoDashboardCert"
    $pwd = ConvertTo-SecureString "SuzanoDashboard!" -AsPlainText -Force
    Export-PfxCertificate -Cert "cert:\\LocalMachine\\My\\$($cert.Thumbprint)" -FilePath "certs\\temp.pfx" -Password $pwd
    choco install openssl.light -y
    openssl pkcs12 -in "certs\\temp.pfx" -nokeys -out "certs\\dashboard.crt" -passin pass:SuzanoDashboard!
    openssl pkcs12 -in "certs\\temp.pfx" -nocerts -out "certs\\dashboard.key" -nodes -passin pass:SuzanoDashboard!
    Remove-Item "certs\\temp.pfx"
}

# 7. Smoke test
$env:VENV_PYTHON = "$ProjectRoot\\venv\\Scripts\\python.exe"
$srv = Start-Process -FilePath $env:VENV_PYTHON -ArgumentList "-m uvicorn dashboard_backend:app --host 0.0.0.0 --port $HttpsPort --ssl-keyfile certs\\dashboard.key --ssl-certfile certs\\dashboard.crt" -PassThru -WindowStyle Hidden
Start-Sleep 10
try { Invoke-WebRequest -Uri https://localhost:$HttpsPort/health -SkipCertificateCheck | Out-Null; Write-Host "Smoke test OK." } catch { Write-Error "Falha no teste." }
$srv | Stop-Process -ErrorAction SilentlyContinue

Write-Host "\n==== Ambiente pronto em $ProjectRoot. Inicie com:\n.\\venv\\Scripts\\activate; uvicorn dashboard_backend:app --host 0.0.0.0 --port $HttpsPort --ssl-keyfile certs\\dashboard.key --ssl-certfile certs\\dashboard.crt"


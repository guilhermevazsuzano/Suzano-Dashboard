# ░█▀█░█░█░█▀▀░█─░█▀▀░█▄─░   run-suzano.ps1  (PowerShell 5.1+)
param(
    [string]$ProjectPath   = "C:\Suzano-Dashboard-Unified",
    [string]$ClientId      = "56963",
    [string]$ClientSecret  = "1MSiBaH879w=",
    [string]$CustomerId    = "39450",
    [string]$OpenIdUrl     = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR",
    [switch]$IgnoreSsl,                     # –IgnoreSsl para ambiente corporativo com proxy
    [int]   $BackDays      = 180,           # carga inicial (6 meses)
    [int]   $JobMinutes    = 30             # incremental cada 30 min
)
$ErrorActionPreference = "Stop"
$Log = Join-Path $ProjectPath "run-suzano.log"
Start-Transcript -Path $Log -Append

Write-Host "`n=== SUZANO DASHBOARD – EXECUÇÃO COMPLETA (`$(Get-Date)) ===" -ForegroundColor Cyan
Set-Location $ProjectPath

# 1. venv
$Venv = Join-Path $ProjectPath "venv"
if (-not (Test-Path $Venv)) { python -m venv $Venv }
. (Join-Path $Venv "Scripts\Activate.ps1")          # ativa

# 2. pip
pip install --quiet --upgrade pip `
    fastapi==0.104.1 uvicorn[standard]==0.24.0 requests==2.31.0 `
    pandas==2.1.4 diskcache==5.6.3 office365-rest-python-client==2.3.11

# 3.  módulos PS para SharePoint
if (-not (Get-Module -ListAvailable Pnp.PowerShell)) {
    Install-Module Pnp.PowerShell -Scope CurrentUser -Force -ErrorAction SilentlyContinue
}

# 4.  Funções helpers (token, coleta, etc.)  -------------------------------
function Get-CreareToken {
    param($Id, $Secret, $Url, [switch]$SkipSsl)
    if ($SkipSsl) { [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true} }
    $basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("$Id`:$Secret"))
    $body  = @{ grant_type = "client_credentials" } | ConvertTo-Json
    (Invoke-RestMethod -Method Post -Uri $Url `
        -Headers @{ Authorization = "Basic $basic"; "Content-Type" = "application/json" } `
        -Body $body -TimeoutSec 30).id_token
}

function Collect-CreareEvents {
    param($Token, $FromIso, $ToIso)
    $url = "https://api.crearecloud.com.br/frotalog/specialized-services/v3/events/by-page"
    $events = @()
    $page   = 1
    do {
        $resp = Invoke-RestMethod -Uri $url -Method Get -Headers @{ Authorization = "Bearer $Token" } `
               -Body @{ customerChildIds = $CustomerId; fromTimestamp = $FromIso; toTimestamp = $ToIso;
                         pageSize = 1000; page = $page; isDetailed = $true; sort = "ASC" } `
               -TimeoutSec 90 -SkipCertificateCheck:$IgnoreSsl
        $events += $resp.content
        $page++
    } until ($resp.last -or !$resp.content)
    return $events
}

function Collect-SharePointList {
    param($Site, $List)
    Connect-PnPOnline -Url $Site -Interactive
    Get-PnPListItem -List $List | Select -ExpandField FieldValues
}

# 5.  Diretórios de cache ---------------------------------------------------
$Cache    = Join-Path $ProjectPath "cache"
$EventsJs = Join-Path $Cache "events_6m.json"
$SpDir    = Join-Path $Cache "sharepoint"
$null = New-Item $Cache -ItemType Directory -Force
$null = New-Item $SpDir -ItemType Directory -Force

# 6. Carga inicial Creare (apenas se não existir)
if (-not (Test-Path $EventsJs)) {
    Write-Host "Coletando $BackDays dias de eventos Creare..."
    $token = Get-CreareToken $ClientId $ClientSecret $OpenIdUrl -SkipSsl:$IgnoreSsl
    $from  = (Get-Date).AddDays(-$BackDays).ToUniversalTime().ToString("o")
    $to    = (Get-Date).ToUniversalTime().ToString("o")
    $evt   = Collect-CreareEvents $token $from $to
    $evt | ConvertTo-Json -Depth 5 | Out-File $EventsJs -Encoding UTF8
    Write-Host "$($evt.Count) eventos salvos em $EventsJs"
}

# 7. Coletar SharePoint (3 listas) -----------------------------------------
$Site   = "https://suzano.sharepoint.com/sites/SeuSite"
$lists  = "ListaEventos","ListaVeiculos","ListaAlertas"
foreach ($l in $lists) {
    $out = Join-Path $SpDir "$l.json"
    if (-not (Test-Path $out)) {
        $data = Collect-SharePointList $Site $l
        $data | ConvertTo-Json -Depth 5 | Out-File $out -Encoding UTF8
        Write-Host "Lista $l salva em cache."
    }
}

# 8. Job incremental Creare a cada $JobMinutes -----------------------------
$job = Get-ScheduledTask -TaskName "SuzanoCreareIncremental" -ErrorAction SilentlyContinue
if (-not $job) {
    $action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument `
      "-NoLogo -NoProfile -ExecutionPolicy Bypass -Command `"& {
          param(`$pth,`$cid,`$sec,`$cus,`$url,`$cache,`$skip)
          Import-Module Microsoft.PowerShell.Utility
          `$tok = (Get-CreareToken `$cid `$sec `$url -SkipSsl:`$skip)
          `$from = (Get-Date).AddMinutes(-$using:JobMinutes).ToUniversalTime().ToString('o')
          `$to   = (Get-Date).ToUniversalTime().ToString('o')
          `$new  = Collect-CreareEvents `$tok `$from `$to
          if (`$new) {
              `$arr = Get-Content `$cache | ConvertFrom-Json
              `$arr += `$new
              `$arr | ConvertTo-Json -Depth 5 | Set-Content `$cache -Encoding UTF8
          }
      }`" -pth '$ProjectPath' -cid '$ClientId' -sec '$ClientSecret' `
         -cus '$CustomerId' -url '$OpenIdUrl' -cache '$EventsJs' -skip:`$true"
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $JobMinutes)
    Register-ScheduledTask -TaskName "SuzanoCreareIncremental" -Action $action -Trigger $trigger -Description "Incremental API Creare" | Out-Null
    Write-Host "Job incremental criado (cada $JobMinutes min)."
}

# 9. Iniciar API - FastAPI --------------------------------------------------
$Api = {
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}
Start-Process -WindowStyle Minimized powershell "-NoLogo -NoProfile -Command `$env:PYTHONPATH='.'; $Api"

# 10. Servir dashboard estático (porta 8080) -------------------------------
Start-Process -WindowStyle Minimized powershell "-NoLogo -NoProfile -Command cd '$ProjectPath\dashboard'; python -m http.server 8080"

Write-Host "`nSERVIÇOS INICIADOS:"
Write-Host "• API FastAPI ........ http://localhost:8000/docs"
Write-Host "• Dashboard HTML .... http://localhost:8080"

Stop-Transcript


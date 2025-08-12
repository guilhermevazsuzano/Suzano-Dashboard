# Script de validaÃ§Ã£o automÃ¡tica do dashboard
# Executar apÃ³s setup_suzano_dashboard.ps1

Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Yellow

$baseUrl = "http://localhost:8000"
$endpoints = @(
    "/api/status",
    "/api/sharepoint-data", 
    "/api/creare-data",
    "/api/metrics"
)

Write-Host '' -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host '' -ForegroundColor Yellow

foreach ($endpoint in $endpoints) {
    $url = "$baseUrl$endpoint"
    Write-Host '' -ForegroundColor White
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
        
        if ($response.success -eq $true -or $endpoint -eq "/api/status") {
            Write-Host '' -ForegroundColor Green
            
            # Mostrar dados relevantes
            switch ($endpoint) {
                "/api/status" {
                    Write-Host '' -ForegroundColor Gray
                    Write-Host '' -ForegroundColor Gray
                    Write-Host '' -ForegroundColor Gray
                }
                "/api/sharepoint-data" {
                    $spData = $response.data
                    if ($spData.lists) {
                        $total = 0
                        foreach ($list in $spData.lists.PSObject.Properties.Name) {
                            $count = $spData.lists.$list.Count
                            $total += $count
                            Write-Host '' -ForegroundColor Gray
                        }
                        Write-Host '' -ForegroundColor Cyan
                    }
                }
                "/api/creare-data" {
                    $creareData = $response.data
                    Write-Host '' -ForegroundColor Gray
                    Write-Host '' -ForegroundColor Gray
                    Write-Host '' -ForegroundColor Gray
                }
                "/api/metrics" {
                    $metrics = $response.metrics
                    Write-Host '' -ForegroundColor Gray
                    Write-Host '' -ForegroundColor Gray
                    Write-Host '' -ForegroundColor Gray
                    Write-Host '' -ForegroundColor Gray
                }
            }
        } else {
            Write-Host '' -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host '' -ForegroundColor Red
    }
}

Write-Host '' -ForegroundColor Yellow
try {
    $htmlResponse = Invoke-WebRequest -Uri $baseUrl -TimeoutSec 10
    if ($htmlResponse.StatusCode -eq 200) {
        Write-Host '' -ForegroundColor Green
        
        # Verificar se contÃ©m elementos esperados
        $content = $htmlResponse.Content
        $checks = @(
            @{ Pattern = "Total de Desvios"; Name = "Card Desvios" },
            @{ Pattern = "Alertas Ativos"; Name = "Card Alertas" },
            @{ Pattern = "EficiÃªncia"; Name = "Card EficiÃªncia" },
            @{ Pattern = "/api/metrics"; Name = "Chamada API Metrics" }
        )
        
        foreach ($check in $checks) {
            if ($content -match $check.Pattern) {
                Write-Host '' -ForegroundColor Green
            } else {
                Write-Host '' -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host '' -ForegroundColor Red
}

Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Yellow

# Contar arquivos gerados
$spFiles = Get-ChildItem -Path . -Include "sharepoint_complete_data_*.json" -File
$creareFiles = if (Test-Path "creare_data") { Get-ChildItem "creare_data\*.json" } else { @() }

Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White
Write-Host '' -ForegroundColor White

Write-Host '' -ForegroundColor Green
Write-Host '' -ForegroundColor Cyan
Write-Host ""
Write-Host '' -ForegroundColor Yellow
Write-Host '' -ForegroundColor White


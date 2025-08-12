# PowerShell Script para Diagnóstico e Mapeamento de APIs Frotalog
# Caminho do projeto: C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard

param(
    [string]$OutputPath = ".\api-endpoints.json",
    [string]$ClientId = $env:FROTALOG_CLIENT_ID,
    [string]$ClientSecret = $env:FROTALOG_CLIENT_SECRET
)

# Configurações das APIs
$APIs = @{
    "Frotalog Basic" = @{
        BaseUrl = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
        Endpoints = @(
            "/drivers",
            "/drivers/by-cpf/{cpf}",
            "/drivers/{id}",
            "/drivers/{id}/attachments/{attachmentId}",
            "/drivers/{id}/attachments/driver-attachment-types",
            "/drivers/{id}/attachments/list",
            "/fences/embeddedfences",
            "/fences/remotefences", 
            "/fences/poi",
            "/fences/logisticfences",
            "/fences/speechfences",
            "/infractions",
            "/infractions/types",
            "/journeys",
            "/tracking",
            "/tracking/latest",
            "/vehicles",
            "/vehicles/config",
            "/vehicles/types",
            "/vehicles/{id}",
            "/vehicles/fences/{id}/embeddedfences",
            "/vehicles/fences/{id}/poi",
            "/vehicles/fences/{id}/remotefences",
            "/vehicles/config-details",
            "/users/{userId}/hierarchy"
        )
    }
    "Frotalog Specialized" = @{
        BaseUrl = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"
        Endpoints = @(
            "/customers",
            "/customers/custom-columns-definitions",
            "/customers/profile",
            "/events",
            "/events/latest",
            "/events/by-page",
            "/events/approvals",
            "/events/types",
            "/events/types/groups",
            "/events/types/{id}",
            "/events/vehicle-charging",
            "/messages/assets/{vehicleId}",
            "/messages/default",
            "/messages/{id}",
            "/traffic-tickets",
            "/working-hours",
            "/working-hours/details",
            "/pontos-notaveis/by-updated"
        )
    }
    "GoAwake Public" = @{
        BaseUrl = "https://api-pub.crearecloud.com.br/goawake"
        AuthUrl = "https://iam-gru.crearecloud.com.br/realms/customers/protocol/openid-connect/token"
        Endpoints = @(
            "/alarm",
            "/alarm/{alarmId}",
            "/alarm/offset",
            "/alarm/history/{alarmId}",
            "/vehicle"
        )
    }
    "GoAwake DW" = @{
        BaseUrl = "https://api.goawakecloud.com.br/dw/1.0"
        Endpoints = @(
            "/alarms",
            "/Vehicles"
        )
    }
}

# Configuração de autenticação
$AuthConfig = @{
    TokenUrl = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
    GrantType = "client_credentials"
}

class AuthClient {
    [string]$ClientId
    [string]$ClientSecret
    [string]$TokenUrl
    [string]$AccessToken
    [DateTime]$TokenExpiry

    AuthClient([string]$clientId, [string]$clientSecret, [string]$tokenUrl) {
        $this.ClientId = $clientId
        $this.ClientSecret = $clientSecret
        $this.TokenUrl = $tokenUrl
    }

    [string] GetToken() {
        if ($this.AccessToken -and $this.TokenExpiry -gt (Get-Date)) {
            return $this.AccessToken
        }

        try {
            Write-Host "AuthClient: Solicitando token de acesso..." -ForegroundColor Yellow
            
            # Codificar credenciais em Base64
            $credentials = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("$($this.ClientId):$($this.ClientSecret)"))
            
            $headers = @{
                "Authorization" = "Basic $credentials"
                "Content-Type" = "application/json"
            }

            $body = @{
                grant_type = "client_credentials"
            } | ConvertTo-Json

            $response = Invoke-RestMethod -Uri $this.TokenUrl -Method Post -Headers $headers -Body $body
            
            $this.AccessToken = $response.id_token
            $this.TokenExpiry = (Get-Date).AddSeconds($response.expires_in - 60) # Renovar 1 min antes
            
            Write-Host "AuthClient: Token obtido com sucesso!" -ForegroundColor Green
            return $this.AccessToken
        }
        catch {
            Write-Host "Erro ao obter token: $($_.Exception.Message)" -ForegroundColor Red
            throw
        }
    }
}

function Test-APIEndpoint {
    param(
        [string]$BaseUrl,
        [string]$Endpoint,
        [string]$AccessToken,
        [string]$ApiName
    )

    # Substituir parâmetros de path por valores de teste
    $testEndpoint = $Endpoint -replace '\{cpf\}', '00000000000'
    $testEndpoint = $testEndpoint -replace '\{id\}', '12345'
    $testEndpoint = $testEndpoint -replace '\{userId\}', '12345'
    $testEndpoint = $testEndpoint -replace '\{vehicleId\}', '12345'
    $testEndpoint = $testEndpoint -replace '\{alarmId\}', '12345'
    $testEndpoint = $testEndpoint -replace '\{attachmentId\}', '12345'

    $fullUrl = "$BaseUrl$testEndpoint"

    try {
        $headers = @{
            "Authorization" = "Bearer $AccessToken"
            "Content-Type" = "application/json"
        }

        # Para endpoints que requerem parâmetros obrigatórios, adicionar query params básicos
        if ($testEndpoint -match "custom-columns-definitions|profile|approvals|traffic-tickets|by-updated|working-hours") {
            if ($testEndpoint -match "custom-columns-definitions") {
                $fullUrl += "?customerId=1"
            }
            elseif ($testEndpoint -match "profile") {
                $fullUrl += "?customerChildId=1"
            }
            elseif ($testEndpoint -match "approvals") {
                $fullUrl += "?customerChildId=1&fromDate=2025-01-01T00:00:00.000Z&toDate=2025-01-02T00:00:00.000Z"
            }
            elseif ($testEndpoint -match "traffic-tickets") {
                $fullUrl += "?pageNumber=1&pageSize=10"
            }
            elseif ($testEndpoint -match "by-updated") {
                $fullUrl += "?startUpdatedAtTimestamp=2025-01-01T00:00:00.000Z&endUpdatedAtTimestamp=2025-01-02T00:00:00.000Z"
            }
            elseif ($testEndpoint -match "working-hours" -and $testEndpoint -notmatch "details") {
                $fullUrl += "?fromTimestamp=2025-01-01T00:00:00.000Z&toTimestamp=2025-01-02T00:00:00.000Z"
            }
            elseif ($testEndpoint -match "embeddedfences|remotefences|poi|logisticfences") {
                $fullUrl += "?listCustomerChildId=1"
            }
            elseif ($testEndpoint -match "messages/default") {
                $fullUrl += "?vehicleId=12345"
            }
            elseif ($testEndpoint -match "vehicle-charging") {
                $fullUrl += "?fromTimestamp=2025-01-01T00:00:00.000Z&toTimestamp=2025-01-02T00:00:00.000Z"
            }
        }

        $response = Invoke-RestMethod -Uri $fullUrl -Method Get -Headers $headers -TimeoutSec 10
        
        return @{
            Status = "✅ Sim"
            HasAccess = $true
            Error = $null
            Endpoint = $Endpoint
            TestUrl = $fullUrl
        }
    }
    catch {
        $errorMessage = $_.Exception.Message
        $statusCode = $null
        
        if ($_.Exception -is [System.Net.WebException]) {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
        elseif ($_.ErrorDetails) {
            $errorDetails = $_.ErrorDetails | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($errorDetails) {
                $statusCode = $errorDetails.status
            }
        }

        $status = switch ($statusCode) {
            400 { "❌ Não (Erro 400)" }
            401 { "❌ Não (Não Autorizado)" }
            403 { "❌ Não (Acesso Negado)" }
            404 { "✅ Sim (Endpoint Válido)" }  # 404 pode significar que o endpoint existe mas o recurso não
            default { "❌ Não (Erro $statusCode)" }
        }

        # Se o erro for 404 em endpoints parametrizados, consideramos como válido
        if ($statusCode -eq 404 -and ($Endpoint -match '\{.*\}')) {
            return @{
                Status = "✅ Sim (Endpoint Válido)"
                HasAccess = $true
                Error = "404 - Recurso não encontrado (endpoint válido)"
                Endpoint = $Endpoint
                TestUrl = $fullUrl
            }
        }

        return @{
            Status = $status
            HasAccess = $false
            Error = $errorMessage
            Endpoint = $Endpoint
            TestUrl = $fullUrl
        }
    }
}

function Start-APIDiagnostics {
    param(
        [string]$ClientId,
        [string]$ClientSecret
    )

    if (-not $ClientId -or -not $ClientSecret) {
        Write-Host "❌ Erro: CLIENT_ID e CLIENT_SECRET são obrigatórios!" -ForegroundColor Red
        Write-Host "Use: .\api-diagnostics.ps1 -ClientId 'seu_client_id' -ClientSecret 'seu_client_secret'" -ForegroundColor Yellow
        return
    }

    Write-Host "🔍 INICIANDO DIAGNÓSTICO DE ACESSO ÀS APIs FROTALOG" -ForegroundColor Cyan
    Write-Host "=" * 60

    $results = @()
    $authClient = [AuthClient]::new($ClientId, $ClientSecret, $AuthConfig.TokenUrl)

    try {
        $accessToken = $authClient.GetToken()
    }
    catch {
        Write-Host "❌ Falha na autenticação. Verificar credenciais." -ForegroundColor Red
        return
    }

    foreach ($apiName in $APIs.Keys) {
        $api = $APIs[$apiName]
        
        Write-Host "`n🔧 Testando API: $apiName" -ForegroundColor Magenta
        
        foreach ($endpoint in $api.Endpoints) {
            Write-Host "-- Testando: $apiName - GET $endpoint" -ForegroundColor White
            
            $result = Test-APIEndpoint -BaseUrl $api.BaseUrl -Endpoint $endpoint -AccessToken $accessToken -ApiName $apiName
            
            Write-Host "   Resultado: $($result.Status)" -ForegroundColor $(if ($result.HasAccess) { "Green" } else { "Red" })
            
            $results += [PSCustomObject]@{
                API = $apiName
                Method = "GET"
                Endpoint = $endpoint
                BaseUrl = $api.BaseUrl
                HasAccess = $result.HasAccess
                Status = $result.Status
                Error = $result.Error
                TestUrl = $result.TestUrl
                TestedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            }
        }
    }

    # Exibir resumo
    Write-Host "`n" + "=" * 60 -ForegroundColor Cyan
    Write-Host "📊 RESUMO DO DIAGNÓSTICO" -ForegroundColor Cyan
    Write-Host "=" * 60

    $summary = $results | Group-Object HasAccess | ForEach-Object {
        [PSCustomObject]@{
            Status = if ($_.Name -eq "True") { "✅ Com Acesso" } else { "❌ Sem Acesso" }
            Count = $_.Count
        }
    }

    $summary | Format-Table -AutoSize

    # Criar JSON de saída
    $output = @{
        DiagnosticInfo = @{
            GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            TotalEndpoints = $results.Count
            AccessibleEndpoints = ($results | Where-Object { $_.HasAccess }).Count
            InaccessibleEndpoints = ($results | Where-Object { -not $_.HasAccess }).Count
        }
        APIs = @{}
        DetailedResults = $results
    }

    # Organizar por API
    foreach ($apiName in $APIs.Keys) {
        $apiResults = $results | Where-Object { $_.API -eq $apiName }
        $accessibleEndpoints = $apiResults | Where-Object { $_.HasAccess }
        
        $output.APIs[$apiName] = @{
            BaseUrl = $APIs[$apiName].BaseUrl
            TotalEndpoints = $apiResults.Count
            AccessibleEndpoints = $accessibleEndpoints.Count
            AccessibleEndpointsList = @($accessibleEndpoints | ForEach-Object { 
                @{
                    Endpoint = $_.Endpoint
                    Method = $_.Method
                    Status = $_.Status
                    FullUrl = "$($_.BaseUrl)$($_.Endpoint)"
                }
            })
            InaccessibleEndpoints = @($apiResults | Where-Object { -not $_.HasAccess } | ForEach-Object {
                @{
                    Endpoint = $_.Endpoint
                    Method = $_.Method
                    Status = $_.Status
                    Error = $_.Error
                }
            })
        }
    }

    # Salvar JSON
    $jsonOutput = $output | ConvertTo-Json -Depth 10
    $jsonOutput | Out-File -FilePath $OutputPath -Encoding UTF8

    Write-Host "`n✅ Diagnóstico concluído!" -ForegroundColor Green
    Write-Host "📄 Resultado salvo em: $OutputPath" -ForegroundColor Green
    Write-Host "📊 Total de endpoints testados: $($results.Count)" -ForegroundColor White
    Write-Host "✅ Endpoints acessíveis: $(($results | Where-Object { $_.HasAccess }).Count)" -ForegroundColor Green
    Write-Host "❌ Endpoints inacessíveis: $(($results | Where-Object { -not $_.HasAccess }).Count)" -ForegroundColor Red

    return $output
}

# Execução principal
if ($ClientId -and $ClientSecret) {
    Start-APIDiagnostics -ClientId $ClientId -ClientSecret $ClientSecret
} else {
    Write-Host "🔧 SCRIPT DE DIAGNÓSTICO DE APIs FROTALOG" -ForegroundColor Cyan
    Write-Host "=" * 50
    Write-Host ""
    Write-Host "📋 Uso:" -ForegroundColor Yellow
    Write-Host "  .\api-diagnostics.ps1 -ClientId 'seu_client_id' -ClientSecret 'seu_client_secret'" -ForegroundColor White
    Write-Host ""
    Write-Host "🔐 Ou configure as variáveis de ambiente:" -ForegroundColor Yellow
    Write-Host "  `$env:FROTALOG_CLIENT_ID = 'seu_client_id'" -ForegroundColor White
    Write-Host "  `$env:FROTALOG_CLIENT_SECRET = 'seu_client_secret'" -ForegroundColor White
    Write-Host "  .\api-diagnostics.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "📄 O resultado será salvo em: $OutputPath" -ForegroundColor Green
}
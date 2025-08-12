# API Diagnostic Tool for Frotalog APIs
# Script PowerShell para testar conectividade e gerar JSON com APIs disponíveis
# Guilherme Vaz - Suzano S.A.

param(
    [string]$OutputPath = "apis-disponíveis.json",
    [string]$ClientId = "",
    [string]$ClientSecret = "",
    [switch]$SkipTests,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Configurações das APIs
$APIs = @{
    "FrotalogSpecialized" = @{
        Name = "Frotalog Specialized Services"
        BaseUrl = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"
        AuthUrl = "https://openid-provider.crearecloud.com.br/auth/v1/token"
        Endpoints = @(
            @{ Method = "GET"; Path = "/customers"; RequiredParams = @(); OptionalParams = @("customerId") }
            @{ Method = "GET"; Path = "/customers/custom-columns-definitions"; RequiredParams = @("customerId"); OptionalParams = @() }
            @{ Method = "GET"; Path = "/customers/profile"; RequiredParams = @("customerChildId"); OptionalParams = @() }
            @{ Method = "GET"; Path = "/events/by-page"; RequiredParams = @("fromTimestamp", "toTimestamp"); OptionalParams = @("vehicleId", "driverId", "customerChildIds", "page", "size", "sort", "isDetailed") }
            @{ Method = "GET"; Path = "/events/latest"; RequiredParams = @(); OptionalParams = @("vehicleId", "driverId", "customerChildIds", "fromTimestamp") }
            @{ Method = "GET"; Path = "/events/approvals"; RequiredParams = @("customerChildId", "fromDate", "toDate"); OptionalParams = @("vehicleId", "pending", "detailed", "reverseGeocoding") }
            @{ Method = "GET"; Path = "/events/types"; RequiredParams = @(); OptionalParams = @() }
            @{ Method = "GET"; Path = "/events/types/groups"; RequiredParams = @(); OptionalParams = @("recursive", "vehicleId") }
            @{ Method = "GET"; Path = "/events/types/{id}"; RequiredParams = @("id"); OptionalParams = @(); PathParams = @("id") }
            @{ Method = "GET"; Path = "/events/vehicle-charging"; RequiredParams = @("fromTimestamp", "toTimestamp"); OptionalParams = @("vehicleId", "customerChildIds", "sort") }
            @{ Method = "GET"; Path = "/messages/assets/{vehicleId}"; RequiredParams = @("vehicleId"); OptionalParams = @("fromDatabaseTimestamp", "fromId"); PathParams = @("vehicleId") }
            @{ Method = "GET"; Path = "/messages/default"; RequiredParams = @("vehicleId"); OptionalParams = @() }
            @{ Method = "GET"; Path = "/messages/{id}"; RequiredParams = @("id"); OptionalParams = @(); PathParams = @("id") }
            @{ Method = "GET"; Path = "/traffic-tickets"; RequiredParams = @("pageNumber", "pageSize"); OptionalParams = @() }
            @{ Method = "GET"; Path = "/working-hours"; RequiredParams = @("fromTimestamp", "toTimestamp"); OptionalParams = @("page", "size", "sort", "driverId") }
            @{ Method = "GET"; Path = "/working-hours/details"; RequiredParams = @(); OptionalParams = @("driverId", "fromId") }
            @{ Method = "GET"; Path = "/pontos-notaveis/by-updated"; RequiredParams = @("startUpdatedAtTimestamp", "endUpdatedAtTimestamp"); OptionalParams = @("page", "size", "sort", "startTimestamp", "endTimestamp", "fenceId", "vehicleId", "driverDetails", "status") }
        )
    }
    "FrotalogBasic" = @{
        Name = "Frotalog Basic Services"
        BaseUrl = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
        AuthUrl = "https://openid-provider.crearecloud.com.br/auth/v1/token"
        Endpoints = @(
            @{ Method = "GET"; Path = "/drivers"; RequiredParams = @(); OptionalParams = @("customerChildIds", "page", "size", "sort", "isActive") }
            @{ Method = "GET"; Path = "/drivers/by-cpf/{cpf}"; RequiredParams = @("cpf"); OptionalParams = @("isActive"); PathParams = @("cpf") }
            @{ Method = "GET"; Path = "/drivers/{id}"; RequiredParams = @("id"); OptionalParams = @(); PathParams = @("id") }
            @{ Method = "GET"; Path = "/drivers/{driverId}/attachments/{driverAttachmentId}"; RequiredParams = @("driverId", "driverAttachmentId"); OptionalParams = @(); PathParams = @("driverId", "driverAttachmentId") }
            @{ Method = "GET"; Path = "/drivers/{id}/attachments/driver-attachment-types"; RequiredParams = @("id"); OptionalParams = @(); PathParams = @("id") }
            @{ Method = "GET"; Path = "/drivers/{id}/attachments/list"; RequiredParams = @("id"); OptionalParams = @(); PathParams = @("id") }
            @{ Method = "GET"; Path = "/fences/embeddedfences"; RequiredParams = @("listCustomerChildId"); OptionalParams = @("pageNumber", "pageSize", "withChild", "sortOrder") }
            @{ Method = "GET"; Path = "/fences/remotefences"; RequiredParams = @("listCustomerChildId"); OptionalParams = @("pageNumber", "pageSize", "withChild", "sortOrder") }
            @{ Method = "GET"; Path = "/fences/poi"; RequiredParams = @("listCustomerChildId"); OptionalParams = @("pageNumber", "pageSize", "withChild") }
            @{ Method = "GET"; Path = "/fences/logisticfences"; RequiredParams = @("listCustomerChildId"); OptionalParams = @("pageNumber", "pageSize", "withChild", "sortOrder") }
            @{ Method = "GET"; Path = "/fences/speechfences"; RequiredParams = @("listCustomerChildId"); OptionalParams = @("pageNumber", "pageSize", "withChild", "sortOrder") }
            @{ Method = "GET"; Path = "/infractions"; RequiredParams = @(); OptionalParams = @("vehicleId", "driverId", "customerChildIds", "fromTimestamp", "toTimestamp", "fromTimestampInsertion", "toTimestampInsertion", "page", "size", "sort") }
            @{ Method = "GET"; Path = "/infractions/types"; RequiredParams = @(); OptionalParams = @() }
            @{ Method = "GET"; Path = "/journeys"; RequiredParams = @(); OptionalParams = @("vehicleId", "driverId", "customerChildIds", "fromTimestamp", "toTimestamp", "page", "size", "sort") }
            @{ Method = "GET"; Path = "/tracking"; RequiredParams = @(); OptionalParams = @("customerChildIds", "vehicleId", "fromTimestamp") }
            @{ Method = "GET"; Path = "/tracking/latest"; RequiredParams = @(); OptionalParams = @("customerChildIds", "vehicleId") }
            @{ Method = "GET"; Path = "/vehicles"; RequiredParams = @(); OptionalParams = @("customerChildIds", "vehicleId", "vehiclePlate", "isActive", "page", "size", "sort") }
            @{ Method = "GET"; Path = "/vehicles/config"; RequiredParams = @(); OptionalParams = @("vehicleId", "vehiclePlate") }
            @{ Method = "GET"; Path = "/vehicles/types"; RequiredParams = @(); OptionalParams = @() }
            @{ Method = "GET"; Path = "/vehicles/{id}"; RequiredParams = @("id"); OptionalParams = @(); PathParams = @("id") }
            @{ Method = "GET"; Path = "/vehicles/fences/{id}/embeddedfences"; RequiredParams = @("id"); OptionalParams = @("sortOrder"); PathParams = @("id") }
            @{ Method = "GET"; Path = "/vehicles/fences/{id}/poi"; RequiredParams = @("id"); OptionalParams = @(); PathParams = @("id") }
            @{ Method = "GET"; Path = "/vehicles/fences/{id}/remotefences"; RequiredParams = @("id"); OptionalParams = @("sortOrder"); PathParams = @("id") }
            @{ Method = "GET"; Path = "/vehicles/config-details"; RequiredParams = @(); OptionalParams = @("vehicleId", "vehiclePlate") }
            @{ Method = "GET"; Path = "/users/{userId}/hierarchy"; RequiredParams = @("userId"); OptionalParams = @(); PathParams = @("userId") }
        )
    }
    "GoAwake" = @{
        Name = "GoAwake API"
        BaseUrl = "https://api-pub.crearecloud.com.br/goawake"
        AuthUrl = "https://iam-gru.crearecloud.com.br/realms/customers/protocol/openid-connect/token"
        AuthType = "KeycloakOAuth2"
        Endpoints = @(
            @{ Method = "GET"; Path = "/alarm"; RequiredParams = @("startDate", "endDate"); OptionalParams = @("hasAudit", "page", "size", "sort", "customerChildIds") }
            @{ Method = "GET"; Path = "/alarm/{alarmId}"; RequiredParams = @("alarmId"); OptionalParams = @(); PathParams = @("alarmId") }
            @{ Method = "GET"; Path = "/alarm/offset"; RequiredParams = @("offset"); OptionalParams = @("size", "page", "sort", "customerChildIds") }
            @{ Method = "GET"; Path = "/alarm/history/{alarmId}"; RequiredParams = @("alarmId"); OptionalParams = @(); PathParams = @("alarmId") }
            @{ Method = "GET"; Path = "/vehicle"; RequiredParams = @("date", "licensePlate"); OptionalParams = @() }
        )
    }
}

# Função para obter token de autenticação
function Get-AuthToken {
    param(
        [string]$AuthUrl,
        [string]$ClientId,
        [string]$ClientSecret,
        [string]$AuthType = "BasicAuth"
    )
    
    try {
        if ($AuthType -eq "KeycloakOAuth2") {
            # Para GoAwake API (Keycloak)
            $body = @{
                "client_id" = $ClientId
                "client_secret" = $ClientSecret
                "grant_type" = "client_credentials"
            }
            
            $response = Invoke-RestMethod -Uri $AuthUrl -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
            return $response.access_token
        } else {
            # Para APIs Frotalog (Basic Auth + OpenID)
            $credentials = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$ClientId`:$ClientSecret"))
            $headers = @{ "Authorization" = "Basic $credentials" }
            $body = @{ "grant_type" = "client_credentials" } | ConvertTo-Json
            
            $response = Invoke-RestMethod -Uri $AuthUrl -Method POST -Headers $headers -Body $body -ContentType "application/json"
            return $response.id_token
        }
    }
    catch {
        Write-Warning "Erro ao obter token de autenticação: $($_.Exception.Message)"
        return $null
    }
}

# Função para testar endpoint
function Test-Endpoint {
    param(
        [string]$BaseUrl,
        [hashtable]$Endpoint,
        [string]$Token,
        [string]$AuthType = "Bearer"
    )
    
    $path = $Endpoint.Path
    $method = $Endpoint.Method
    
    # Substituir parâmetros de path por valores de teste
    if ($Endpoint.PathParams) {
        foreach ($param in $Endpoint.PathParams) {
            $testValue = switch ($param) {
                "id" { "12345" }
                "cpf" { "00000000000" }
                "userId" { "12345" }
                "vehicleId" { "12345" }
                "driverId" { "12345" }
                "driverAttachmentId" { "12345" }
                "alarmId" { "12345" }
                default { "12345" }
            }
            $path = $path -replace "{$param}", $testValue
        }
    }
    
    $uri = "$BaseUrl$path"
    $headers = @{ "Authorization" = "$AuthType $Token" }
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Method $method -Headers $headers -TimeoutSec 10
        return @{ Success = $true; Status = "200"; Message = "OK" }
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.Value__
        $message = $_.Exception.Message
        
        # Alguns códigos 4xx podem indicar que o endpoint existe mas precisa de parâmetros
        if ($statusCode -in @(400, 422)) {
            return @{ Success = $true; Status = $statusCode; Message = "Endpoint Válido (Precisa de parâmetros)" }
        }
        elseif ($statusCode -eq 404) {
            return @{ Success = $false; Status = $statusCode; Message = "Endpoint não encontrado" }
        }
        elseif ($statusCode -eq 403) {
            return @{ Success = $false; Status = $statusCode; Message = "Acesso Negado" }
        }
        else {
            return @{ Success = $false; Status = $statusCode; Message = $message }
        }
    }
}

# Função principal para diagnóstico
function Start-ApiDiagnostic {
    Write-Host "`n--- INICIANDO DIAGNÓSTICO DE ACESSO ÀS APIs FROTALOG ---" -ForegroundColor Green
    
    if (-not $ClientId -or -not $ClientSecret) {
        Write-Host "⚠️  ATENÇÃO: ClientId e ClientSecret não fornecidos." -ForegroundColor Yellow
        Write-Host "   Para testes completos, execute:" -ForegroundColor Yellow
        Write-Host "   .\api-diagnostic-tool.ps1 -ClientId 'SEU_CLIENT_ID' -ClientSecret 'SEU_CLIENT_SECRET'" -ForegroundColor Cyan
        Write-Host ""
    }
    
    $results = @()
    $availableApis = @{}
    
    foreach ($apiKey in $APIs.Keys) {
        $api = $APIs[$apiKey]
        Write-Host "`n-- Testando API: $($api.Name)" -ForegroundColor Cyan
        
        $token = $null
        if ($ClientId -and $ClientSecret -and -not $SkipTests) {
            Write-Host "   AuthClient: Solicitando token de acesso..." -ForegroundColor Gray
            $authType = if ($api.ContainsKey("AuthType")) { $api.AuthType } else { "BasicAuth" }
            $token = Get-AuthToken -AuthUrl $api.AuthUrl -ClientId $ClientId -ClientSecret $ClientSecret -AuthType $authType
            
            if ($token) {
                Write-Host "   AuthClient: Token obtido com sucesso!" -ForegroundColor Green
            } else {
                Write-Host "   AuthClient: Falha ao obter token!" -ForegroundColor Red
            }
        }
        
        $apiEndpoints = @()
        
        foreach ($endpoint in $api.Endpoints) {
            $endpointName = "$($endpoint.Method) $($endpoint.Path)"
            
            if ($token -and -not $SkipTests) {
                Write-Host "-- Testando: $($api.Name) - $endpointName" -ForegroundColor White
                $testResult = Test-Endpoint -BaseUrl $api.BaseUrl -Endpoint $endpoint -Token $token
                
                $status = if ($testResult.Success) { "✅ Sim" } else { "❌ Não" }
                if ($testResult.Message -ne "OK") {
                    $status += " ($($testResult.Message))"
                }
                
                Write-Host "   Resultado: $status" -ForegroundColor $(if ($testResult.Success) { "Green" } else { "Red" })
                
                $results += @{
                    API = $api.Name
                    Endpoint = $endpointName
                    HasAccess = $testResult.Success
                    Status = $testResult.Status
                    Message = $testResult.Message
                }
                
                if ($testResult.Success) {
                    $apiEndpoints += @{
                        Method = $endpoint.Method
                        Path = $endpoint.Path
                        RequiredParams = $endpoint.RequiredParams
                        OptionalParams = $endpoint.OptionalParams
                        PathParams = if ($endpoint.PathParams) { $endpoint.PathParams } else { @() }
                        FullUrl = "$($api.BaseUrl)$($endpoint.Path)"
                        Tested = $true
                        WorkingStatus = $testResult.Status
                    }
                }
            } else {
                # Adicionar todos os endpoints mesmo sem teste
                $apiEndpoints += @{
                    Method = $endpoint.Method
                    Path = $endpoint.Path
                    RequiredParams = $endpoint.RequiredParams
                    OptionalParams = $endpoint.OptionalParams
                    PathParams = if ($endpoint.PathParams) { $endpoint.PathParams } else { @() }
                    FullUrl = "$($api.BaseUrl)$($endpoint.Path)"
                    Tested = $false
                    WorkingStatus = "Not Tested"
                }
            }
        }
        
        $availableApis[$apiKey] = @{
            Name = $api.Name
            BaseUrl = $api.BaseUrl
            AuthUrl = $api.AuthUrl
            AuthType = if ($api.ContainsKey("AuthType")) { $api.AuthType } else { "BasicAuth" }
            HasValidToken = ($token -ne $null)
            Endpoints = $apiEndpoints
            TotalEndpoints = $apiEndpoints.Count
            WorkingEndpoints = ($apiEndpoints | Where-Object { $_.Tested -and $_.WorkingStatus -in @("200", "400", "422") }).Count
        }
    }
    
    # Exibir resumo
    if ($results.Count -gt 0) {
        Write-Host "`n================" -ForegroundColor Yellow
        Write-Host "             TABELA-RESUMO DE ACESSO ÀS APIs FROTALOG" -ForegroundColor Yellow
        Write-Host "================" -ForegroundColor Yellow
        Write-Host "API`tEndpoint`tTem Acesso?" -ForegroundColor White
        
        for ($i = 0; $i -lt $results.Count; $i++) {
            $result = $results[$i]
            $accessStatus = if ($result.HasAccess) { "✅ Sim" } else { "❌ Não" }
            if ($result.Message -ne "OK" -and $result.Message -ne "Endpoint não encontrado") {
                $accessStatus += " ($($result.Message))"
            }
            Write-Host "$i`t$($result.API)`t$($result.Endpoint)`t$accessStatus"
        }
    }
    
    # Gerar arquivo JSON
    $jsonOutput = @{
        GeneratedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        GeneratedBy = "API Diagnostic Tool - Suzano S.A."
        ClientId = if ($ClientId) { $ClientId.Substring(0, [Math]::Min(10, $ClientId.Length)) + "..." } else { "Not Provided" }
        TestsExecuted = (-not $SkipTests -and $ClientId -and $ClientSecret)
        Summary = @{
            TotalAPIs = $availableApis.Count
            TotalEndpoints = ($availableApis.Values | ForEach-Object { $_.TotalEndpoints } | Measure-Object -Sum).Sum
            WorkingEndpoints = ($availableApis.Values | ForEach-Object { $_.WorkingEndpoints } | Measure-Object -Sum).Sum
        }
        APIs = $availableApis
        TestResults = $results
    }
    
    $jsonOutput | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputPath -Encoding UTF8
    Write-Host "`n📄 Arquivo JSON gerado: $OutputPath" -ForegroundColor Green
    
    # Exibir estatísticas
    Write-Host "`n📊 ESTATÍSTICAS:" -ForegroundColor Cyan
    Write-Host "   • Total de APIs: $($jsonOutput.Summary.TotalAPIs)" -ForegroundColor White
    Write-Host "   • Total de Endpoints: $($jsonOutput.Summary.TotalEndpoints)" -ForegroundColor White
    if ($jsonOutput.TestsExecuted) {
        Write-Host "   • Endpoints Funcionais: $($jsonOutput.Summary.WorkingEndpoints)" -ForegroundColor Green
        Write-Host "   • Taxa de Sucesso: $([math]::Round(($jsonOutput.Summary.WorkingEndpoints / $jsonOutput.Summary.TotalEndpoints) * 100, 1))%" -ForegroundColor Green
    } else {
        Write-Host "   • Testes não executados (credenciais não fornecidas)" -ForegroundColor Yellow
    }
}

# Verificar se está no diretório correto
$expectedPath = "C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard"
if ((Get-Location).Path -ne $expectedPath) {
    Write-Host "⚠️  Mudando para o diretório do projeto..." -ForegroundColor Yellow
    try {
        Set-Location $expectedPath
        Write-Host "✅ Diretório alterado para: $expectedPath" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Erro ao mudar diretório. Continuando no diretório atual: $((Get-Location).Path)" -ForegroundColor Red
    }
}

# Executar diagnóstico
Start-ApiDiagnostic

Write-Host "`n🎉 Diagnóstico concluído!" -ForegroundColor Green
Write-Host "   Para usar as APIs, consulte o arquivo gerado: $OutputPath" -ForegroundColor Cyan
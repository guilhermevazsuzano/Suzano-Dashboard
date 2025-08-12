# Script para executar atualizações periódicas da API Creare
# Execute este arquivo regularmente (ex: via Task Scheduler)

$repo = 'C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard'
Set-Location $repo

Write-Host '' -ForegroundColor Cyan
Write-Host '' -ForegroundColor Gray

python creare_incremental_collector.py

Write-Host '' -ForegroundColor Green



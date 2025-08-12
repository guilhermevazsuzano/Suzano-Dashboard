
# Define o caminho da pasta e do arquivo
$folderPath = "/home/ubuntu/powershell_test"
$filePath = "$folderPath/my_script.py"

# 1. Cria a pasta se ela nÃ£o existir
Write-Host "Criando a pasta: $folderPath"
New-Item -Path $folderPath -ItemType Directory -Force | Out-Null

# 2. Cria o arquivo Python com conteÃºdo
Write-Host "Criando o arquivo: $filePath"
$pythonContent = "print('OlÃ¡ do script Python criado pelo PowerShell!')"
Set-Content -Path $filePath -Value $pythonContent

# 3. Executa o arquivo Python
Write-Host "Executando o script Python: $filePath"
python $filePath

Write-Host "Script PowerShell concluÃ­do."





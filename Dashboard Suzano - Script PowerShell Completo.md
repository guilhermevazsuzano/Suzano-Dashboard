# Dashboard Suzano - Script PowerShell Completo

## 📋 Visão Geral

Este script PowerShell automatiza completamente a configuração, execução e verificação do Dashboard Suzano, incluindo:

- Clonagem do repositório
- Instalação de dependências Python
- Extração de dados do SharePoint
- Coleta de dados da API Creare
- Implementação completa do backend com todos os endpoints
- Inicialização do servidor

## 🚀 Como Executar

### 1. Pré-requisitos

- **Windows 10/11** com PowerShell 5.1 ou superior
- **Python 3.8+** instalado e no PATH
- **Git** instalado e no PATH
- **Conexão com a internet**

### 2. Execução do Script

1. **Baixe o script:** Salve o conteúdo do arquivo `run_suzano_dashboard.ps1` em seu computador
2. **Abra o PowerShell como Administrador**
3. **Execute o script:**
   ```powershell
   .\run_suzano_dashboard.ps1
   ```

### 3. O que o Script Faz

#### Etapa 1: Configuração do Ambiente
- Cria o diretório: `C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard`
- Clona o repositório do GitHub
- Instala dependências Python: `fastapi`, `uvicorn`, `requests`, `office365-rest-python-client`

#### Etapa 2: Extração de Dados
- Remove arquivos JSON antigos
- Executa `extract_all_sharepoint.py` para coletar dados das 3 listas do SharePoint
- Cria a pasta `creare_data`

#### Etapa 3: Implementação do Coletor Creare
- Cria/atualiza `creare_collector.py` com autenticação e coleta de dados
- Executa o coletor para gerar arquivos JSON da Creare

#### Etapa 4: Backend Completo
- Cria/atualiza `dashboard_backend.py` com implementação completa
- Inclui todos os endpoints necessários:
  - `GET /` - Página principal
  - `GET /api/sharepoint-data` - Dados do SharePoint
  - `GET /api/creare-data` - Dados da Creare
  - `GET /api/metrics` - Métricas consolidadas
  - `POST /api/reload-data` - Recarregar dados

#### Etapa 5: Inicialização do Servidor
- Inicia o servidor Uvicorn na porta 8000
- Dashboard acessível em: `http://localhost:8000`

## 📊 Endpoints Implementados

### 1. Endpoint Principal
```
GET /
```
Retorna informações do sistema e lista de endpoints disponíveis.

### 2. Dados do SharePoint
```
GET /api/sharepoint-data
```
Retorna todos os dados extraídos das 3 listas do SharePoint com resumo por lista.

### 3. Dados da Creare
```
GET /api/creare-data
```
Retorna eventos coletados da API Creare com tipos de eventos e totais.

### 4. Métricas Consolidadas
```
GET /api/metrics
```
Retorna métricas calculadas idênticas ao dashboard HTML original:
- Total de desvios
- Alertas ativos
- Tempo médio de resolução
- Eficiência operacional
- Veículos monitorados
- Pontos de interesse

### 5. Recarregar Dados
```
POST /api/reload-data
```
Recarrega todos os dados e recalcula métricas em tempo real.

## 🔧 Configurações Importantes

### Credenciais da API Creare
No arquivo `creare_collector.py`, substitua as credenciais simuladas pelas reais:
```python
USERNAME = "your_username"  # Substitua pelo usuário real
PASSWORD = "your_password"  # Substitua pela senha real
```

### Estrutura de Dados
- **SharePoint:** Dados carregados de `sharepoint_complete_data_YYYYMMDD_HHMMSS.json`
- **Creare:** Dados carregados de `creare_data/*.json`
- **Métricas:** Calculadas em tempo real baseadas nos dados carregados

## 📈 Métricas Calculadas

O backend calcula automaticamente:

1. **Total de Desvios:** Soma de registros SharePoint + eventos Creare de violação
2. **Alertas Ativos:** Eventos Creare não resolvidos
3. **Tempo Médio de Resolução:** Baseado em eventos resolvidos
4. **Eficiência Operacional:** Percentual de eventos resolvidos
5. **Veículos Monitorados:** IDs únicos de veículos
6. **Pontos de Interesse:** Localizações únicas dos eventos

## 🌐 Acesso ao Dashboard

Após a execução bem-sucedida:

1. **Dashboard Principal:** `http://localhost:8000`
2. **API de Métricas:** `http://localhost:8000/api/metrics`
3. **Dados SharePoint:** `http://localhost:8000/api/sharepoint-data`
4. **Dados Creare:** `http://localhost:8000/api/creare-data`

## 🔍 Verificação de Funcionamento

Para verificar se tudo está funcionando:

1. **Acesse:** `http://localhost:8000`
2. **Verifique os logs** no PowerShell para mensagens de sucesso
3. **Teste os endpoints** individualmente
4. **Confirme** que as métricas são exibidas corretamente

## ⚠️ Solução de Problemas

### Erro: Python não encontrado
```
Solução: Instale Python 3.8+ e adicione ao PATH do sistema
```

### Erro: Git não encontrado
```
Solução: Instale Git e adicione ao PATH do sistema
```

### Erro: Falha na extração SharePoint
```
Solução: Verifique credenciais e conectividade com SharePoint
```

### Erro: Falha na coleta Creare
```
Solução: Atualize credenciais reais da API Creare
```

### Servidor não inicia
```
Solução: Verifique se a porta 8000 está livre
```

## 📝 Logs e Monitoramento

O script fornece logs detalhados com timestamps:
- `[INFO]` - Informações gerais
- `[SUCCESS]` - Operações bem-sucedidas
- `[ERROR]` - Erros que requerem atenção
- `[WARNING]` - Avisos não críticos

## 🔄 Atualizações e Manutenção

Para atualizar dados:
1. **Execute novamente** o script PowerShell, ou
2. **Use o endpoint** `POST /api/reload-data` para recarregar sem reiniciar

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs do PowerShell
2. Confirme pré-requisitos instalados
3. Teste conectividade com SharePoint e Creare
4. Verifique permissões de arquivo e rede


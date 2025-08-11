import requests
`nimport urllib3`nurllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)`nimport os
import pytz
import pandas as pd
import json
from datetime import datetime, timedelta
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURAÇÕES SUZANO - COLETA 2 MESES (ADAPTADO)
# ==============================================================================
CREARE_APP_CLIENT_ID = "56963"
CREARE_APP_CLIENT_SECRET = "1MSiBaH879w"  # Removido = extra
VALID_CUSTOMER_CHILD_ID = [39450]

# ==============================================================================
# CLASSE DE AUTENTICAÇÃO OTIMIZADA (SUA VERSÃO)
# ==============================================================================
class AuthClient:
    """Cliente otimizado para autenticação com a API Creare."""
    AUTH_URL = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._id_token = None
        self._token_expires_at = None

    def _is_token_expired(self):
        if not self._token_expires_at:
            return True
        return datetime.now() >= (self._token_expires_at - timedelta(seconds=60))

    def get_id_token(self):
        if self._id_token and not self._is_token_expired():
            return self._id_token

        print("🔐 Obtendo token de autenticação...")
        try:
            response = requests.post(
                self.AUTH_URL,
                auth=(self.client_id, self.client_secret),
                json={"grant_type": "client_credentials"},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            self._id_token = data.get("id_token")
            expires_in = int(data.get("expires_in", 3600))

            if self._id_token:
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                print("✅ Token obtido com sucesso!")
                return self._id_token
            else:
                raise Exception("Token não encontrado na resposta")

        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            return None

# ==============================================================================
# CLIENT API COMPLETO - SUA VERSÃO MELHORADA ADAPTADA PARA 2 MESES
# ==============================================================================
class SuzanoAPIClient:
    """Cliente completo para APIs Suzano - Versão otimizada para 2 meses."""
    FROTALOG_BASIC_URL = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
    FROTALOG_SPECIALIZED_URL = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"

    def __init__(self, auth_client_instance):
        self.auth_client = auth_client_instance
        self.session = requests.Session()
        self.session.verify = \False
        self.session.headers.update({'Accept': 'application/json'})

    def _get_headers(self):
        token = self.auth_client.get_id_token()
        if not token:
            raise Exception("Token não disponível")
        return {"Authorization": f"Bearer {token}"}

    def _make_request(self, method, url, params=None, json_data=None, timeout=120):
        headers = self._get_headers()
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=json_data, params=params, timeout=timeout)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout na requisição para {url}")
            return None
        except Exception as e:
            print(f"❌ Erro na requisição para {url}: {e}")
            return None

    def get_events_complete_2_months(self, customer_child_ids, start_date, end_date):
        """COLETA COMPLETA DE EVENTOS - 2 MESES - ADAPTADO DA SUA VERSÃO"""
        url = f"{self.FROTALOG_SPECIALIZED_URL}/events/by-page"
        all_events = []

        customer_ids_str = ",".join(map(str, customer_child_ids))
        print(f"🚀 COLETA COMPLETA: {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
        print("🔓 SEM FILTROS - Coletando TODOS os eventos possíveis (2 meses)")

        current_interval_start = start_date
        interval_count = 0

        while current_interval_start < end_date:
            interval_count += 1
            # Intervalos de 6 dias (sua otimização mantida)
            current_interval_end = current_interval_start + timedelta(days=6)

            if current_interval_end > end_date:
                current_interval_end = end_date

            from_timestamp_str = current_interval_start.isoformat(timespec='milliseconds')
            to_timestamp_str = current_interval_end.isoformat(timespec='milliseconds')

            print(f"\n📅 Intervalo {interval_count}: {current_interval_start.strftime('%d/%m/%Y')} - {current_interval_end.strftime('%d/%m/%Y')}")

            # Coleta paginada completa
            page = 1
            while True:
                params = {
                    "customerChildIds": customer_ids_str,
                    "fromTimestamp": from_timestamp_str,
                    "toTimestamp": to_timestamp_str,
                    "page": page,
                    "size": 1000,  # Máximo por página
                    "isDetailed": True,
                    "sort": "ASC"
                    # SEM FILTROS ADICIONAIS!
                }

                try:
                    response_data = self._make_request("GET", url, params=params)
                    if not response_data:
                        break

                    content = response_data.get("content", [])

                    if not content:
                        break

                    all_events.extend(content)
                    print(f"   📄 Página {page}: +{len(content)} eventos (Total: {len(all_events):,})")

                    if response_data.get("last") or len(content) < 1000:
                        break

                    page += 1

                except Exception as e:
                    print(f"   ❌ Erro na página {page}: {e}")
                    break

            current_interval_start = current_interval_end + timedelta(days=1)

        return all_events

    def get_all_additional_data(self):
        """Coleta dados adicionais completos"""
        additional_data = {}

        # Endpoints adicionais importantes
        endpoints = {
            'vehicles': f"{self.FROTALOG_BASIC_URL}/vehicles",
            'drivers': f"{self.FROTALOG_BASIC_URL}/drivers",
            'tracking_latest': f"{self.FROTALOG_BASIC_URL}/tracking/latest",
            'event_types': f"{self.FROTALOG_SPECIALIZED_URL}/events/types",
            'fences_poi': f"{self.FROTALOG_BASIC_URL}/fences/poi"
        }

        for name, url in endpoints.items():
            print(f"📥 Coletando: {name}")
            try:
                if name == 'vehicles':
                    params = {'customerId': VALID_CUSTOMER_CHILD_ID[0]}
                elif name == 'tracking_latest':
                    params = {'customerId': VALID_CUSTOMER_CHILD_ID, 'addTelemetry': True}
                elif name == 'fences_poi':
                    params = {'listCustomerChildId': VALID_CUSTOMER_CHILD_ID}
                else:
                    params = {}

                data = self._make_request("GET", url, params=params)
                additional_data[name] = data or []
                count = len(data) if isinstance(data, list) else "OK"
                print(f"   ✅ {count}")

            except Exception as e:
                print(f"   ❌ Erro: {e}")
                additional_data[name] = []

        return additional_data

# ==============================================================================
# EXECUÇÃO COMPLETA - 2 MESES ADAPTADO
# ==============================================================================
def executar_coleta_completa_suzano_2_meses():
    """Executa coleta completa de dados Suzano - 2 meses"""
    print("🏢 SUZANO - COLETA COMPLETA DE DADOS (2 MESES)")
    print("🚀 Versão otimizada para validação SharePoint")
    print("=" * 80)

    # Configurar período - ALTERADO PARA 2 MESES
    local_tz = pytz.timezone("America/Campo_Grande")
    end_date = local_tz.localize(datetime.now())
    start_date = end_date - timedelta(days=60)  # 2 meses (era 180)

    # Inicializar clientes
    auth_client = AuthClient(CREARE_APP_CLIENT_ID, CREARE_APP_CLIENT_SECRET)
    api_client = SuzanoAPIClient(auth_client)

    # Coleta completa de eventos
    all_events = api_client.get_events_complete_2_months(
        VALID_CUSTOMER_CHILD_ID, start_date, end_date
    )

    # Coleta dados adicionais
    print(f"\n🔧 COLETANDO DADOS ADICIONAIS")
    additional_data = api_client.get_all_additional_data()

    # Análise completa
    print(f"\n📊 ANÁLISE COMPLETA DOS DADOS")
    print("-" * 50)

    if all_events:
        print(f"✅ Total de eventos coletados: {len(all_events):,}")

        # Criar DataFrame otimizado
        df_eventos = pd.DataFrame(all_events)

        # Análise detalhada
        analyze_suzano_data_complete_2_months(df_eventos, additional_data)

        # Salvar dados completos
        save_complete_data_2_months(all_events, additional_data)

        return df_eventos, additional_data
    else:
        print("❌ Nenhum evento coletado")
        return None, None

def analyze_suzano_data_complete_2_months(df_eventos, additional_data):
    """Análise completa dos dados Suzano - 2 meses"""

    print(f"\n📈 RESUMO EXECUTIVO SUZANO (2 MESES):")
    print(f"   • Total de eventos: {len(df_eventos):,}")
    print(f"   • Período: 2 meses completos")
    print(f"   • Eventos por dia (média): {len(df_eventos) / 60:.1f}")  # 60 dias

    # Análise por colunas disponíveis
    print(f"\n📋 COLUNAS DISPONÍVEIS: {list(df_eventos.columns)}")

    # Veículos únicos
    if 'vehicleId' in df_eventos.columns:
        veiculos_unicos = df_eventos['vehicleId'].nunique()
        print(f"   • Veículos únicos: {veiculos_unicos}")

    # Motoristas únicos
    if 'driverId' in df_eventos.columns:
        motoristas_unicos = df_eventos['driverId'].nunique()
        print(f"   • Motoristas únicos: {motoristas_unicos}")

    # Análise de tipos de eventos
    for col in ['eventLabel', 'eventMessage', 'eventGroupName']:
        if col in df_eventos.columns:
            unique_count = df_eventos[col].nunique()
            print(f"   • {col} únicos: {unique_count}")

            # Top 10
            print(f"\n🏷️ TOP 10 {col.upper()}:")
            top_values = df_eventos[col].value_counts().head(10)
            for i, (value, count) in enumerate(top_values.items(), 1):
                perc = (count / len(df_eventos)) * 100
                print(f"   {i:2d}. {value}: {count:,} ({perc:.1f}%)")
            break

def save_complete_data_2_months(events, additional_data):
    """Salva dados completos - 2 meses"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Dados completos em JSON
    complete_data = {
        'events': events,
        'additional_data': additional_data,
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_events': len(events),
            'collection_method': 'COMPLETE_2_MONTHS_OPTIMIZED',
            'period_days': 60,
            'customer_id': VALID_CUSTOMER_CHILD_ID[0]
        }
    }

    filename = f'suzano_creare_data_2_months_{timestamp}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(complete_data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n💾 Dados Creare salvos: {filename}")

    # CSV dos eventos
    if events:
        df_events = pd.DataFrame(events)
        csv_filename = f'suzano_creare_events_2_months_{timestamp}.csv'
        df_events.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"💾 CSV Creare salvo: {csv_filename}")

    return filename

# ==============================================================================
# EXECUTAR SE CHAMADO DIRETAMENTE
# ==============================================================================
if __name__ == "__main__":
    print("🎯 EXECUTANDO COLETA CREARE 2 MESES")
    df_eventos, additional_data = executar_coleta_completa_suzano_2_meses()
    
    if df_eventos is not None:
        print(f"\n🎉 COLETA CREARE CONCLUÍDA COM SUCESSO!")
        print(f"📊 {len(df_eventos):,} eventos coletados dos últimos 2 meses")
        print(f"💡 Dados prontos para validação com SharePoint")
    else:
        print("❌ Falha na coleta Creare")


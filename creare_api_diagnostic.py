# -*- coding: utf-8 -*-
import requests
from datetime import datetime, timedelta

class AuthClient:
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
        print("AuthClient: Solicitando token de acesso...")
        try:
            response = requests.post(self.AUTH_URL, auth=(self.client_id, self.client_secret), 
                                   json={"grant_type": "client_credentials"}, verify=False)
            response.raise_for_status()
            data = response.json()
            self._id_token = data.get("id_token")
            expires_in = int(data.get("expires_in"))
            if self._id_token:
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                print("AuthClient: Token obtido com sucesso!")
                return self._id_token
            raise ValueError("Resposta da autenticação inválida.")
        except Exception as e:
            print(f"AuthClient: Falha na autenticação: {e}")
            raise

class APIDiagnosticTool:
    FROTALOG_BASIC_URL = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
    FROTALOG_SPECIALIZED_URL = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"

    def __init__(self, auth_client):
        self.auth_client = auth_client
        self.session = requests.Session()
        self.session.verify = False
        self.results = []

    def _make_request(self, api_type, method, endpoint, params=None):
        base_url = self.FROTALOG_BASIC_URL if api_type == 'basic' else self.FROTALOG_SPECIALIZED_URL
        url = f"{base_url}{endpoint}"
        token = self.auth_client.get_id_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        try:
            response = self.session.request(method, url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            return {"status_code": response.status_code, "data": response.json() if response.status_code != 204 else {}}
        except requests.exceptions.HTTPError as e:
            return {"status_code": e.response.status_code, "error": e.response.text}
        except requests.exceptions.RequestException as e:
            return {"status_code": None, "error": str(e)}

    def test_endpoint(self, api_name, api_type, method, endpoint, params=None):
        print(f"\n-- Testando: {api_name} - {method} {endpoint}")
        response = self._make_request(api_type, method, endpoint, params=params)
        
        status = ""
        if 'error' not in response:
            status = "✅ Sim"
        else:
            if response['status_code'] in [401, 403]:
                status = "❌ Não (Acesso Negado)"
            elif response['status_code'] == 404:
                status = "✅ Sim (Endpoint Válido)"
            else:
                status = f"❌ Não (Erro {response['status_code']})"

        print(f"   Resultado: {status}")
        self.results.append({"API": api_name, "Endpoint": f"{method} {endpoint}", "Tem Acesso?": status})

if __name__ == '__main__':
    CREARE_APP_CLIENT_ID = "56963"
    CREARE_APP_CLIENT_SECRET = "1MSiBaH879w="
    VALID_CUSTOMER_CHILD_ID = "39450"
    EXAMPLE_ID = "12345"
    EXAMPLE_CPF = "00000000000"

    print("--- INICIANDO DIAGNÓSTICO DE ACESSO ÀS APIs FROTALOG ---")

    auth_client = AuthClient(CREARE_APP_CLIENT_ID, CREARE_APP_CLIENT_SECRET)
    diagnostic_tool = APIDiagnosticTool(auth_client)

    # Parâmetros temporais
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    from_ts_str, to_ts_str = start_time.isoformat(), end_time.isoformat()
    from_date_str, to_date_str = start_time.strftime('%Y-%m-%d'), end_time.strftime('%Y-%m-%d')
    customer_params = {'customerChildIds': VALID_CUSTOMER_CHILD_ID}

    # Specialized endpoints
    api_name_specialized = "Frotalog Specialized"
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/customers')
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/customers/custom-columns-definitions', params={'customerId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/customers/profile', params={'customerChildId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/events/by-page', params={"customerChildIds": VALID_CUSTOMER_CHILD_ID, "fromTimestamp": from_ts_str, "toTimestamp": to_ts_str})
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/events/latest', params=customer_params)
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/events/types')
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/events/types/groups')
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', f'/events/types/{EXAMPLE_ID}')
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/events/vehicle-charging', params={"customerChildIds": VALID_CUSTOMER_CHILD_ID, "fromTimestamp": from_ts_str, "toTimestamp": to_ts_str})
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', f'/messages/assets/{EXAMPLE_ID}')
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/messages/default', params={'vehicleId': EXAMPLE_ID})
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/working-hours', params={"fromTimestamp": from_ts_str, "toTimestamp": to_ts_str})
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/working-hours/details', params={"fromTimestamp": from_ts_str, "toTimestamp": to_ts_str})
    diagnostic_tool.test_endpoint(api_name_specialized, 'specialized', 'GET', '/pontos-notaveis/by-updated', params={"startUpdatedAtTimestamp": from_ts_str, "endUpdatedAtTimestamp": to_ts_str})

    # Basic endpoints
    api_name_basic = "Frotalog Basic"
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/drivers')
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', f'/drivers/by-cpf/{EXAMPLE_CPF}')
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', f'/drivers/{EXAMPLE_ID}')
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/fences/embeddedfences', params={'listCustomerChildId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/fences/remotefences', params={'listCustomerChildId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/fences/poi', params={'listCustomerChildId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/fences/logisticfences', params={'listCustomerChildId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/fences/speechfences', params={'listCustomerChildId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/infractions', params={"customerChildIds": VALID_CUSTOMER_CHILD_ID, "fromTimestamp": from_ts_str, "toTimestamp": to_ts_str})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/infractions/types')
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/journeys', params={"customerChildIds": VALID_CUSTOMER_CHILD_ID, "fromTimestamp": from_ts_str, "toTimestamp": to_ts_str})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/tracking', params={'vehicleId': EXAMPLE_ID, "fromTimestamp": from_ts_str, "toTimestamp": to_ts_str})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/tracking/latest', params={'customerId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/vehicles', params={'customerId': VALID_CUSTOMER_CHILD_ID})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/vehicles/config', params={'vehicleId': EXAMPLE_ID})
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', '/vehicles/types')
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', f'/vehicles/{EXAMPLE_ID}')
    diagnostic_tool.test_endpoint(api_name_basic, 'basic', 'GET', f'/users/{EXAMPLE_ID}/hierarchy')

    print("\n" + "="*80)
    print("             TABELA-RESUMO DE ACESSO ÀS APIs FROTALOG")
    print("="*80)

    for i, result in enumerate(diagnostic_tool.results):
        print(f"{i}\t{result['API']}\t{result['Endpoint']}\t{result['Tem Acesso?']}")
    
    print(f"\n✅ Diagnóstico concluído! {len(diagnostic_tool.results)} endpoints testados.")

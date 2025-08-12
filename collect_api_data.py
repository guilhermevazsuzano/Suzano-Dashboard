import os, json, requests, base64, urllib3
from datetime import datetime, timedelta
urllib3.disable_warnings()                     # <── ignora SSL

CID   = "56963"
CSEC  = "1MSiBaH879w="
CHILD = "39450"
VEH   = "12345"

TOKEN = "https://openid-provider.crearecloud.com.br/auth/v1/token?lang=pt-BR"
URL_S = "https://api.crearecloud.com.br/frotalog/specialized-services/v3"
URL_B = "https://api.crearecloud.com.br/frotalog/basic-services/v3"
OUT   = "data_api"

os.makedirs(OUT, exist_ok=True)

def get_token():
    basic = base64.b64encode(f"{CID}:{CSEC}".encode()).decode()
    r = requests.post(
        TOKEN, headers={"Authorization": f"Basic {basic}"},
        json={"grant_type":"client_credentials"}, timeout=30, verify=False  # <── verify=False
    )
    r.raise_for_status()
    return r.json()["id_token"]

now  = datetime.utcnow(); d30 = (now - timedelta(days=30)).isoformat()+"Z"
d07  = (now - timedelta(days=7 )).isoformat()+"Z"; nowZ = now.isoformat()+"Z"

EP_S = {
 "/customers": {},
 "/customers/custom-columns-definitions": {"customerId": CHILD},
 "/customers/profile": {"customerChildId": CHILD},
 "/events/by-page":{
   "customerChildIds":CHILD,"fromTimestamp":d30,"toTimestamp":nowZ,
   "page":0,"pageSize":1000,"isDetailed":True},
 "/events/latest": {"customerChildIds": CHILD},
 "/events/types": {}, "/events/types/groups": {},
 "/events/vehicle-charging":{"customerChildIds":CHILD,"fromTimestamp":d07,"toTimestamp":nowZ},
 "/working-hours":{"fromTimestamp":d07,"toTimestamp":nowZ},
 "/working-hours/details":{"fromTimestamp":d07,"toTimestamp":nowZ},
 "/pontos-notaveis/by-updated":{"startUpdatedAtTimestamp":d07,"endUpdatedAtTimestamp":nowZ}
}

EP_B = {
 "/drivers": {},
 "/fences/embeddedfences":{"listCustomerChildId":CHILD},
 "/fences/poi":{"listCustomerChildId":CHILD},
 "/infractions":{"customerChildIds":CHILD,"fromTimestamp":d30,"toTimestamp":nowZ},
 "/infractions/types": {},
 "/journeys":{"customerChildIds":CHILD,"fromTimestamp":d30,"toTimestamp":nowZ},
 "/tracking/latest":{"customerId":CHILD},
 "/vehicles":{"customerId":CHILD},
 "/vehicles/config":{"vehicleId":VEH},
 "/vehicles/types": {}
}

def fetch(base, ep, pr, tk):
    r = requests.get(base+ep, headers={"Authorization":f"Bearer {tk}"}, params=pr, timeout=60, verify=False)
    r.raise_for_status()
    fname = ep.strip("/").replace("/","_")+".json"
    json.dump(r.json(), open(os.path.join(OUT,fname),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✔ {ep}")

def main():
    tk = get_token(); print("Token OK\n— Specialized —")
    [fetch(URL_S, e, p, tk) for e,p in EP_S.items()]
    print("— Basic —")
    [fetch(URL_B, e, p, tk) for e,p in EP_B.items()]
    print(f"\n✅ Coleta concluída → {OUT}")

if __name__=="__main__": main()

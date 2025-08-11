import json, requests, base64, time
from datetime import datetime, timedelta

CFG = {
    "CLIENT_ID":"56963","CLIENT_SECRET":"1MSiBaH879w",
    "AUTH_URL":"https://openid-provider.crearecloud.com.br/auth/v1/token",
    "API_URL":"https://api.crearecloud.com.br/frotalog/specialized-services/v3"
}

class CreareAPIValidator:
    def __init__(self): self.token=None;self.headers=None;self.sp=None
    def get_auth_token(self):
        cred=f"{CFG['CLIENT_ID']}:{CFG['CLIENT_SECRET']}"
        h={"Authorization":f"Basic {base64.b64encode(cred.encode()).decode()}",
           "Content-Type":"application/json"}
        r=requests.post(CFG['AUTH_URL'],headers=h,json={"grant_type":"client_credentials"},timeout=30)
        if r.status_code==200:
            t=r.json().get("id_token");self.token=t
            self.headers={"Authorization":f"Bearer {t}"}
            return True
        return False
    def load_sharepoint_data(self,fn="sharepoint_complete_data.json"):
        try:
            self.sp=json.load(open(fn,'r',encoding='utf-8'))
            return True
        except: return False
    def fetch_creare_events(self,days=7):
        now=datetime.now();start=now-timedelta(days=days)
        params={"fromTimestamp":start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z",
                "toTimestamp":now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z",
                "customerChildIds":[39450],"pageSize":1000,"page":1,
                "sort":"ASC","isDetailed":True}
        ev=[];page=1
        while True:
            params["page"]=page
            r=requests.get(f"{CFG['API_URL']}/events/by-page",headers=self.headers,params=params,timeout=60)
            if r.status_code!=200: break
            data=r.json().get("content",[])
            if not data: break
            ev+=data; page+=1; time.sleep(0.3)
            if page>100: break
        return ev
    def validate_data_consistency(self,ev):
        report={"timestamp":datetime.now().isoformat(),
                "sharepoint_summary":{},
                "creare_summary":{},
                "validation_results":{},
                "discrepancies":[], "recommendations":[]}
        sp_lists=self.sp.get("lists",{})
        report["sharepoint_summary"]={"total_records":sum(len(v) for v in sp_lists.values())}
        report["creare_summary"]={"total_events":len(ev)}
        # exemplo: validações mínimas
        if not ev: report["discrepancies"].append({"type":"NO_CREARE","description":"Nenhum evento Creare"})
        if not sp_lists: report["discrepancies"].append({"type":"NO_SP","description":"Nenhum dado SP"})
        report["recommendations"].append({"priority":"MEDIUM","title":"Agendar validação diária","action":"Agendar tarefa no Windows"})
        return report
    def save_validation_report(self,rep):
        fn=f"validation_report_{datetime.now():yyyyMMdd_HHmmss}.json"
        json.dump(rep, open(fn,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
        return fn

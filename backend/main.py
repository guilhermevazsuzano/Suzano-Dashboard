import os, json
from fastapi import FastAPI, HTTPException

app=FastAPI()
DIR='creare_data'

@app.get('/api/creare-data')
def get_data():
    files=sorted([f for f in os.listdir(DIR) if f.startswith('events_') and f.endswith('.json')], reverse=True)
    if not files:
        raise HTTPException(404,'Nenhum dado Creare')
    path=os.path.join(DIR,files[0])
    with open(path,encoding='utf-8') as f:
        d=json.load(f)
    return {'timestamp':files,'total':len(d),'events':d}

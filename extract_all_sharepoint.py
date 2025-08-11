import json
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from datetime import datetime
import time

# Credenciais
SITE_URL = "https://suzano.sharepoint.com/sites/Controleoperacional"
USERNAME = "guilhermevaz@suzano.com.br"
PASSWORD = "STRT1918a*"

# IDs das 3 listas reais
LIST_IDS = {
    "Lista1": "264e0df9-4cb4-42fa-93bc-083c35141849",
    "Lista2": "3d5e0830-6aff-43b7-bd37-21a49e47fbd0",
    "Lista3": "833cb2f9-5aab-4f1b-82d0-48aadd1cb968"
}

def fetch_all_list_items(list_id, list_name):
    """Extrai TODOS os itens de uma lista SharePoint usando paginação"""
    print(f"🔍 Extraindo TODOS os registros de {list_name}...")
    
    # Autenticar
    ctx_auth = AuthenticationContext(SITE_URL)
    if not ctx_auth.acquire_token_for_user(USERNAME, PASSWORD):
        raise Exception("Falha na autenticação SharePoint!")
    
    ctx = ClientContext(SITE_URL, ctx_auth)
    sp_list = ctx.web.lists.get_by_id(list_id)
    
    all_items = []
    skip = 0
    page_size = 500  # Tamanho da página
    page_count = 0
    
    while True:
        page_count += 1
        print(f"  → Página {page_count} (skip: {skip})...")
        
        try:
            # Obter itens com paginação
            items = sp_list.items.skip(skip).top(page_size)
            ctx.load(items)
            ctx.execute_query()
            
            # Converter para lista Python
            page_items = []
            for item in items:
                item_props = {}
                for key, value in item.properties.items():
                    if key != "__metadata" and value is not None:
                        item_props[key] = str(value)
                page_items.append(item_props)
            
            if not page_items:  # Sem mais itens
                break
                
            all_items.extend(page_items)
            print(f"    ✅ +{len(page_items)} itens (Total: {len(all_items)})")
            
            # Próxima página
            skip += page_size
            
            # Proteção contra loop infinito
            if page_count > 100:
                print(f"    ⚠️ Limite de 100 páginas atingido")
                break
                
            # Pequena pausa para não sobrecarregar
            time.sleep(0.5)
            
        except Exception as e:
            print(f"    ❌ Erro na página {page_count}: {e}")
            if "does not exist" in str(e) or skip == 0:
                # Se é erro na primeira página, a lista pode não existir
                break
            else:
                # Se é erro em página posterior, pode ser fim dos dados
                print(f"    ℹ️ Possível fim dos dados na página {page_count}")
                break
    
    print(f"✅ TOTAL EXTRAÍDO de {list_name}: {len(all_items)} registros")
    return all_items

def main():
    print("🚀 EXTRAINDO TODOS OS DADOS DAS LISTAS SHAREPOINT SUZANO")
    print("=" * 70)
    
    all_data = {
        "timestamp": datetime.now().isoformat(),
        "site": SITE_URL,
        "extraction_type": "COMPLETE",
        "lists": {}
    }
    
    total_records = 0
    
    for name, list_id in LIST_IDS.items():
        print(f"\n📋 PROCESSANDO {name.upper()} ({list_id[:8]}...)...")
        
        try:
            data = fetch_all_list_items(list_id, name)
            all_data["lists"][name] = data
            total_records += len(data)
            
            # Mostrar amostra dos campos
            if data:
                sample_fields = list(data[0].keys())[:8]
                print(f"  📊 Campos exemplo: {', '.join(sample_fields)}")
                
        except Exception as e:
            print(f"❌ Erro total em {name}: {e}")
            all_data["lists"][name] = []

    # Salvar dados completos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sharepoint_complete_data_{timestamp}.json"
    
    print(f"\n💾 Salvando dados completos...")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n🎉 EXTRAÇÃO COMPLETA FINALIZADA!")
    print(f"📊 Total de registros extraídos: {total_records:,}")
    print(f"📁 Arquivo salvo: {filename}")
    print(f"📍 Localização: {os.getcwd()}\\{filename}")
    
    # Resumo por lista
    print(f"\n📋 RESUMO POR LISTA:")
    for list_name, items in all_data["lists"].items():
        print(f"  • {list_name}: {len(items):,} registros")
    
    return filename

if __name__ == "__main__":
    import os
    try:
        resultado = main()
        print(f"\n🎯 SUCESSO! Arquivo completo: {resultado}")
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")

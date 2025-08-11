import json
import os
import glob
from datetime import datetime

class SharePointDataLoader:
    def __init__(self):
        self.possible_files = [
            "sharepoint_complete_data_20250811_163527.json",
            "sharepoint_data_20250811_161305.json",
            "sharepoint_complete_data*.json",
            "sharepoint_data*.json"
        ]
    
    def find_sharepoint_file(self):
        print("🔍 Procurando arquivos SharePoint...")
        
        # Procurar arquivos específicos primeiro
        for filename in self.possible_files[:2]:
            if os.path.exists(filename):
                print(f"✅ Encontrado: {filename}")
                return filename
        
        # Procurar com wildcards
        for pattern in self.possible_files[2:]:
            files = glob.glob(pattern)
            if files:
                latest_file = max(files, key=os.path.getmtime)
                print(f"✅ Encontrado (mais recente): {latest_file}")
                return latest_file
        
        print("❌ Nenhum arquivo SharePoint encontrado")
        return None
    
    def load_sharepoint_data(self):
        """Carrega dados SharePoint com progresso"""
        print("📊 INICIANDO COLETA SHAREPOINT...")
        
        filename = self.find_sharepoint_file()
        if not filename:
            raise FileNotFoundError("Arquivo SharePoint não encontrado")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("✅ SharePoint carregado com sucesso!")
                return data
        except Exception as e:
            raise Exception(f"Erro ao carregar SharePoint: {e}")

# Instância global
sharepoint_loader = SharePointDataLoader()

if __name__ == "__main__":
    data = sharepoint_loader.load_sharepoint_data()
    total = sum(len(items) for items in data.get("lists", {}).values())
    print(f"Total de registros SharePoint: {total:,}")

# -*- coding: utf-8 -*-
"""
Sistema de coleta incremental para SharePoint e Creare
Verifica dados existentes e atualiza apenas o que é necessário
"""
import json
import os
import glob
import subprocess
from datetime import datetime, timedelta

class IncrementalDataManager:
    def __init__(self):
        self.sharepoint_file = None
        self.creare_data_dir = "creare_data"
        
    def check_sharepoint_data(self):
        """Verifica se dados SharePoint existem e sua idade"""
        files = glob.glob("sharepoint_complete_data_*.json")
        if not files:
            return False, None, 0
        
        latest_file = max(files, key=os.path.getmtime)
        self.sharepoint_file = latest_file
        
        # Verificar idade do arquivo
        file_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
        age_hours = (datetime.now() - file_time).total_seconds() / 3600
        
        # Contar registros
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total = sum(len(items) for items in data.get("lists", {}).values())
                return True, age_hours, total
        except:
            return False, None, 0
    
    def should_update_sharepoint(self, age_hours, total_records):
        """Decide se deve atualizar SharePoint baseado na idade e tamanho"""
        if age_hours is None:
            return True, "Primeira coleta"
        elif age_hours > 24:  # Mais de 24 horas
            return True, f"Dados antigos ({age_hours:.1f}h)"
        elif total_records < 100000:  # Dados incompletos
            return True, f"Dados incompletos ({total_records:,} registros)"
        else:
            return False, f"Dados atuais ({age_hours:.1f}h, {total_records:,} registros)"
    
    def check_creare_data(self):
        """Verifica dados Creare existentes"""
        if not os.path.exists(self.creare_data_dir):
            return False, None, 0
        
        event_files = glob.glob(f"{self.creare_data_dir}/events_complete_*.json")
        if not event_files:
            return False, None, 0
        
        latest_file = max(event_files, key=os.path.getmtime)
        file_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
        age_hours = (datetime.now() - file_time).total_seconds() / 3600
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                events = json.load(f)
                return True, age_hours, len(events)
        except:
            return False, None, 0
    
    def should_update_creare(self, age_hours, total_events):
        """Decide se deve atualizar Creare"""
        if age_hours is None:
            return True, "Primeira coleta"
        elif age_hours > 6:  # Mais de 6 horas (dados mais dinâmicos)
            return True, f"Dados antigos ({age_hours:.1f}h)"
        else:
            return False, f"Dados atuais ({age_hours:.1f}h, {total_events:,} eventos)"

def smart_data_sync():
    """Sincronização inteligente de dados"""
    print("🤖 SISTEMA DE COLETA INCREMENTAL")
    print("=" * 40)
    
    manager = IncrementalDataManager()
    
    # SharePoint
    exists, age_hours, total = manager.check_sharepoint_data()
    should_update, reason = manager.should_update_sharepoint(age_hours, total)
    
    print(f"📊 SHAREPOINT STATUS: {reason}")
    
    if should_update:
        print("🔄 Executando coleta SharePoint...")
        if os.path.exists("extract_all_sharepoint.py"):
            subprocess.run(["python", "extract_all_sharepoint.py"])
            # Verificar novamente após coleta
            exists, age_hours, total = manager.check_sharepoint_data()
            print(f"✅ SharePoint atualizado: {total:,} registros")
        else:
            print("❌ extract_all_sharepoint.py não encontrado")
    else:
        print("⏭️  SharePoint: Usando dados existentes")
    
    print()
    
    # Creare
    exists_c, age_hours_c, total_c = manager.check_creare_data()
    should_update_c, reason_c = manager.should_update_creare(age_hours_c, total_c)
    
    print(f"📡 CREARE STATUS: {reason_c}")
    
    if should_update_c:
        print("🔄 Executando coleta Creare...")
        if os.path.exists("creare_collector_updated.py"):
            subprocess.run(["python", "creare_collector_updated.py"])
            # Verificar novamente após coleta
            exists_c, age_hours_c, total_c = manager.check_creare_data()
            print(f"✅ Creare atualizado: {total_c:,} eventos")
        else:
            print("❌ creare_collector_updated.py não encontrado")
    else:
        print("⏭️  Creare: Usando dados existentes")
    
    # Resumo final
    print(f"\n📋 RESUMO DA SINCRONIZAÇÃO:")
    print(f"📊 SharePoint: {total:,} registros")
    print(f"📡 Creare: {total_c:,} eventos")
    print(f"🕒 Sincronizado em: {datetime.now().strftime('%H:%M:%S')}")
    
    return manager.sharepoint_file is not None, exists_c

if __name__ == "__main__":
    smart_data_sync()

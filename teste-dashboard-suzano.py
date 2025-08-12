# -*- coding: utf-8 -*-
import os
import sys
import requests
import json
import time
from datetime import datetime

print("=" * 70)
print("DASHBOARD SUZANO - DIAGNÓSTICO COMPLETO")
print("=" * 70)
print(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Diretório atual: {os.getcwd()}")
print("=" * 70)

# Configurações
API_BASE = "http://localhost:5000/api"
test_results = {}

def test_file_structure():
    """Teste 1: Verificar estrutura de arquivos"""
    print("\n1/5 🔍 TESTANDO ESTRUTURA DE ARQUIVOS...")
    
    # Arquivos essenciais esperados no projeto Suzano
    required_files = [
        "backend/serverbase.py",
        "backend/server.py", 
        "frontend/index.html",
        "backend/crearerealcollector.py",
        "src/staging-area/events30d.json",
        "src/run-etl.ps1",
        "requirements.txt"
    ]
    
    files_found = 0
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"✅ {filepath}")
            files_found += 1
        else:
            print(f"❌ {filepath} - NÃO ENCONTRADO")
    
    # Verificar estrutura de pastas
    expected_folders = ["backend", "frontend", "src", "scripts", "tests"]
    folders_found = 0
    
    print("\n📁 Verificando estrutura de pastas:")
    for folder in expected_folders:
        if os.path.exists(folder):
            print(f"✅ {folder}/")
            folders_found += 1
        else:
            print(f"❌ {folder}/ - NÃO ENCONTRADA")
    
    success = files_found >= len(required_files) * 0.6  # 60% dos arquivos ok
    test_results["estrutura_arquivos"] = {
        "success": success,
        "arquivos_encontrados": files_found,
        "total_arquivos": len(required_files),
        "pastas_encontradas": folders_found,
        "total_pastas": len(expected_folders)
    }
    
    if success:
        print(f"✅ ESTRUTURA BOA: {files_found}/{len(required_files)} arquivos")
    else:
        print(f"⚠️ ESTRUTURA PARCIAL: {files_found}/{len(required_files)} arquivos")
    
    return success

def test_python_environment():
    """Teste 2: Verificar ambiente Python"""
    print("\n2/5 🐍 TESTANDO AMBIENTE PYTHON...")
    
    print(f"✅ Versão Python: {sys.version}")
    print(f"✅ Executável: {sys.executable}")
    
    # Verificar dependências críticas
    dependencies = {
        "requests": "Requisições HTTP",
        "flask": "Framework web",
        "pandas": "Análise de dados", 
        "json": "Manipulação JSON (built-in)"
    }
    
    deps_ok = 0
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {dep} - {desc}")
            deps_ok += 1
        except ImportError:
            print(f"❌ {dep} - NÃO INSTALADO ({desc})")
    
    # Verificar se está em venv
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Executando em ambiente virtual")
    else:
        print("⚠️ Não está em ambiente virtual")
    
    success = deps_ok >= len(dependencies) * 0.75
    test_results["ambiente_python"] = {
        "success": success,
        "dependencias_ok": deps_ok,
        "total_dependencias": len(dependencies),
        "em_venv": in_venv,
        "versao_python": sys.version.split()[0]
    }
    
    return success

def test_flask_server():
    """Teste 3: Verificar servidor Flask/FastAPI"""
    print("\n3/5 🌐 TESTANDO SERVIDOR WEB...")
    
    endpoints_to_test = [
        ("http://localhost:5000/api/health", "Flask Health"),
        ("http://localhost:8000/health", "FastAPI Health"),
        ("http://localhost:5000/api/alertas", "Flask Alertas"),
        ("http://localhost:8000/events", "FastAPI Events")
    ]
    
    server_working = False
    working_endpoints = 0
    
    for url, name in endpoints_to_test:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ {name} - Respondendo (HTTP {response.status_code})")
                try:
                    data = response.json()
                    print(f"   📊 Dados: {len(str(data))} caracteres")
                except:
                    print(f"   📊 Resposta não-JSON")
                server_working = True
                working_endpoints += 1
            else:
                print(f"⚠️ {name} - HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {name} - Servidor offline")
        except requests.exceptions.Timeout:
            print(f"❌ {name} - Timeout")
        except Exception as e:
            print(f"❌ {name} - Erro: {str(e)[:50]}")
    
    if not server_working:
        print("\n🔧 INSTRUÇÕES PARA INICIAR SERVIDOR:")
        print("   Flask: python backend/serverbase.py")
        print("   FastAPI: cd src && python main.py")
        print("   Ou: uvicorn main:app --host 0.0.0.0 --port 8000")
    
    test_results["servidor_web"] = {
        "success": server_working,
        "endpoints_funcionando": working_endpoints,
        "total_testados": len(endpoints_to_test)
    }
    
    return server_working

def test_data_files():
    """Teste 4: Verificar arquivos de dados"""
    print("\n4/5 📊 TESTANDO ARQUIVOS DE DADOS...")
    
    data_files = {
        "src/staging-area/events30d.json": "Eventos ETL",
        "cache/events-6m.json": "Cache 6 meses", 
        "data/consolidated.json": "Dados consolidados",
        "staging/events.json": "Staging área",
        ".env": "Configurações"
    }
    
    files_with_data = 0
    total_size = 0
    
    for filepath, desc in data_files.items():
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            total_size += size
            if size > 100:  # Arquivo com conteúdo
                print(f"✅ {desc} - {size:,} bytes ({filepath})")
                files_with_data += 1
            else:
                print(f"⚠️ {desc} - Arquivo vazio ({filepath})")
        else:
            print(f"❌ {desc} - Não encontrado ({filepath})")
    
    print(f"\n📈 Total de dados: {total_size:,} bytes")
    
    success = files_with_data > 0
    test_results["arquivos_dados"] = {
        "success": success,
        "arquivos_com_dados": files_with_data,
        "tamanho_total_bytes": total_size,
        "tamanho_total_mb": round(total_size / 1024 / 1024, 2)
    }
    
    return success

def test_system_health():
    """Teste 5: Verificar saúde geral do sistema"""
    print("\n5/5 🔋 TESTANDO SAÚDE DO SISTEMA...")
    
    # Verificar processos Python rodando
    try:
        import psutil
        python_processes = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'python' in proc.info['name'].lower():
                python_processes += 1
        print(f"✅ Processos Python ativos: {python_processes}")
        psutil_available = True
    except ImportError:
        print("⚠️ psutil não disponível - não é possível verificar processos")
        python_processes = 0
        psutil_available = False
    
    # Verificar espaço em disco
    try:
        import shutil
        total, used, free = shutil.disk_usage('.')
        free_gb = free // (1024**3)
        print(f"✅ Espaço livre: {free_gb} GB")
        space_ok = free_gb > 1
    except:
        print("⚠️ Não foi possível verificar espaço em disco")
        space_ok = True
    
    # Verificar conectividade internet
    try:
        response = requests.get("https://httpbin.org/status/200", timeout=5)
        internet_ok = response.status_code == 200
        print("✅ Conectividade com internet: OK")
    except:
        print("❌ Conectividade com internet: Falhou")
        internet_ok = False
    
    success = space_ok and (python_processes > 0 or not psutil_available)
    test_results["saude_sistema"] = {
        "success": success,
        "processos_python": python_processes,
        "psutil_disponivel": psutil_available,
        "espaco_ok": space_ok,
        "internet_ok": internet_ok
    }
    
    return success

def generate_final_report():
    """Gerar relatório final detalhado"""
    print("\n" + "="*70)
    print("📋 RELATÓRIO FINAL - DASHBOARD SUZANO")
    print("="*70)
    
    tests = [
        ("Estrutura de Arquivos", test_results.get("estrutura_arquivos", {}).get("success", False)),
        ("Ambiente Python", test_results.get("ambiente_python", {}).get("success", False)),
        ("Servidor Web", test_results.get("servidor_web", {}).get("success", False)),
        ("Arquivos de Dados", test_results.get("arquivos_dados", {}).get("success", False)),
        ("Saúde do Sistema", test_results.get("saude_sistema", {}).get("success", False))
    ]
    
    passed = sum(1 for _, result in tests if result)
    
    print(f"📊 RESULTADOS:")
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:20} {status}")
    
    print(f"\n🎯 SCORE: {passed}/{len(tests)} testes passaram")
    
    # Análise detalhada
    if passed == len(tests):
        status = "🎉 EXCELENTE"
        message = "Sistema Dashboard Suzano está perfeito!"
        color = "🟢"
    elif passed >= len(tests) * 0.8:
        status = "👍 MUITO BOM" 
        message = "Sistema está operacional, pequenos ajustes necessários."
        color = "🟡"
    elif passed >= len(tests) * 0.6:
        status = "⚠️ FUNCIONAL"
        message = "Sistema parcialmente operacional, requer correções."
        color = "🟡"
    else:
        status = "❌ CRÍTICO"
        message = "Sistema requer correções substanciais."
        color = "🔴"
    
    print(f"\n{color} STATUS: {status}")
    print(f"📝 {message}")
    
    # Recomendações específicas
    print(f"\n🔧 RECOMENDAÇÕES:")
    
    if not test_results.get("estrutura_arquivos", {}).get("success", False):
        print("   • Verificar se está no diretório correto do projeto")
        print("   • Executar scripts de setup se necessário")
    
    if not test_results.get("ambiente_python", {}).get("success", False):
        print("   • Instalar dependências: pip install -r requirements.txt")
        print("   • Ativar ambiente virtual se disponível")
    
    if not test_results.get("servidor_web", {}).get("success", False):
        print("   • Iniciar servidor: python backend/serverbase.py")
        print("   • Ou: cd src && uvicorn main:app --port 8000")
    
    if not test_results.get("arquivos_dados", {}).get("success", False):
        print("   • Executar ETL: src/run-etl.ps1")
        print("   • Ou: python backend/crearerealcollector.py")
    
    # Salvar relatório
    report = {
        "timestamp": datetime.now().isoformat(),
        "diretorio": os.getcwd(),
        "status": status,
        "testes_passaram": passed,
        "total_testes": len(tests),
        "taxa_sucesso": round((passed / len(tests)) * 100, 1),
        "detalhes": test_results,
        "recomendacoes": "Ver output do console"
    }
    
    report_file = "relatorio-dashboard-suzano.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório salvo: {report_file}")
    print("="*70)

def main():
    """Executar diagnóstico completo"""
    try:
        print("🚀 Iniciando diagnóstico do Dashboard Suzano...")
        
        # Executar todos os testes
        test_file_structure()
        test_python_environment() 
        test_flask_server()
        test_data_files()
        test_system_health()
        
        # Gerar relatório final
        generate_final_report()
        
    except KeyboardInterrupt:
        print("\n⏹️ Diagnóstico interrompido pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Diagnóstico concluído!")
    input("\nPressione ENTER para fechar...")

if __name__ == "__main__":
    main()

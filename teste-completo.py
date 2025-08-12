# -*- coding: utf-8 -*-
import os
import sys
import requests
import json
import time
from datetime import datetime

print("=" * 70)
print("DASHBOARD SUZANO - TESTE COMPLETO AUTOMATIZADO")
print("=" * 70)
print(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Configurações
API_BASE = "http://localhost:5000/api"
test_results = {}

def test_file_structure():
    """Teste 1: Verificar estrutura de arquivos"""
    print("1/5 TESTANDO ESTRUTURA DE ARQUIVOS...")
    
    required_files = [
        "backend/serverbase.py",
        "frontend/index.html", 
        "backend/crearerealcollector.py"
    ]
    
    files_found = 0
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"✓ {filepath}")
            files_found += 1
        else:
            print(f"✗ {filepath} - NÃO ENCONTRADO")
    
    success = files_found == len(required_files)
    test_results["estrutura_arquivos"] = {
        "success": success, 
        "found": files_found, 
        "total": len(required_files)
    }
    
    if success:
        print(f"✓ ESTRUTURA COMPLETA: {files_found}/{len(required_files)} arquivos")
    else:
        print(f"⚠ ESTRUTURA PARCIAL: {files_found}/{len(required_files)} arquivos")
    
    return success

def test_python_dependencies():
    """Teste 2: Verificar dependências Python"""
    print("\n2/5 TESTANDO DEPENDÊNCIAS PYTHON...")
    
    dependencies = ["flask", "requests", "pandas", "numpy"]
    deps_ok = 0
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep}")
            deps_ok += 1
        except ImportError:
            print(f"✗ {dep} - NÃO INSTALADO")
    
    success = deps_ok >= len(dependencies) * 0.8  # 80% das deps ok
    test_results["dependencias"] = {
        "success": success,
        "installed": deps_ok,
        "total": len(dependencies)
    }
    
    if success:
        print(f"✓ DEPENDÊNCIAS OK: {deps_ok}/{len(dependencies)}")
    else:
        print(f"⚠ DEPENDÊNCIAS INCOMPLETAS: {deps_ok}/{len(dependencies)}")
    
    return success

def test_flask_server():
    """Teste 3: Verificar servidor Flask"""
    print("\n3/5 TESTANDO SERVIDOR FLASK...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ Servidor respondendo (HTTP {response.status_code})")
            print(f"✓ Status: {health_data.get('status', 'unknown')}")
            
            test_results["flask_server"] = {
                "success": True,
                "status": health_data.get('status')
            }
            return True
        else:
            print(f"⚠ Servidor retornou HTTP {response.status_code}")
            test_results["flask_server"] = {
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
            return False
    
    except requests.exceptions.ConnectionError:
        print("✗ Servidor Flask não está rodando")
        print("  → Inicie com: python backend/serverbase.py")
        test_results["flask_server"] = {
            "success": False,
            "error": "Connection refused"
        }
        return False
    
    except Exception as e:
        print(f"✗ Erro ao testar Flask: {e}")
        test_results["flask_server"] = {
            "success": False,
            "error": str(e)
        }
        return False

def test_api_endpoints():
    """Teste 4: Testar endpoints da API"""
    print("\n4/5 TESTANDO ENDPOINTS DA API...")
    
    endpoints = [
        ("api/health", "GET"),
        ("api/alertas", "GET"),
        ("api/etl-status", "GET")
    ]
    
    endpoints_ok = 0
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"http://localhost:5000/{endpoint}", timeout=5)
            else:
                response = requests.post(f"http://localhost:5000/{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✓ {method} {endpoint}")
                endpoints_ok += 1
            else:
                print(f"⚠ {method} {endpoint} - HTTP {response.status_code}")
                
        except Exception as e:
            print(f"✗ {method} {endpoint} - {str(e)[:50]}...")
    
    success = endpoints_ok >= 2  # Pelo menos 2 endpoints funcionando
    test_results["api_endpoints"] = {
        "success": success,
        "working": endpoints_ok,
        "total": len(endpoints)
    }
    
    return success

def generate_report():
    """Gerar relatório final"""
    print("=" * 70)
    print("RELATÓRIO FINAL DOS TESTES")
    print("=" * 70)
    
    tests = [
        ("Estrutura de Arquivos", test_results.get("estrutura_arquivos", {}).get("success", False)),
        ("Dependências Python", test_results.get("dependencias", {}).get("success", False)),
        ("Servidor Flask", test_results.get("flask_server", {}).get("success", False)),
        ("Endpoints API", test_results.get("api_endpoints", {}).get("success", False))
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print("=" * 70)
    
    if passed == len(tests):
        print(f"🎉 PERFEITO! TODOS OS {len(tests)} TESTES PASSARAM!")
        print("Sistema Dashboard Suzano está 100% funcional!")
        status = "EXCELENTE"
    elif passed >= len(tests) * 0.8:
        print(f"👍 MUITO BOM! {passed}/{len(tests)} testes passaram!")
        print("Sistema está operacional com pequenos ajustes necessários.")
        status = "BOM"  
    elif passed >= len(tests) * 0.5:
        print(f"⚠️  FUNCIONAL: {passed}/{len(tests)} testes passaram.")
        print("Sistema parcialmente operacional, requer ajustes.")
        status = "PARCIAL"
    else:
        print(f"❌ PROBLEMAS CRÍTICOS. Apenas {passed}/{len(tests)} testes passaram.")
        print("Sistema requer correções antes de usar.")
        status = "CRÍTICO"
    
    print("=" * 70)
    
    # Salvar relatório
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "tests_passed": passed,
        "tests_total": len(tests),
        "success_rate": (passed / len(tests)) * 100,
        "details": test_results
    }
    
    with open("test-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Relatório detalhado salvo em: test-report.json")

def main():
    """Executar todos os testes"""
    try:
        test_file_structure()
        test_python_dependencies() 
        test_flask_server()
        test_api_endpoints()
        generate_report()
        
    except KeyboardInterrupt:
        print("\n❌ Testes interrompidos pelo usuário.")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    
    print("\n✅ Testes concluídos!")
    input("Pressione ENTER para fechar...")

if __name__ == "__main__":
    main()

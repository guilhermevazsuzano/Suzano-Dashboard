# Adicione estas rotas ao seu dashboard_backend.py existente

from validation_creare_api import CreareAPIValidator
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

# Instância global do validador
validator = CreareAPIValidator()
validation_cache = {}
validation_lock = threading.Lock()

@app.get("/api/validation/status")
async def get_validation_status():
    """Status do sistema de validação"""
    return {
        "validation_enabled": True,
        "last_validation": validation_cache.get("last_validation"),
        "cache_status": "active" if validation_cache else "empty",
        "api_status": "configured" if validator.token else "needs_auth"
    }

@app.post("/api/validation/run")
async def run_validation():
    """Executa validação completa SharePoint vs Creare"""
    try:
        # Executar validação em thread separada para não bloquear
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_validation_sync)
            
            # Aguardar com timeout
            import concurrent.futures
            try:
                result = future.result(timeout=300)  # 5 minutos timeout
                
                with validation_lock:
                    validation_cache["last_validation"] = result
                    validation_cache["timestamp"] = datetime.now().isoformat()
                
                return {
                    "success": True,
                    "message": "Validação executada com sucesso",
                    "summary": {
                        "sharepoint_records": result["sharepoint_summary"]["total_records"],
                        "creare_events": result["creare_summary"]["total_events"],
                        "discrepancies": len(result["discrepancies"]),
                        "recommendations": len(result["recommendations"])
                    },
                    "timestamp": datetime.now().isoformat()
                }
            except concurrent.futures.TimeoutError:
                return {
                    "success": False,
                    "error": "Validação excedeu tempo limite de 5 minutos",
                    "timestamp": datetime.now().isoformat()
                }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def _run_validation_sync():
    """Executa validação de forma síncrona"""
    # Autenticar
    if not validator.get_auth_token():
        raise Exception("Falha na autenticação Creare API")
    
    # Carregar dados SharePoint
    if not validator.load_sharepoint_data():
        raise Exception("Falha ao carregar dados SharePoint")
    
    # Buscar dados Creare
    creare_events = validator.fetch_creare_events(days=7)
    
    # Executar validação
    return validator.validate_data_consistency(creare_events)

@app.get("/api/validation/report")
async def get_validation_report():
    """Retorna último relatório de validação"""
    with validation_lock:
        if not validation_cache.get("last_validation"):
            return {
                "available": False,
                "message": "Nenhuma validação executada ainda. Execute /api/validation/run primeiro."
            }
        
        report = validation_cache["last_validation"]
        return {
            "available": True,
            "report": report,
            "generated_at": validation_cache.get("timestamp"),
            "summary": {
                "sharepoint_total": report["sharepoint_summary"]["total_records"],
                "creare_total": report["creare_summary"]["total_events"], 
                "validations_performed": len(report["validation_results"]),
                "discrepancies_found": len(report["discrepancies"]),
                "recommendations_count": len(report["recommendations"])
            }
        }

@app.get("/api/validation/discrepancies")
async def get_discrepancies():
    """Retorna apenas discrepâncias encontradas"""
    with validation_lock:
        if not validation_cache.get("last_validation"):
            return {"available": False, "message": "Execute validação primeiro"}
        
        discrepancies = validation_cache["last_validation"]["discrepancies"]
        return {
            "available": True,
            "count": len(discrepancies),
            "discrepancies": discrepancies,
            "critical_count": len([d for d in discrepancies if d["severity"] == "HIGH"]),
            "timestamp": validation_cache.get("timestamp")
        }

@app.get("/api/validation/recommendations") 
async def get_recommendations():
    """Retorna recomendações baseadas na validação"""
    with validation_lock:
        if not validation_cache.get("last_validation"):
            return {"available": False, "message": "Execute validação primeiro"}
        
        recommendations = validation_cache["last_validation"]["recommendations"]
        return {
            "available": True,
            "count": len(recommendations),
            "recommendations": recommendations,
            "high_priority": [r for r in recommendations if r["priority"] == "HIGH"],
            "timestamp": validation_cache.get("timestamp")
        }

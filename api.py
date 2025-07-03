#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotel Rating Aggregator API
===========================

API REST para scraping de avaliações de hotéis de forma assíncrona.
Suporta TripAdvisor, Booking.com, Google Places e Decolar.
"""

import os
import json
import uuid
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv("config.env")

# =============================================================================
# CONFIGURAÇÃO DA API
# =============================================================================

app = FastAPI(
    title="Hotel Rating Aggregator API",
    description="API para scraping multi-site de avaliações de hotéis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações de segurança
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")
API_ENABLE_AUTH = os.getenv("API_ENABLE_AUTH", "true").lower() == "true"

# Storage em memória para jobs (em produção usar Redis/DB)
jobs_storage: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# FUNÇÕES DE SEGURANÇA
# =============================================================================

def verify_api_key(x_api_key: str = Header(None)) -> bool:
    """Verifica se a API key é válida"""
    if not API_ENABLE_AUTH:
        return True
    
    if not x_api_key:
        raise HTTPException(
            status_code=401, 
            detail="API key obrigatória. Inclua o header 'X-API-Key'"
        )
    
    if not API_SECRET_KEY:
        raise HTTPException(
            status_code=500, 
            detail="API key não configurada no servidor"
        )
    
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=401, 
            detail="API key inválida"
        )
    
    return True


# =============================================================================
# MODELOS DE DADOS
# =============================================================================

class ScrapingJob(BaseModel):
    """Modelo para job de scraping"""
    job_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    sites: Optional[list] = None
    error_message: Optional[str] = None


class ScrapingRequest(BaseModel):
    """Modelo para requisição de scraping"""
    sites: Optional[list] = None
    hotels_only: Optional[bool] = False


class ScrapingResult(BaseModel):
    """Modelo para resultado do scraping"""
    job_id: str
    status: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def generate_job_id() -> str:
    """Gera ID único para o job"""
    return str(uuid.uuid4())


def get_latest_result_file() -> Optional[str]:
    """Encontra o arquivo de resultado mais recente"""
    results_dir = Path("resultados")
    if not results_dir.exists():
        return None
    
    # Primeiro, procura por arquivos consolidados
    json_files = list(results_dir.glob("scraper_dados_*.json"))
    if json_files:
        latest_file = max(json_files, key=os.path.getctime)
        return str(latest_file)
    
    # Se não encontrar consolidados, procura por qualquer arquivo JSON de resultado
    all_json_files = list(results_dir.glob("*_dados_*.json"))
    if all_json_files:
        latest_file = max(all_json_files, key=os.path.getctime)
        print(f"Arquivo consolidado não encontrado, usando arquivo individual: {latest_file}")
        return str(latest_file)
    
    return None


def load_result_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Carrega dados do arquivo de resultado"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar {file_path}: {e}")
        return None


async def execute_scraping(job_id: str, sites: Optional[list] = None):
    """Executa o scraping em background"""
    try:
        jobs_storage[job_id]["status"] = "running"
        jobs_storage[job_id]["started_at"] = datetime.now().isoformat()
        
        print(f"Iniciando scraping para job {job_id}")
        
        # Monta comando para executar o main.py
        if sites:
            cmd = ["python3", "main.py", "--sites"] + sites
        else:
            cmd = ["python3", "main.py"]
        
        # Executa o comando de scraping
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        stdout, stderr = await process.communicate()
        
        # Verifica se o scraping terminou com sucesso
        if process.returncode == 0:
            print(f"Scraping individual concluído para job {job_id}, iniciando consolidação...")
            
            # Executa consolidação automática
            consolidate_cmd = ["python3", "main.py", "--consolidar"]
            consolidate_process = await asyncio.create_subprocess_exec(
                *consolidate_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            consolidate_stdout, consolidate_stderr = await consolidate_process.communicate()
            
            if consolidate_process.returncode == 0:
                # Busca o arquivo consolidado
                result_file = get_latest_result_file()
                
                if result_file:
                    data = load_result_data(result_file)
                    
                    jobs_storage[job_id].update({
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "result_file": result_file,
                        "data": data,
                        "stdout": stdout.decode('utf-8') if stdout else "",
                        "consolidate_stdout": consolidate_stdout.decode('utf-8') if consolidate_stdout else "",
                    })
                    
                    print(f"Scraping e consolidação concluídos para job {job_id}: {result_file}")
                else:
                    raise Exception("Arquivo consolidado não encontrado após consolidação")
            else:
                raise Exception(f"Consolidação falhou: {consolidate_stderr.decode('utf-8')}")
        else:
            raise Exception(f"Scraping falhou: {stderr.decode('utf-8')}")
            
    except Exception as e:
        jobs_storage[job_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error_message": str(e),
            "stderr": stderr.decode('utf-8') if 'stderr' in locals() else str(e)
        })
        
        print(f"Erro no scraping para job {job_id}: {e}")


# =============================================================================
# ENDPOINTS DA API
# =============================================================================

@app.get("/")
async def root():
    """Informações gerais da API"""
    return {
        "message": "Hotel Rating Aggregator API",
        "version": "2.0.0",
        "description": "API para scraping multi-site de avaliações de hotéis",
        "authentication": "Obrigatória" if API_ENABLE_AUTH else "Desabilitada",
        "endpoints": {
            "POST /scraper/start": "Inicia processo de scraping",
            "GET /scraper/status/{job_id}": "Verifica status do job",
            "GET /scraper/result/{job_id}": "Retorna resultado completo",
            "POST /scraper/consolidate": "Consolida arquivos individuais existentes",
            "GET /docs": "Documentação interativa"
        },
        "sites_supported": ["tripadvisor", "booking", "google", "decolar"],
        "timestamp": datetime.now().isoformat()
    }


@app.post("/scraper/start", response_model=ScrapingJob)
async def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key)
):
    """Inicia processo de scraping em background"""
    job_id = generate_job_id()
    
    # Valida sites se fornecidos
    valid_sites = ["tripadvisor", "booking", "google", "decolar"]
    if request.sites:
        invalid_sites = [s for s in request.sites if s not in valid_sites]
        if invalid_sites:
            raise HTTPException(
                status_code=400, 
                detail=f"Sites inválidos: {invalid_sites}. Sites válidos: {valid_sites}"
            )
    
    # Cria job no storage
    jobs_storage[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "sites": request.sites or valid_sites,
        "hotels_only": request.hotels_only
    }
    
    # Adiciona task em background
    background_tasks.add_task(execute_scraping, job_id, request.sites)
    
    print(f"Job {job_id} criado e adicionado à fila")
    
    return ScrapingJob(**jobs_storage[job_id])


@app.get("/scraper/status/{job_id}")
async def get_scraping_status(
    job_id: str,
    _: bool = Depends(verify_api_key)
):
    """Verifica status de um job de scraping"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job_data = jobs_storage[job_id]
    
    # Calcula tempo decorrido
    created_at = datetime.fromisoformat(job_data["created_at"])
    elapsed_time = (datetime.now() - created_at).total_seconds()
    
    return {
        "job_id": job_id,
        "status": job_data["status"],
        "created_at": job_data["created_at"],
        "elapsed_time_seconds": round(elapsed_time, 2),
        "sites": job_data.get("sites", []),
        "completed_at": job_data.get("completed_at"),
        "error_message": job_data.get("error_message")
    }


@app.get("/scraper/result/{job_id}", response_model=ScrapingResult)
async def get_scraping_result(
    job_id: str, 
    include_raw_data: bool = True,
    _: bool = Depends(verify_api_key)
):
    """Retorna resultado completo de um job de scraping"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job_data = jobs_storage[job_id]
    
    if job_data["status"] == "running":
        raise HTTPException(status_code=202, detail="Job ainda executando")
    
    if job_data["status"] == "queued":
        raise HTTPException(status_code=202, detail="Job na fila de execução")
    
    if job_data["status"] == "failed":
        raise HTTPException(
            status_code=500, 
            detail=f"Job falhou: {job_data.get('error_message', 'Erro desconhecido')}"
        )
    
    # Job completed - retorna dados
    result_data = job_data.get("data", {})
    
    # Prepara metadata resumida
    metadata = {
        "job_info": {
            "job_id": job_id,
            "created_at": job_data["created_at"],
            "completed_at": job_data["completed_at"],
            "sites_processed": job_data.get("sites", [])
        }
    }
    
    if result_data and "metadata" in result_data:
        metadata["scraping_stats"] = result_data["metadata"]
    
    response = ScrapingResult(
        job_id=job_id,
        status=job_data["status"],
        metadata=metadata,
        file_path=job_data.get("result_file")
    )
    
    # Inclui dados completos se solicitado
    if include_raw_data and result_data:
        response.data = result_data
    
    return response


@app.get("/scraper/jobs")
async def list_jobs(_: bool = Depends(verify_api_key)):
    """Lista todos os jobs de scraping"""
    jobs_list = []
    
    for job_id, job_data in jobs_storage.items():
        job_summary = {
            "job_id": job_id,
            "status": job_data["status"],
            "created_at": job_data["created_at"],
            "sites": job_data.get("sites", []),
            "completed_at": job_data.get("completed_at")
        }
        
        if job_data["status"] == "failed":
            job_summary["error"] = job_data.get("error_message")
        
        jobs_list.append(job_summary)
    
    return {
        "total_jobs": len(jobs_list),
        "jobs": sorted(jobs_list, key=lambda x: x["created_at"], reverse=True)
    }


@app.delete("/scraper/jobs/{job_id}")
async def delete_job(job_id: str, _: bool = Depends(verify_api_key)):
    """Remove um job do storage"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job_data = jobs_storage.pop(job_id)
    
    return {
        "message": f"Job {job_id} removido com sucesso",
        "removed_job": {
            "job_id": job_id,
            "status": job_data["status"],
            "created_at": job_data["created_at"]
        }
    }


@app.post("/scraper/consolidate")
async def manual_consolidate(_: bool = Depends(verify_api_key)):
    """Consolida manualmente os arquivos individuais existentes"""
    try:
        # Executa consolidação manual
        consolidate_cmd = ["python3", "main.py", "--consolidar"]
        process = await asyncio.create_subprocess_exec(
            *consolidate_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            result_file = get_latest_result_file()
            
            return {
                "message": "Consolidação executada com sucesso",
                "result_file": result_file,
                "stdout": stdout.decode('utf-8') if stdout else "",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Consolidação falhou: {stderr.decode('utf-8')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro na consolidação: {str(e)}"
        )


@app.get("/health")
async def health_check(_: bool = Depends(verify_api_key)):
    """Health check da API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len([j for j in jobs_storage.values() if j["status"] == "running"]),
        "total_jobs": len(jobs_storage),
        "authentication": "Enabled" if API_ENABLE_AUTH else "Disabled"
    }


# =============================================================================
# EXECUÇÃO DA API
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("Iniciando Hotel Rating Aggregator API...")
    print("Documentação: http://localhost:8000/docs")
    print("API Base: http://localhost:8000")
    print(f"Autenticação: {'Habilitada' if API_ENABLE_AUTH else 'Desabilitada'}")
    if API_ENABLE_AUTH:
        print(f"API Key necessária: {API_SECRET_KEY[:20]}...")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
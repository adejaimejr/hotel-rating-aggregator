# Hotel Rating Aggregator - Docker Image
FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="Adejaime Junior <adejaimejunior@gmail.com>"
LABEL description="Hotel Rating Aggregator API - Sistema multi-site de scraping de avaliações"
LABEL version="2.0.0"

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar arquivos do projeto
COPY . .

# Criar pasta de resultados
RUN mkdir -p resultados

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Variáveis de ambiente padrão (podem ser sobrescritas)
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Porta da API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Comando padrão - inicia a API REST
CMD ["python", "api.py"]

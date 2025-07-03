#!/bin/bash
# Hotel Rating Aggregator - Docker Test Script

set -e

echo "🧪 Hotel Rating Aggregator - Docker Test"
echo "========================================"

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado!"
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado!"
    exit 1
fi

echo "✅ Docker e Docker Compose detectados"

# Verificar se está no diretório correto
if [ ! -f "../api.py" ]; then
    echo "❌ Erro: Execute este script a partir da pasta docker/"
    exit 1
fi

# Verificar se config.env existe
if [ ! -f "../config.env" ]; then
    echo "⚠️  Arquivo config.env não encontrado!"
    echo "📋 Criando config.env temporário para teste..."
    cp ../config.env-EXEMPLO ../config.env
    echo "# Configuração temporária para teste" >> ../config.env
    echo "API_SECRET_KEY=teste_docker_$(date +%s)" >> ../config.env
    echo "✅ config.env temporário criado"
fi

# Build da imagem
echo "🔨 Testando build da imagem..."
docker-compose build --no-cache

echo "✅ Build concluído com sucesso!"

# Verificar se imagem foi criada
IMAGE_NAME=$(docker-compose config --services | head -1)
if docker images | grep -q "docker_${IMAGE_NAME}"; then
    echo "✅ Imagem Docker criada: docker_${IMAGE_NAME}"
else
    echo "⚠️  Imagem criada com nome diferente (normal)"
fi

# Testar configuração do compose
echo "🔧 Testando configuração do docker-compose..."
docker-compose config > /dev/null
echo "✅ Configuração do docker-compose válida"

echo ""
echo "✅ Todos os testes passaram!"
echo ""
echo "📋 Próximos passos:"
echo "   1. Configure o arquivo config.env (se ainda não fez)"
echo "   2. Execute: docker-compose up -d"
echo "   3. Teste: curl http://localhost:8000/"
echo ""
echo "🔧 Para setup completo execute: ./setup-docker.sh"

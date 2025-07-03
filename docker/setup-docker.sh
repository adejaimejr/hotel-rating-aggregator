#!/bin/bash
# Hotel Rating Aggregator - Docker Setup Script

set -e

echo "🚀 Hotel Rating Aggregator - Docker Setup"
echo "=========================================="

# Verificar se está no diretório correto
if [ ! -f "../api.py" ]; then
    echo "❌ Erro: Execute este script a partir da pasta docker/"
    exit 1
fi

# Criar volumes Docker Swarm
echo "📦 Criando volumes Docker..."
docker volume create hotel_rating_results || echo "Volume hotel_rating_results já existe"
docker volume create hotel_rating_logs || echo "Volume hotel_rating_logs já existe"

# Criar rede se não existir
echo "🌐 Verificando rede Docker Swarm..."
docker network create --driver overlay --attachable network_swarm_public || echo "Rede network_swarm_public já existe"

# Verificar se arquivo config.env existe
if [ ! -f "../config.env" ]; then
    echo "⚠️  Arquivo config.env não encontrado!"
    echo "📋 Criando config.env a partir do template..."
    cp ../config.env-EXEMPLO ../config.env
    echo "✅ Arquivo config.env criado!"
    echo ""
    echo "🔧 IMPORTANTE: Edite o arquivo config.env com suas configurações:"
    echo "   - API_SECRET_KEY"
    echo "   - GOOGLE_API_KEY" 
    echo "   - URLs e IDs dos seus hotéis"
    echo ""
    echo "💡 Gerar API key: python -c \"import secrets; print(secrets.token_hex(32))\""
    echo ""
    read -p "Pressione Enter após configurar o arquivo config.env..."
fi

# Verificar se config.env tem as configurações mínimas
if ! grep -q "API_SECRET_KEY=" "../config.env"; then
    echo "⚠️  API_SECRET_KEY não configurada no config.env!"
    echo "🔧 Configure pelo menos API_SECRET_KEY antes de continuar"
    exit 1
fi

# Build da imagem
echo "🔨 Construindo imagem Docker..."
docker-compose build

echo ""
echo "✅ Setup concluído!"
echo ""
echo "🚀 Para iniciar o serviço:"
echo "   docker-compose up -d"
echo ""
echo "📊 Para verificar logs:"
echo "   docker-compose logs -f"
echo ""
echo "🌐 API estará disponível em: http://localhost:8000"
echo "📖 Documentação: http://localhost:8000/docs"

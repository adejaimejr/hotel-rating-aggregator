# 🐳 Hotel Rating Aggregator - Docker Deployment

## 📋 Visão Geral

Este diretório contém todos os arquivos necessários para executar o Hotel Rating Aggregator em containers Docker, sem modificar os scripts originais.

## 🏗️ Estrutura

```
docker/
├── Dockerfile              # Imagem Docker do sistema
├── docker-compose.yml      # Orquestração dos serviços
├── docker-compose-swarm.yml # Docker Swarm específico
├── portainer-stack.yml     # Stack para Portainer (PRONTO)
├── PORTAINER-INSTRUCTIONS.md # Instruções detalhadas Portainer
├── setup-docker.sh        # Script de setup automatizado
├── test-docker.sh         # Script de teste automatizado
└── README-Docker.md       # Esta documentação
```

## 🚀 Quick Start

### 1. Setup Inicial
```bash
cd docker/
./setup-docker.sh
```

### 2. Configurar Variáveis
```bash
# Editar arquivo .env com suas configurações
cp .env-template .env
nano .env
```

### 3. Iniciar Serviços
```bash
docker-compose up -d
```

### 4. Verificar Status
```bash
docker-compose ps
docker-compose logs -f
```

## 🌟 Deploy via Portainer (Recomendado para Produção)

### Setup para Portainer
```bash
# Criar estrutura de diretórios
mkdir -p /swarm-hyperscale/stacks/hotel-rating/{resultados,logs}

# Copiar configuração
cp ../config.env /swarm-hyperscale/stacks/hotel-rating/

# Ajustar permissões
chown -R 1000:1000 /swarm-hyperscale/stacks/hotel-rating/
chmod 755 /swarm-hyperscale/stacks/hotel-rating/{resultados,logs}

# Deploy via Portainer UI:
# 1. Stacks → Add Stack
# 2. Nome: hotel-rating-aggregator  
# 3. Cole conteúdo de portainer-stack.yml
# 4. Deploy
```

### Características do Portainer Stack
- ✅ **Volumes persistentes**: `/swarm-hyperscale/stacks/hotel-rating/`
- ✅ **Health checks automáticos**: A cada 30s
- ✅ **Auto-restart**: Política de falha configurada
- ✅ **Recursos limitados**: CPU 0.5-2 cores, RAM 1-4GB
- ✅ **Rede overlay**: `network_swarm_public`

## 🔧 Configuração

### Variáveis de Ambiente Principais

```bash
# Segurança da API
API_SECRET_KEY=sua_chave_secreta_64_caracteres
API_ENABLE_AUTH=true

# Google Places API
GOOGLE_API_KEY=sua_google_api_key

# Configuração de hotéis
TRIPADVISOR_HOTEL_001=https://...
BOOKING_HOTEL_001=https://...
# ... etc
```

### Gerar API Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 📊 Comandos Úteis

### Gerenciamento do Serviço
```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Reiniciar
docker-compose restart

# Ver logs
docker-compose logs -f hotel-rating-api

# Status
docker-compose ps
```

### Build e Deploy
```bash
# Rebuild imagem
docker-compose build --no-cache

# Pull imagem mais recente
docker-compose pull

# Scale replicas
docker-compose up -d --scale hotel-rating-api=2
```

## 🌐 Endpoints da API

- **API Base**: http://localhost:8000/
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Redoc**: http://localhost:8000/redoc

## 📡 Uso da API

### Autenticação Obrigatória
Todos os endpoints (exceto info geral) requerem header:
```
X-API-Key: sua_api_secret_key
```

### Exemplo de Uso
```bash
# Iniciar scraping
curl -X POST "http://localhost:8000/scraper/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua_api_key" \
  -d '{"sites": ["booking", "google"]}'

# Verificar status
curl -X GET "http://localhost:8000/scraper/status/JOB_ID" \
  -H "X-API-Key: sua_api_key"

# Obter resultado
curl -X GET "http://localhost:8000/scraper/result/JOB_ID" \
  -H "X-API-Key: sua_api_key"
```

## 💾 Persistência de Dados

### Volumes Docker
- `hotel_rating_results`: Arquivos JSON de resultados
- `hotel_rating_logs`: Logs da aplicação

### Backup de Dados
```bash
# Backup resultados
docker run --rm -v hotel_rating_results:/data -v $(pwd):/backup alpine tar czf /backup/results-backup.tar.gz /data

# Restore resultados
docker run --rm -v hotel_rating_results:/data -v $(pwd):/backup alpine tar xzf /backup/results-backup.tar.gz -C /
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Erro de autenticação**
   ```bash
   # Verificar se API_SECRET_KEY está configurada
   docker-compose exec hotel-rating-api env | grep API_SECRET_KEY
   ```

2. **Container não inicia**
   ```bash
   # Ver logs detalhados
   docker-compose logs hotel-rating-api
   ```

3. **Sem acesso à API**
   ```bash
   # Verificar se porta está mapeada
   docker-compose port hotel-rating-api 8000
   ```

### Health Check
```bash
# Verificar saúde do container
docker-compose exec hotel-rating-api curl -f http://localhost:8000/health \
  -H "X-API-Key: $API_SECRET_KEY"
```

## 🏭 Produção

### Docker Swarm
O `docker-compose.yml` está configurado para Docker Swarm:

```bash
# Inicializar swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml hotel-rating-stack

# Verificar stack
docker stack services hotel-rating-stack
```

### Recursos Configurados
- **CPU**: 0.5-2 cores
- **Memória**: 1GB-4GB
- **Replicas**: 1 (configurável)
- **Restart**: on-failure

## ⚠️ Importante

### Compatibilidade
- ✅ Scripts Python funcionam normalmente sem Docker
- ✅ Mesmo arquivo `requirements.txt`
- ✅ Mesma estrutura de pastas
- ✅ Configuração via `config.env` ou variáveis de ambiente

### Segurança
- 🔐 Nunca commitar arquivo `.env`
- 🔐 Usar API keys únicas por ambiente
- 🔐 Rotacionar credenciais periodicamente

## 📞 Suporte

Para problemas específicos do Docker:
1. Verificar logs: `docker-compose logs -f`
2. Testar localmente: `python api.py`
3. Verificar configuração: `docker-compose config`

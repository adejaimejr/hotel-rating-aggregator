# 🐳 Hotel Rating Aggregator - Docker Deployment

## 📋 Visão Geral

Este diretório contém todos os arquivos necessários para executar o Hotel Rating Aggregator em containers Docker, **sem modificar os scripts originais**. O sistema usa o mesmo arquivo `config.env` do projeto.

## 🏗️ Estrutura

```
docker/
├── Dockerfile              # Imagem Docker do sistema
├── docker-compose.yml      # Orquestração dos serviços
├── .env-template           # Template alternativo (opcional)
├── setup-docker.sh        # Script de setup automatizado
├── test-docker.sh         # Script de teste
└── README-Docker.md       # Esta documentação

../config.env               # Arquivo de configuração principal (compartilhado)
../config.env-EXEMPLO       # Template do projeto
```

## 🚀 Quick Start

### 1. Setup Automatizado
```bash
cd docker/
./setup-docker.sh
```

### 2. Setup Manual
```bash
# Verificar se config.env existe
ls -la ../config.env

# Se não existir, criar do template
cp ../config.env-EXEMPLO ../config.env

# Editar configurações
nano ../config.env

# Criar volumes e rede
docker volume create hotel_rating_results
docker volume create hotel_rating_logs  
docker network create --driver overlay --attachable network_swarm_public

# Build e start
docker-compose build
docker-compose up -d
```

### 3. Verificar Status
```bash
docker-compose ps
docker-compose logs -f
```

## 🔧 Configuração

### Arquivo Principal: `../config.env`
O Docker usa o **mesmo arquivo `config.env`** do projeto Python, garantindo consistência.

```bash
# Variáveis principais obrigatórias
API_SECRET_KEY=sua_chave_secreta_64_caracteres
API_ENABLE_AUTH=true
GOOGLE_API_KEY=sua_google_api_key

# Configuração de hotéis (mesmo formato do projeto)
TRIPADVISOR_HOTEL_001=https://...
BOOKING_HOTEL_001=https://...
# ... etc
```

### Compatibilidade Total
- ✅ **Scripts Python funcionam normalmente** (python api.py)
- ✅ **Mesmo arquivo config.env** para Docker e execução local
- ✅ **Mesma estrutura de dados** e resultados
- ✅ **Não modifica nenhum código existente**

## 📊 Comandos Docker

### Gerenciamento do Serviço
```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Reiniciar
docker-compose restart

# Ver logs em tempo real
docker-compose logs -f

# Status dos containers
docker-compose ps

# Entrar no container
docker-compose exec hotel-rating-api bash
```

### Build e Manutenção
```bash
# Rebuild completo
docker-compose build --no-cache

# Testar configuração
docker-compose config

# Ver recursos utilizados
docker stats

# Limpar recursos não utilizados
docker system prune
```

## 🌐 Endpoints da API

Uma vez iniciado o container:

- **API Base**: http://localhost:8000/
- **Documentação**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Redoc**: http://localhost:8000/redoc

## 📡 Uso da API (Igual à Execução Local)

### Autenticação
```bash
# Usar mesma API key do config.env
X-API-Key: valor_do_API_SECRET_KEY
```

### Exemplos
```bash
# Iniciar scraping
curl -X POST "http://localhost:8000/scraper/start" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $(grep API_SECRET_KEY ../config.env | cut -d'=' -f2)" \
  -d '{"sites": ["booking", "google"]}'

# Status do job
curl -X GET "http://localhost:8000/scraper/status/JOB_ID" \
  -H "X-API-Key: $(grep API_SECRET_KEY ../config.env | cut -d'=' -f2)"
```

## 💾 Persistência e Volumes

### Volumes Criados
- `hotel_rating_results`: Pasta `/app/resultados` (JSONs gerados)
- `hotel_rating_logs`: Pasta `/app/logs` (logs da aplicação)

### Acessar Dados
```bash
# Ver resultados
docker-compose exec hotel-rating-api ls -la resultados/

# Copiar resultados para host
docker cp $(docker-compose ps -q hotel-rating-api):/app/resultados ./resultados_backup

# Backup completo dos volumes
docker run --rm -v hotel_rating_results:/data -v $(pwd):/backup alpine tar czf /backup/results-backup.tar.gz -C / data
```

## 🔍 Troubleshooting

### Problemas Comuns

1. **Arquivo config.env não encontrado**
   ```bash
   # Criar do template
   cp ../config.env-EXEMPLO ../config.env
   # Editar com suas configurações
   ```

2. **Container não inicia**
   ```bash
   # Ver logs detalhados
   docker-compose logs hotel-rating-api
   
   # Verificar configuração
   docker-compose config
   ```

3. **API não responde**
   ```bash
   # Verificar se porta está mapeada
   docker-compose port hotel-rating-api 8000
   
   # Testar localmente primeiro
   cd .. && python api.py
   ```

4. **Problemas de autenticação**
   ```bash
   # Verificar API key no container
   docker-compose exec hotel-rating-api env | grep API_SECRET_KEY
   ```

### Health Check
```bash
# Verificar saúde do serviço
API_KEY=$(grep API_SECRET_KEY ../config.env | cut -d'=' -f2)
curl -H "X-API-Key: $API_KEY" http://localhost:8000/health
```

## 🏭 Produção e Docker Swarm

### Deploy em Swarm
```bash
# Inicializar swarm
docker swarm init

# Deploy da stack
docker stack deploy -c docker-compose.yml hotel-rating-stack

# Verificar serviços
docker stack services hotel-rating-stack

# Logs do swarm
docker service logs hotel-rating-stack_hotel-rating-api
```

### Recursos Configurados
- **CPU**: 0.5-2 cores
- **Memória**: 1GB-4GB  
- **Replicas**: 1 (escalável)
- **Restart**: on-failure
- **Placement**: node.role == manager

## 🔄 Testes

### Teste Automatizado
```bash
./test-docker.sh
```

### Teste Manual
```bash
# 1. Testar build
docker-compose build

# 2. Testar configuração
docker-compose config

# 3. Testar start
docker-compose up -d

# 4. Testar API
curl http://localhost:8000/

# 5. Cleanup
docker-compose down
```

## ⚠️ Importante

### Compatibilidade Garantida
- ✅ **Execução local funciona**: `python api.py`
- ✅ **Scripts funcionam**: `python main.py --status`
- ✅ **Mesmo config.env**: compatibilidade total
- ✅ **Mesmos resultados**: pasta `resultados/`

### Segurança
- �� config.env já está no .gitignore
- 🔐 Usar API keys únicas por ambiente
- 🔐 Container roda como usuário não-root

### Deploy no Servidor
1. Copiar projeto completo para servidor
2. Certificar que config.env está configurado
3. Executar `cd docker && ./setup-docker.sh`
4. Verificar com `docker-compose ps`

## 📞 Suporte

Para problemas específicos:
1. **Teste local primeiro**: `python api.py`
2. **Verificar config.env**: arquivo existe e tem API_SECRET_KEY
3. **Logs Docker**: `docker-compose logs -f`
4. **Teste configuração**: `docker-compose config`

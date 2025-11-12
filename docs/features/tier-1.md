# TweetPulse Tier 1 - User Stories

## Feature 1: Real-time Tweet Ingestion

### US-1.1: Conectar com Twitter API
**Como** desenvolvedor  
**Quero** conectar a aplicação com a Twitter API v2  
**Para** poder receber tweets em tempo real

**Critérios de Aceite:**
- Autenticação com Twitter API usando Bearer Token
- Gerenciar rate limits (450 requisições/15 min)
- Retry automático em caso de timeout
- Logs de conexão e erros
- Timeout para reconexão após falha > 5s

**Tarefas Técnicas:**
- Instalar Tweepy
- Criar TweetFetcher service com async
- Implementar circuit breaker
- Configurar logging

**Dados de Teste:**
- Keyword: "python", "#technology"
- Validar 20+ tweets em 1 minuto

---

### US-1.2: Armazenar tweets em PostgreSQL
**Como** analista  
**Quero** que tweets sejam salvos no banco de dados  
**Para** poder consultar histórico depois

**Critérios de Aceite:**
- Tweets salvos com: id, content, author_id, created_at, metrics
- Sem duplicatas (tweet_id é unique)
- Índices em: author_id, created_at
- Performance: < 100ms para insert
- Validação de dados antes de salvar

**Tarefas Técnicas:**
- Criar Tweet model (SQLAlchemy)
- Criar TweetRepository
- Implementar deduplicação
- Migration Alembic

**Dados de Teste:**
- 1000 tweets sem duplicatas
- Verificar índices criados

---

### US-1.3: Cache de tweets em Redis
**Como** usuário  
**Quero** que tweets populares sejam cacheados  
**Para** ter respostas rápidas

**Critérios de Aceite:**
- Últimos 100 tweets em cache
- TTL de 5 minutos
- Invalidar cache ao novo tweet chegar
- Cache key pattern: "tweets:recent"
- Fallback para DB se cache vazio

**Tarefas Técnicas:**
- Implementar CacheService
- Redis connection pool
- TTL management
- Cache invalidation

**Dados de Teste:**
- Cache hit rate > 80%
- Response time < 10ms (cached)

---

### US-1.4: Retry automático com backoff
**Como** operador  
**Quero** que falhas temporárias sejam recuperadas  
**Para** ter alta disponibilidade

**Critérios de Aceite:**
- 3 tentativas máximo
- Backoff exponencial: 1s, 2s, 4s
- Logs de cada tentativa
- Não retentar erros 400-level
- Breaker aberto após 5 falhas seguidas

**Tarefas Técnicas:**
- Implementar retry decorator
- Circuit breaker pattern
- Logging estruturado

**Dados de Teste:**
- Simular timeout, validar retry
- Validar que após 5 falhas para de tentar

---

## Feature 2: Sentiment Analysis Pipeline

### US-2.1: Carregar modelo de sentiment
**Como** cientista de dados  
**Quero** usar um modelo pré-treinado de sentiment  
**Para** não ter que treinar do zero

**Critérios de Aceite:**
- Usar modelo HuggingFace: distilbert-base-uncased-finetuned-sst-2-english
- Cache de modelo em memória (lazy load)
- Suportar GPU se disponível
- Fallback para CPU
- Tempo de carregamento < 2s

**Tarefas Técnicas:**
- Instalar transformers, torch
- Criar SentimentModel class
- Pipeline abstrato
- GPU detection

**Dados de Teste:**
- "I love Python" → Positive
- "This is terrible" → Negative
- "The weather is ok" → Neutral

---

### US-2.2: Processar tweets em batch
**Como** processador  
**Quero** analisar múltiplos tweets simultaneamente  
**Para** economizar tempo

**Critérios de Aceite:**
- Batch size: 32 tweets
- Tempo máximo: 100ms por tweet
- Manter ordem dos resultados
- Tratar erros sem falhar o batch inteiro

**Tarefas Técnicas:**
- Implementar batch_predict method
- Async processing
- Error handling robusto

**Dados de Teste:**
- 1000 tweets, verificar tempo total
- Um tweet inválido no batch não falha tudo

---

### US-2.3: Armazenar sentimento no banco
**Como** analista  
**Quero** saber o sentimento de cada tweet  
**Para** gerar relatórios

**Critérios de Aceite:**
- Adicionar colunas: sentiment (enum), confidence (0-1)
- Atualizar tweet com resultado
- Índice em sentiment para queries rápidas
- Validação: confidence > 0.5

**Tarefas Técnicas:**
- Migration para adicionar colunas
- Update Tweet model
- Índice em sentiment

**Dados de Teste:**
- 100 tweets com sentimento
- Query "WHERE sentiment = 'POSITIVE'" < 50ms

---

### US-2.4: Enqueuer em Celery
**Como** processador de background  
**Quero** que sentiment seja calculado async  
**Para** não bloquear a API

**Critérios de Aceite:**
- Nova tarefa Celery para cada tweet
- Fila priorizada: tweets com > 1k followers = alta prioridade
- Retry automático se falhar
- Máximo 3 retries
- Timeout: 5 minutos

**Tarefas Técnicas:**
- Criar sentiment_task.py
- Queue prioritizado
- Celery config

**Dados de Teste:**
- 100 tweets enfileirados
- Todos processados em < 1 minuto
- Validar retry após erro simulado

---

## Feature 3: Real-time Dashboard

### US-3.1: Endpoint para tweets recentes
**Como** usuário frontend  
**Quero** um endpoint que retorne tweets recentes  
**Para** mostrar no dashboard

**Critérios de Aceite:**
- GET /api/v1/tweets?limit=20&offset=0
- Response em < 200ms
- Retorna: id, content, sentiment, author, created_at
- Ordenado por created_at DESC
- Validação: limit max 100

**Tarefas Técnicas:**
- Criar router tweets.py
- Paginação com offset/limit
- Serialização com Pydantic

**Dados de Teste:**
- 50 tweets, paginar por 10
- Response payload valida schema

---

### US-3.2: Endpoint para distribuição de sentimentos
**Como** analista  
**Quero** saber quantos tweets são positivos/negativos/neutros  
**Para** visualizar no gráfico

**Critérios de Aceite:**
- GET /api/v1/analytics/sentiment-distribution
- Retorna: {"positive": 45, "negative": 20, "neutral": 35}
- Filtro opcional: period=24h (padrão)
- Response < 500ms
- Cache por 5 minutos

**Tarefas Técnicas:**
- Query aggregação (GROUP BY sentiment)
- Analytics service
- Cache

**Dados de Teste:**
- 100 tweets com distribuição conhecida
- Validar contagem exata

---

### US-3.3: Endpoint para tweets por hora
**Como** analista  
**Quero** saber quantos tweets chegam por hora  
**Para** entender padrões de atividade

**Critérios de Aceite:**
- GET /api/v1/analytics/tweets-per-hour?period=24h
- Retorna: [{"hour": "00:00", "count": 150}, ...]
- Hora em UTC
- Cache por 10 minutos
- Response < 300ms

**Tarefas Técnicas:**
- Query com DATE_TRUNC
- Analytics service
- Serialização

**Dados de Teste:**
- 1000 tweets em 24h
- Distribuição uniforme validada

---

### US-3.4: Dashboard HTML simples
**Como** gerente  
**Quero** ver um dashboard básico em HTML  
**Para** monitorar em tempo real

**Critérios de Aceite:**
- GET / retorna HTML com gráficos
- Atualiza a cada 30 segundos (polling)
- Mostra: tweets/hora, distribuição sentimentos, últimos tweets
- Responsivo (mobile-friendly)
- Sem dependência de JS framework (vanilla JS)

**Tarefas Técnicas:**
- HTML template
- Charting library (Chart.js ou Plotly)
- JavaScript para polling
- CSS básico

**Dados de Teste:**
- Abrir no browser, validar gráficos
- Atualização a cada 30s

---

## Feature 4: Search & Filter API

### US-4.1: Busca por keyword
**Como** usuário  
**Quero** buscar tweets por palavras-chave  
**Para** encontrar tweets específicos

**Critérios de Aceite:**
- GET /api/v1/tweets/search?q=python
- Full-text search via PostgreSQL
- Response < 500ms para < 1M tweets
- Retorna: id, content, sentiment, created_at
- Limit: max 100 results

**Tarefas Técnicas:**
- Query LIKE ou tsvector
- Índice em content
- Validação de query

**Dados de Teste:**
- 100 tweets com keyword "python"
- Query "python" retorna relevantes

---

### US-4.2: Filtro por sentimento
**Como** analista  
**Quero** filtrar tweets por sentimento  
**Para** analisar subconjunto

**Critérios de Aceite:**
- GET /api/v1/tweets?sentiment=positive
- Valores válidos: positive, negative, neutral
- Combina com search query
- Response < 300ms
- Validação: sentiment é enum válido

**Tarefas Técnicas:**
- Query filtering
- Validação de enum
- Índice em sentiment

**Dados de Teste:**
- 100 tweets, filtrar por "positive"
- Resultado contém apenas positivos

---

### US-4.3: Filtro por período
**Como** analista  
**Quero** filtrar tweets por data  
**Para** analisar período específico

**Critérios de Aceite:**
- GET /api/v1/tweets?start_date=2024-01-01&end_date=2024-01-31
- Formato: YYYY-MM-DD
- Combina com outros filtros
- Response < 300ms
- Validação: start_date < end_date

**Tarefas Técnicas:**
- Query WHERE created_at BETWEEN
- Date parsing e validação
- Índice em created_at

**Dados de Teste:**
- 100 tweets em janeiro, filtrar por período
- Resultado só contém tweets do período

---

### US-4.4: Paginação com cursor
**Como** desenvolvedor  
**Quero** usar cursor-based pagination  
**Para** ter performance consistente

**Critérios de Aceite:**
- GET /api/v1/tweets?cursor=abc123&limit=20
- Response inclui: data[], next_cursor, has_more
- Cursor é base64 encoded
- Performance consistente para página 1000
- Validação: limit max 100

**Tarefas Técnicas:**
- Implementar cursor pagination
- Encoding/decoding
- Query otimizado

**Dados de Teste:**
- 10k tweets, paginar com cursor
- Performance < 200ms em qualquer página

---

## Feature 5: User Authentication & Authorization

### US-5.1: Login com email/senha
**Como** usuário  
**Quero** fazer login com email e senha  
**Para** acessar minha conta

**Critérios de Aceite:**
- POST /api/v1/auth/login
- Request: email, password
- Response: access_token, refresh_token
- Tokens JWT com 24h e 7 dias TTL
- Validação: email válido, senha > 8 chars
- Hash: bcrypt

**Tarefas Técnicas:**
- User model com email, password_hash
- JWT generation
- Bcrypt hashing
- Login endpoint

**Dados de Teste:**
- Registrar usuário, fazer login
- Tokens válidos por período configurado

---

### US-5.2: Refresh token
**Como** usuário  
**Quero** renovar meu access token expirado  
**Para** continuar autenticado

**Critérios de Aceite:**
- POST /api/v1/auth/refresh
- Request: refresh_token
- Response: new_access_token, new_refresh_token
- Refresh token válido por 7 dias
- Invalidar refresh token antigo após uso

**Tarefas Técnicas:**
- Refresh token logic
- Token invalidation
- Endpoint

**Dados de Teste:**
- Login, esperar expiração access
- Refresh funciona, novo token válido

---

### US-5.3: Logout
**Como** usuário  
**Quero** fazer logout  
**Para** invalidar minha sessão

**Critérios de Aceite:**
- POST /api/v1/auth/logout
- Invalidar refresh_token no banco
- Apagar sessão em cache (Redis)
- Response: success message
- Requer autenticação

**Tarefas Técnicas:**
- Logout endpoint
- Token revocation (blacklist)
- Cache invalidation

**Dados de Teste:**
- Login, logout, validar que token inválido

---

### US-5.4: Role-based access control
**Como** administrador  
**Quero** controlar quem acessa quais endpoints  
**Para** garantir segurança

**Critérios de Aceite:**
- Roles: viewer, analyst, admin
- GET /api/v1/admin/* requer admin
- GET /api/v1/analytics/* requer analyst ou admin
- Retorna 403 Forbidden se não autorizado
- Role no JWT token

**Tarefas Técnicas:**
- Role column em User
- Role guard/middleware
- JWT include role

**Dados de Teste:**
- Criar usuários com roles
- Testar acesso com cada role
- Validar 403 para não autorizado

---

## Summary

**Total User Stories: 16**
- Feature 1: 4 stories
- Feature 2: 4 stories
- Feature 3: 4 stories
- Feature 4: 4 stories
- Feature 5: 4 stories

**Estimativa:**
- Cada story: 4-8 horas
- Total Tier 1: 64-128 horas (2-3 semanas)
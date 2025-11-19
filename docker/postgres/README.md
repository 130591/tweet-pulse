# PostgreSQL Schema - TweetPulse

## Estrutura de Tabelas

Este diretório contém os scripts de inicialização do banco de dados PostgreSQL para o TweetPulse.

### Tabelas Principais

#### 1. `twitter_profiles`
Armazena dados públicos de perfis do Twitter coletados via API.

**Campos:**
- `id` (BIGINT): ID do Twitter do usuário
- `username` (VARCHAR): Nome de usuário (@username)
- `name` (VARCHAR): Nome completo
- `is_protected` (BOOLEAN): Se o perfil é protegido (compliance GDPR)
- `created_at` (TIMESTAMPTZ): Data de criação no Twitter
- `last_updated` (TIMESTAMPTZ): Última atualização dos dados

#### 2. `profile_snapshots`
Snapshots históricos de métricas de perfis para análise de crescimento.

**Campos:**
- `id` (SERIAL): ID interno
- `profile_id` (BIGINT): Referência ao perfil
- `captured_at` (TIMESTAMPTZ): Momento da captura
- `followers_count` (INT): Número de seguidores
- `following_count` (INT): Número seguindo
- `tweet_count` (INT): Total de tweets
- `location` (VARCHAR): Localização do perfil

**Uso:**
```sql
-- Ver crescimento de seguidores de um perfil
SELECT 
    captured_at,
    followers_count,
    followers_count - LAG(followers_count) OVER (ORDER BY captured_at) AS crescimento
FROM profile_snapshots
WHERE profile_id = 123456789
ORDER BY captured_at;
```

#### 3. `tweets`
Tweets coletados e processados.

**Campos:**
- `id` (BIGINT): ID do tweet
- `profile_id` (BIGINT): ID do autor
- `parent_tweet_id` (BIGINT): ID do tweet pai (para threads)
- `content` (TEXT): Conteúdo do tweet
- `language` (VARCHAR): Idioma detectado
- `created_at` (TIMESTAMPTZ): Data de criação
- `ingested_at` (TIMESTAMPTZ): Data de ingestão no sistema
- `processed_at` (TIMESTAMPTZ): Data de processamento
- `retweet_count`, `reply_count`, `like_count`, `quote_count`: Métricas de engajamento

#### 4. `entities`
Entidades nomeadas extraídas via NLP (Named Entity Recognition).

**Tipos válidos:**
- `PERSON`: Pessoas
- `ORG`: Organizações
- `LOCATION`: Locais
- `PRODUCT`: Produtos
- `EVENT`: Eventos

#### 5. `hashtags`
Hashtags extraídas dos tweets.

#### 6. `mentions`
Menções de usuários nos tweets.

#### 7. `media`
Mídias anexadas aos tweets (fotos, vídeos, GIFs).

#### 8. `sentiments`
Análise de sentimento dos tweets.

**Valores válidos:**
- `POSITIVE`: Sentimento positivo
- `NEUTRAL`: Sentimento neutro
- `NEGATIVE`: Sentimento negativo

## Inicialização

Os scripts neste diretório (`docker/postgres/initdb/`) são executados automaticamente quando o container PostgreSQL é criado pela primeira vez.

### Como iniciar:

```bash
# Parar containers existentes
docker-compose -f docker-compose-dev.yml down

# Remover volume antigo (se necessário resetar o banco)
docker volume rm tweet-pulse_postgres_data

# Iniciar com novo schema
docker-compose -f docker-compose-dev.yml up -d db

# Verificar logs
docker-compose -f docker-compose-dev.yml logs db
```

### Verificar tabelas criadas:

```bash
docker exec -it tweet-pulse-db-1 psql -U user -d tweetpulse -c "\dt"
```

## Índices

O schema inclui vários índices para otimização:

- **B-Tree Indexes**: Para buscas por ID, username, tags
- **BRIN Index**: Para dados temporais (`tweets.created_at`)
- **Foreign Keys**: Com `ON DELETE CASCADE` para integridade referencial

## Compliance e Segurança

- **GDPR**: Campo `is_protected` indica perfis protegidos
- **Constraints**: Validações de tipo e valores positivos
- **Cascading Deletes**: Exclusão automática de dados relacionados

## Queries Úteis

### Ver tweets mais engajados:
```sql
SELECT 
    t.id,
    t.content,
    tp.username,
    (t.retweet_count + t.like_count + t.reply_count + t.quote_count) AS total_engagement
FROM tweets t
JOIN twitter_profiles tp ON t.profile_id = tp.id
ORDER BY total_engagement DESC
LIMIT 10;
```

### Top hashtags:
```sql
SELECT 
    tag,
    COUNT(*) as count,
    AVG(t.retweet_count + t.like_count) as avg_engagement
FROM hashtags h
JOIN tweets t ON h.tweet_id = t.id
GROUP BY tag
ORDER BY count DESC
LIMIT 20;
```

### Crescimento de perfil:
```sql
SELECT 
    date_trunc('day', captured_at) as dia,
    MAX(followers_count) as seguidores
FROM profile_snapshots
WHERE profile_id = 123456789
GROUP BY dia
ORDER BY dia;
```

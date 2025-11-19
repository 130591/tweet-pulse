-- TweetPulse Database Schema
-- Criado automaticamente no startup do container PostgreSQL

-- Tabela de perfis do Twitter (dados públicos coletados)
CREATE TABLE IF NOT EXISTS twitter_profiles (
    id BIGINT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    name VARCHAR(100),
    is_protected BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ,
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de snapshots históricos de perfis
CREATE TABLE IF NOT EXISTS profile_snapshots (
    id SERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES twitter_profiles(id) ON DELETE CASCADE,
    captured_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    followers_count INT,
    following_count INT,
    tweet_count INT,
    location VARCHAR(100)
);

-- Tabela de tweets
CREATE TABLE IF NOT EXISTS tweets (
    id BIGINT PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES twitter_profiles(id) ON DELETE CASCADE,
    parent_tweet_id BIGINT REFERENCES tweets(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    language VARCHAR(10),
    created_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ,
    retweet_count INT DEFAULT 0,
    reply_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    quote_count INT DEFAULT 0,
    
    CONSTRAINT positive_counts CHECK (
        retweet_count >= 0 AND
        reply_count >= 0 AND
        like_count >= 0 AND
        quote_count >= 0
    )
);

-- Tabela de entidades reconhecidas (NLP)
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT NOT NULL REFERENCES tweets(id) ON DELETE CASCADE,
    text VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,
    score DECIMAL(5,4),
    
    CONSTRAINT valid_entity_type CHECK (type IN ('PERSON', 'ORG', 'LOCATION', 'PRODUCT', 'EVENT'))
);

-- Tabela de hashtags
CREATE TABLE IF NOT EXISTS hashtags (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT NOT NULL REFERENCES tweets(id) ON DELETE CASCADE,
    tag VARCHAR(100) NOT NULL
);

-- Tabela de menções
CREATE TABLE IF NOT EXISTS mentions (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT NOT NULL REFERENCES tweets(id) ON DELETE CASCADE,
    mentioned_profile_id BIGINT NOT NULL REFERENCES twitter_profiles(id) ON DELETE CASCADE
);

-- Tabela de mídias
CREATE TABLE IF NOT EXISTS media (
    id SERIAL PRIMARY KEY,
    tweet_id BIGINT NOT NULL REFERENCES tweets(id) ON DELETE CASCADE,
    url VARCHAR(255) NOT NULL,
    type VARCHAR(20),
    alt_text TEXT
);

-- Tabela de sentimentos (análise)
CREATE TABLE IF NOT EXISTS sentiments (
    tweet_id BIGINT PRIMARY KEY REFERENCES tweets(id) ON DELETE CASCADE,
    label VARCHAR(10) NOT NULL,
    score DECIMAL(3,2) NOT NULL,
    model VARCHAR(50) NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_sentiment CHECK (label IN ('POSITIVE', 'NEUTRAL', 'NEGATIVE'))
);

-- Índices para otimização
CREATE INDEX IF NOT EXISTS idx_tweets_profile ON tweets(profile_id);
CREATE INDEX IF NOT EXISTS idx_tweets_created ON tweets(created_at);
CREATE INDEX IF NOT EXISTS idx_tweets_ingested ON tweets(ingested_at);
CREATE INDEX IF NOT EXISTS idx_entities_text ON entities(text);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_hashtags_tag ON hashtags(tag);
CREATE INDEX IF NOT EXISTS idx_mentions_profile ON mentions(mentioned_profile_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_profile ON profile_snapshots(profile_id, captured_at);

-- Índice BRIN para dados temporais (mais eficiente para time-series)
CREATE INDEX IF NOT EXISTS idx_tweets_created_brin ON tweets USING BRIN(created_at);

-- Comentários para documentação
COMMENT ON TABLE twitter_profiles IS 'Perfis públicos do Twitter coletados via API';
COMMENT ON TABLE profile_snapshots IS 'Histórico de métricas de perfis para análise de crescimento';
COMMENT ON TABLE tweets IS 'Tweets coletados e processados';
COMMENT ON TABLE entities IS 'Entidades nomeadas extraídas via NLP';
COMMENT ON TABLE hashtags IS 'Hashtags extraídas dos tweets';
COMMENT ON TABLE sentiments IS 'Análise de sentimento dos tweets';

-- Log de criação
DO $$
BEGIN
    RAISE NOTICE 'Schema TweetPulse criado com sucesso!';
    RAISE NOTICE 'Tabelas: twitter_profiles, profile_snapshots, tweets, entities, hashtags, mentions, media, sentiments';
END $$;

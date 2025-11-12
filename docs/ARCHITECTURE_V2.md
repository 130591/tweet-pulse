# TweetPulse Architecture v2.0

## Overview
TweetPulse now implements a distributed architecture with specialized workers for real-time indexing and persistence.

## Architecture Diagram

```
┌──────────────────────────┐
│   Twitter API / Stream   │
└────────────┬─────────────┘
             ↓
      [Redis Stream]
      (Ingest Layer)
             ↓
       ┌─────┴─────┐
       │           │
[Elastic Worker]  [Persist Worker]
       │           │
       ↓           ↓
[ElasticSearch]  [PostgreSQL]
       │           │
       └─────┬─────┘
             ↓
        [REST API]
             ↓
      [React Frontend]
```

## Components

### 1. **Ingestion Layer**
- **Redis Stream**: Message queue for incoming tweets
- **Deduplication**: Using RedisBloom for efficient duplicate detection
- **Distributed Locks**: Redis-based locking for coordination

### 2. **Processing Workers**

#### **Elastic Worker** (`elastic_worker`)
- **Purpose**: Real-time indexing and analysis
- **Features**:
  - Sentiment analysis
  - Entity extraction
  - Keyword extraction
  - Real-time indexing to ElasticSearch
- **Batch Size**: 50 tweets
- **Batch Timeout**: 5 seconds

#### **Persist Worker** (`persist_worker`)
- **Purpose**: Durable storage and aggregations
- **Features**:
  - PostgreSQL persistence
  - Hourly aggregations
  - Metrics calculation
  - Batch optimized writes
- **Batch Size**: 100 tweets
- **Batch Timeout**: 10 seconds

### 3. **Storage Layer**

#### **ElasticSearch**
- **Purpose**: Search and analytics
- **Indices**:
  - `tweets`: Individual tweet documents
  - `tweet_aggregations`: Pre-computed analytics
- **Features**:
  - Full-text search
  - Real-time aggregations
  - Sentiment analytics
  - Entity analytics

#### **PostgreSQL**
- **Purpose**: Durable storage and historical data
- **Tables**:
  - `tweets`: Raw tweet data
  - `tweet_aggregations`: Time-series aggregations
- **Features**:
  - ACID compliance
  - Historical queries
  - Data integrity

#### **Redis**
- **Purpose**: Caching and coordination
- **Usage**:
  - Stream for message queue
  - Bloom filters for deduplication
  - Distributed locks
  - Temporary caching

### 4. **API Layer**
- **Framework**: FastAPI
- **Endpoints**:
  - `/api/elastic/search`: Search tweets
  - `/api/elastic/analytics/sentiment`: Sentiment analytics
  - `/api/elastic/analytics/entities`: Entity extraction analytics
  - `/api/tweets`: PostgreSQL queries
  - `/api/ingestion`: Stream management

### 5. **Frontend**
- **Stack**: React + Ant Design
- **Features**:
  - Real-time dashboard
  - Search interface
  - Analytics visualization
  - Stream monitoring

## Data Flow

1. **Ingestion**: Tweets arrive via Twitter API or simulator
2. **Queueing**: Tweets pushed to Redis Stream
3. **Processing**: Workers consume from stream in parallel
   - Elastic Worker: Enriches and indexes for search
   - Persist Worker: Stores and aggregates in PostgreSQL
4. **Serving**: API serves data from both ElasticSearch and PostgreSQL
5. **Visualization**: Frontend displays real-time and historical data

## Deployment

### Docker Services

```yaml
services:
  - app           # FastAPI application
  - elastic_worker # ElasticSearch indexing
  - persist_worker # PostgreSQL persistence
  - elasticsearch  # Search engine
  - db            # PostgreSQL database
  - redis         # Redis + RedisBloom
  - simulator     # Tweet stream simulator
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/tweetpulse
ELASTICSEARCH_URL=http://elasticsearch:9200
REDIS_URL=redis://redis:6379

# Workers
WORKER_ID=worker_1
BATCH_SIZE=100
BATCH_TIMEOUT=10.0
ENABLE_AGGREGATIONS=true

# Stream
STREAM_START_FROM=$  # Start from end (production)
```

## Scaling Considerations

### Horizontal Scaling
- **Workers**: Add more worker instances with unique IDs
- **ElasticSearch**: Add nodes for clustering
- **Redis**: Use Redis Cluster for high availability

### Performance Optimization
- **Batch Processing**: Tunable batch sizes and timeouts
- **Index Optimization**: ElasticSearch mappings optimized for queries
- **Connection Pooling**: Async connections with pooling
- **Caching**: Redis for frequently accessed data

## Monitoring

### Metrics
- **Worker Metrics**: Total processed, failed, batch sizes
- **ElasticSearch**: Index size, query performance
- **PostgreSQL**: Connection pool, query times
- **Redis**: Memory usage, stream length

### Health Checks
- All services include health endpoints
- Docker health checks configured
- Automatic restart on failure

## Future Enhancements

1. **Message Queue**: Replace Redis Stream with Kafka/Kinesis
2. **Monitoring**: Add Grafana/Prometheus
3. **ML Pipeline**: Real-time model serving
4. **Multi-tenancy**: Support multiple projects/keywords
5. **WebSocket**: Real-time updates to frontend

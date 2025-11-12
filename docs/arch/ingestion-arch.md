**Arquitetura completa do Tweet Pulse:**
```
┌─────────────────────────────────────────────────────┐
│         TWEET SOURCE (API / Stream)                 │
└────────────────────┬────────────────────────────────┘
                     │ (UM tweet por vez)
                     ↓
┌─────────────────────────────────────────────────────┐
│  Redis Queue (Celery Broker)                        │
│  - tweets_queue                                     │
│  - Max: 1M items                                    │
│  - Retry: automático                                │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    ┌────────┐  ┌────────┐  ┌────────┐
    │Worker 1│  │Worker 2│  │Worker 3│ ... x10
    └────┬───┘  └────┬───┘  └────┬───┘
         │           │           │
         └─────────┬─────────────┘
                   ↓
    ┌──────────────────────────────┐
    │ Processing (em cada worker):  │
    │ - Validação                   │
    │ - Enriquecimento              │
    │ - Deduplicação                │
    │ - NLP/análise                 │
    └──────────┬───────────────────┘
               ↓
    ┌──────────────────────────────┐
    │ PostgreSQL                    │
    │ - tweets table                │
    │ - tweets_stats               │
    └──────────┬───────────────────┘
               ↓
    ┌──────────────────────────────┐
    │ Redis Cache                   │
    │ - feed:{userId}               │
    │ - stats:{type}                │
    └──────────┬───────────────────┘
               ↓
    ┌──────────────────────────────┐
    │ WebSocket (100k users)        │
    │ - Push updates               │
    │ - Real-time notifications    │
    └──────────────────────────────┘

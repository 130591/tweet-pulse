# TweetPulse Lite Version 🪶

Versão otimizada do TweetPulse sem PyTorch e HuggingFace Transformers, reduzindo drasticamente o tamanho da imagem Docker e uso de memória.

## 📊 Comparação

| Aspecto | Versão Completa | Versão Lite |
|---------|----------------|-------------|
| **Tamanho da imagem Docker** | ~3.5 GB | ~500 MB |
| **Memória RAM necessária** | ~2-4 GB | ~500 MB - 1 GB |
| **Tempo de build** | ~10-15 min | ~2-3 min |
| **Dependências ML** | PyTorch + Transformers | VADER Sentiment |
| **Modelo de sentimento** | DistilBERT (fine-tuned) | VADER (rule-based) |
| **Precisão** | ~90-95% | ~80-85% |
| **Velocidade** | Moderada | Muito rápida |

## 🚀 Como Usar

### Opção 1: Docker Compose (Recomendado)

```bash
# Subir a versão lite
docker-compose -f docker-compose-lite.yml up --build

# Parar
docker-compose -f docker-compose-lite.yml down
```

### Opção 2: Instalação Local

```bash
# Instalar dependências leves
pip install -r requirements-lite.txt

# Configurar variável de ambiente
export USE_LITE_ENRICHMENT=1

# Rodar aplicação
uvicorn tweetpulse.main:app --reload
```

## 🔧 Diferenças Técnicas

### Análise de Sentimento

**Versão Completa:**
- Usa modelo DistilBERT fine-tuned da HuggingFace
- Deep learning com transformers
- Requer GPU/CPU intensivo
- Melhor para textos complexos e nuances

**Versão Lite:**
- Usa VADER (Valence Aware Dictionary and sEntiment Reasoner)
- Baseado em regras e léxico
- Otimizado para textos de redes sociais
- Processa emojis, pontuação, e gírias

### Código

A versão lite usa `enrichment_lite.py` ao invés de `enrichment.py`:

```python
# enrichment.py (completa)
from transformers import pipeline
import torch

# enrichment_lite.py (lite)
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
```

## 📦 Arquivos da Versão Lite

```
tweet-pulse/
├── requirements-lite.txt          # Dependências sem PyTorch
├── Dockerfile.lite                # Dockerfile otimizado
├── docker-compose-lite.yml        # Compose para versão lite
└── src/tweetpulse/ingestion/
    └── enrichment_lite.py         # Enricher com VADER
```

## 🎯 Quando Usar Cada Versão

### Use a Versão Completa se:
- ✅ Você tem recursos de hardware disponíveis (>4GB RAM)
- ✅ Precisa da maior precisão possível
- ✅ Trabalha com textos complexos e nuances sutis
- ✅ Tem GPU disponível para acelerar inferência

### Use a Versão Lite se:
- ✅ Quer desenvolvimento rápido e iterativo
- ✅ Tem recursos limitados (laptop, CI/CD)
- ✅ Foca em tweets e textos de redes sociais
- ✅ Prioriza velocidade sobre precisão máxima
- ✅ Quer builds Docker rápidos

## 🔄 Migrando Entre Versões

### De Completa → Lite

```bash
# Parar versão completa
docker-compose down

# Subir versão lite
docker-compose -f docker-compose-lite.yml up --build
```

### De Lite → Completa

```bash
# Parar versão lite
docker-compose -f docker-compose-lite.yml down

# Subir versão completa
docker-compose up --build
```

## 📝 Notas Importantes

1. **Compatibilidade de API**: Ambas as versões expõem a mesma API REST
2. **Formato de dados**: O schema de resposta é idêntico
3. **Performance**: VADER é ~10x mais rápido que DistilBERT
4. **Acurácia**: Para tweets, VADER tem performance competitiva (~80-85%)

## 🐛 Troubleshooting

### Erro: "Module 'enrichment_lite' not found"

Certifique-se que a variável de ambiente está configurada:
```bash
export USE_LITE_ENRICHMENT=1
```

### Build muito lento

Use a versão lite:
```bash
docker-compose -f docker-compose-lite.yml up --build
```

### Memória insuficiente

A versão lite usa ~70% menos memória que a completa.

## 📚 Referências

- [VADER Sentiment Analysis](https://github.com/cjhutto/vaderSentiment)
- [Paper: VADER - A Parsimonious Rule-based Model for Sentiment Analysis](http://comp.social.gatech.edu/papers/icwsm14.vader.hutto.pdf)

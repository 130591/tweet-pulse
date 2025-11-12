# Guia de Migração - TweetPulse Lite 🔄

Este guia ajuda você a migrar entre as versões completa e lite do TweetPulse.

## 📋 Índice

1. [Migrando de Completa → Lite](#migrando-de-completa--lite)
2. [Migrando de Lite → Completa](#migrando-de-lite--completa)
3. [Compatibilidade de Dados](#compatibilidade-de-dados)
4. [Troubleshooting](#troubleshooting)

---

## Migrando de Completa → Lite

### Motivações Comuns
- ✅ Reduzir uso de recursos (RAM, disco)
- ✅ Acelerar builds e deploys
- ✅ Desenvolvimento local mais rápido
- ✅ CI/CD mais eficiente

### Passo a Passo

#### 1. Parar Versão Atual
```bash
# Se usando Docker Compose
docker-compose down

# Se rodando localmente
# Ctrl+C no terminal onde está rodando
```

#### 2. Instalar Dependências Lite
```bash
# Opção A: Criar novo ambiente virtual (recomendado)
python -m venv venv-lite
source venv-lite/bin/activate  # Linux/Mac
# ou
.\venv-lite\Scripts\activate   # Windows

pip install -r requirements-lite.txt

# Opção B: Atualizar ambiente existente
pip uninstall torch transformers  # Remove pacotes pesados
pip install -r requirements-lite.txt
```

#### 3. Configurar Variável de Ambiente
```bash
# Linux/Mac
export USE_LITE_ENRICHMENT=1

# Windows
set USE_LITE_ENRICHMENT=1

# Ou adicione ao .env
echo "USE_LITE_ENRICHMENT=1" >> .env
```

#### 4. Iniciar Versão Lite

**Docker:**
```bash
docker-compose -f docker-compose-lite.yml up --build
```

**Local:**
```bash
uvicorn tweetpulse.main:app --reload
```

**Script Helper:**
```bash
./scripts/run-lite.sh up
```

#### 5. Verificar Funcionamento
```bash
# Teste a API
curl http://localhost:8000/health

# Verifique os logs
docker-compose -f docker-compose-lite.yml logs -f app
```

### ⚠️ Diferenças Esperadas

| Aspecto | Mudança |
|---------|---------|
| **Modelo de Sentimento** | DistilBERT → VADER |
| **Acurácia** | ~90-95% → ~80-85% |
| **Velocidade** | Moderada → Muito rápida |
| **Memória** | ~2-4GB → ~500MB-1GB |
| **Formato de API** | ✅ Idêntico |
| **Schema de Dados** | ✅ Idêntico |

---

## Migrando de Lite → Completa

### Motivações Comuns
- ✅ Máxima acurácia em produção
- ✅ Análise de textos complexos
- ✅ Recursos de hardware disponíveis
- ✅ GPU disponível para acelerar

### Passo a Passo

#### 1. Parar Versão Lite
```bash
# Docker
docker-compose -f docker-compose-lite.yml down

# Local
# Ctrl+C no terminal
```

#### 2. Instalar Dependências Completas
```bash
# Opção A: Novo ambiente virtual (recomendado)
python -m venv venv-full
source venv-full/bin/activate  # Linux/Mac

pip install -r requirements.txt

# Opção B: Atualizar ambiente existente
pip install -r requirements.txt
```

**Nota:** A instalação do PyTorch pode demorar ~10-15 minutos.

#### 3. Remover Variável de Ambiente
```bash
# Linux/Mac
unset USE_LITE_ENRICHMENT

# Windows
set USE_LITE_ENRICHMENT=

# Ou remova do .env
sed -i '/USE_LITE_ENRICHMENT/d' .env  # Linux/Mac
```

#### 4. Iniciar Versão Completa

**Docker:**
```bash
docker-compose up --build
```

**Local:**
```bash
uvicorn tweetpulse.main:app --reload
```

#### 5. Verificar Funcionamento
```bash
# Teste a API
curl http://localhost:8000/health

# Verifique os logs
docker-compose logs -f app
```

---

## Compatibilidade de Dados

### ✅ Totalmente Compatível

Ambas as versões usam:
- Mesmo schema de banco de dados
- Mesmo formato de API REST
- Mesmos endpoints
- Mesma estrutura de dados

### 🔄 Você Pode Alternar Livremente

```bash
# Dados são preservados ao alternar
docker-compose -f docker-compose-lite.yml down
docker-compose up

# Ou vice-versa
docker-compose down
docker-compose -f docker-compose-lite.yml up
```

### 📊 Diferenças nos Dados

Apenas o campo `sentiment` pode ter pequenas diferenças:

```json
// Versão Lite (VADER)
{
  "sentiment": "positive",
  "confidence": 0.85
}

// Versão Completa (DistilBERT)
{
  "sentiment": "positive",
  "confidence": 0.92
}
```

**Nota:** O formato é idêntico, apenas os valores podem variar ligeiramente.

---

## Troubleshooting

### Erro: "Module 'enrichment_lite' not found"

**Causa:** Variável `USE_LITE_ENRICHMENT` não configurada.

**Solução:**
```bash
export USE_LITE_ENRICHMENT=1  # Linux/Mac
set USE_LITE_ENRICHMENT=1     # Windows
```

### Erro: "No module named 'torch'"

**Causa:** Tentando usar versão completa sem PyTorch instalado.

**Solução:**
```bash
pip install -r requirements.txt
# Ou use a versão lite
pip install -r requirements-lite.txt
```

### Erro: "No module named 'vaderSentiment'"

**Causa:** Tentando usar versão lite sem VADER instalado.

**Solução:**
```bash
pip install -r requirements-lite.txt
```

### Build Docker muito lento

**Causa:** Versão completa baixa ~3GB de dependências.

**Solução:**
```bash
# Use a versão lite
docker-compose -f docker-compose-lite.yml up --build

# Ou use cache do Docker
docker-compose build --parallel
```

### Memória insuficiente

**Causa:** Versão completa requer ~2-4GB RAM.

**Solução:**
```bash
# Migre para versão lite
./scripts/run-lite.sh up

# Ou aumente memória do Docker Desktop
# Settings → Resources → Memory → 4GB+
```

### Resultados de sentimento diferentes

**Causa:** Modelos diferentes (VADER vs DistilBERT).

**Solução:** Isso é esperado. Escolha baseado em suas necessidades:
- **Lite:** Rápido, otimizado para redes sociais
- **Completa:** Mais preciso, melhor para textos complexos

---

## Comparação Rápida

| Característica | Lite | Completa |
|----------------|------|----------|
| Instalação | 2-3 min | 10-15 min |
| Tamanho | 500 MB | 3.5 GB |
| RAM | 500 MB - 1 GB | 2-4 GB |
| Velocidade | Muito rápida | Moderada |
| Acurácia | 80-85% | 90-95% |
| GPU | Não precisa | Opcional |
| Ideal para | Dev, CI/CD | Produção |

---

## Dicas Pro

### Para Desenvolvimento
```bash
# Use lite para desenvolvimento rápido
./scripts/run-lite.sh up
```

### Para Produção
```bash
# Use completa se tiver recursos
docker-compose up --build

# Ou lite se recursos limitados
docker-compose -f docker-compose-lite.yml up --build
```

### Para CI/CD
```yaml
# Use lite para testes rápidos
- name: Run tests
  run: |
    pip install -r requirements-lite.txt
    pytest
```

### Para Comparar
```bash
# Execute o script de comparação
python examples/compare_versions.py
```

---

## Suporte

- 📚 [Documentação Lite](LITE_VERSION.md)
- 🚀 [Quick Start](../QUICKSTART.md)
- 🐛 [Issues](https://github.com/130591/tweetpulse/issues)

---

**Última atualização:** 2024-11-03

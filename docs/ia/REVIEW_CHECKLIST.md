# ✅ Checklist de Code Review - Testes Focados em Comportamento

Use este checklist ao revisar pull requests com testes novos ou modificados.

## 🎯 Checklist Rápido

Para cada teste, pergunte:

### ✅ Teste de COMPORTAMENTO (Aprovar)

- [ ] **Nome descreve comportamento?**  
  ✅ `test_storage_persists_tweets_to_file()`  
  ❌ `test_storage_buffer_append()`

- [ ] **Usa apenas APIs públicas?**  
  ✅ `storage.store(tweet)` e `storage.get(id)`  
  ❌ `storage._buffer.append(tweet)`

- [ ] **Verifica saídas observáveis?**  
  ✅ `assert file_exists(path)`  
  ❌ `assert len(storage._queue) == 1`

- [ ] **Sobrevive a refatoração?**  
  ✅ Se mudar de list para deque, teste ainda passa?  
  ❌ Teste quebra se renomear variável interna?

- [ ] **Testa requisito de negócio?**  
  ✅ "Sistema deve armazenar tweets sem duplicatas"  
  ❌ "Buffer interno usa deque com maxlen=1000"

### ❌ Teste de IMPLEMENTAÇÃO (Solicitar Mudança)

- [ ] **Acessa atributos privados?**  
  ❌ `assert len(obj._buffer) == 1`  
  ❌ `assert isinstance(obj._queue, deque)`

- [ ] **Verifica ordem de chamadas internas?**  
  ❌ `mock.method1.assert_called_before(mock.method2)`  
  ❌ `assert call_count == 1`

- [ ] **Testa estruturas de dados internas?**  
  ❌ `assert obj._cache == {'key': 'value'}`  
  ❌ `assert obj._pending_items.qsize() == 5`

- [ ] **Mock de métodos privados?**  
  ❌ `with patch.object(obj, '_internal_method')`  
  ❌ `obj._process.assert_called_once()`

## 📋 Checklist Detalhado

### 1. Nome do Teste

**Pergunta**: O nome descreve O QUE o sistema faz?

```python
# ❌ RUIM: Foca na implementação
def test_deduplicator_uses_bloom_filter()
def test_storage_buffer_is_list()
def test_pipeline_calls_enricher_first()

# ✅ BOM: Descreve comportamento
def test_deduplicator_identifies_duplicate_tweets()
def test_storage_persists_all_tweets()
def test_pipeline_processes_unique_tweets_only()
```

**Ação**: Se nome menciona detalhe de implementação, pedir refatoração.

---

### 2. Arrange (Setup)

**Pergunta**: Setup usa APIs públicas ou acessa internals?

```python
# ❌ RUIM: Manipula estado interno
def test_something():
    storage = Storage()
    storage._buffer = [tweet1, tweet2]  # ❌ Manipulação interna
    storage._initialized = True         # ❌ Flag privada

# ✅ BOM: Usa API pública
def test_something():
    storage = Storage()
    await storage.store(tweet1)  # ✅ API pública
    await storage.store(tweet2)  # ✅ API pública
```

**Ação**: Se setup manipula `._atributos`, sugerir usar métodos públicos.

---

### 3. Act (Execução)

**Pergunta**: Executa comportamento público do sistema?

```python
# ❌ RUIM: Chama método privado
def test_something():
    result = storage._flush_buffer()  # ❌ Método privado

# ✅ BOM: Chama método público
def test_something():
    result = await storage.flush()  # ✅ Método público
```

**Ação**: Se chama métodos privados (`_nome`), pedir para testar via API pública.

---

### 4. Assert (Verificação)

**Pergunta**: Verifica comportamento observável ou estado interno?

```python
# ❌ RUIM: Verifica estado interno
def test_something():
    await storage.store(tweet)
    assert len(storage._buffer) == 1              # ❌ Atributo privado
    assert storage._last_flush_time is not None   # ❌ Estado interno
    assert isinstance(storage._queue, deque)      # ❌ Tipo interno

# ✅ BOM: Verifica comportamento observável
def test_something():
    await storage.store(tweet)
    
    # ✅ Verifica efeito observável
    retrieved = await storage.get(tweet['id'])
    assert retrieved is not None
    assert retrieved['id'] == tweet['id']
    
    # ✅ Verifica arquivo criado
    files = list(staging_dir.glob("*.parquet"))
    assert len(files) > 0
```

**Ação**: Se assert verifica `._atributos`, pedir verificação de comportamento observável.

---

### 5. Mocks

**Pergunta**: Mock é de dependência externa ou componente interno?

```python
# ❌ RUIM: Mock de componente interno do sistema
@patch.object(pipeline, 'enricher')  # ❌ Componente nosso
@patch.object(storage, '_buffer')    # ❌ Estrutura interna
def test_something(mock_enricher, mock_buffer):
    await pipeline.process(tweet)
    mock_enricher.enrich.assert_called()  # ❌ Verifica chamada interna

# ✅ BOM: Mock apenas dependências externas
@patch('transformers.pipeline')           # ✅ Lib externa
@patch('tweepy.StreamingClient')         # ✅ API externa
def test_something(mock_model, mock_twitter):
    await pipeline.process(tweet)
    
    # ✅ Verifica resultado, não chamadas
    result = await storage.get(tweet['id'])
    assert 'sentiment' in result
```

**Ação**: Se mocka componentes internos do sistema, pedir para usar componentes reais ou verificar apenas resultado.

---

### 6. Acoplamento

**Pergunta**: Teste quebraria com refatoração que não muda comportamento?

**Teste Mental**: Imagine estas mudanças:

- ✅ Mudar de `list` para `deque`: Teste deve PASSAR
- ✅ Renomear `_buffer` para `_staging_queue`: Teste deve PASSAR
- ✅ Mudar ordem de operações internas: Teste deve PASSAR
- ✅ Adicionar cache interno: Teste deve PASSAR
- ✅ Processar em paralelo vs sequencial: Teste deve PASSAR

```python
# ❌ RUIM: Quebra com mudanças internas
def test_something():
    storage = Storage()
    storage._buffer.append(tweet)  # ❌ Quebra se renomear _buffer
    assert isinstance(storage._buffer, list)  # ❌ Quebra se mudar para deque

# ✅ BOM: Sobrevive a mudanças internas
def test_something():
    storage = Storage()
    await storage.store(tweet)  # ✅ API pública
    
    files = list(staging_dir.glob("*.parquet"))
    assert len(files) > 0  # ✅ Verifica efeito observável
```

**Ação**: Se teste quebra com refatorações seguras, pedir refatoração.

---

## 🚨 Red Flags Comuns

### 🔴 Alto Risco (Solicitar Mudança Obrigatória)

1. **Acessa `._atributos` privados**
   ```python
   assert obj._internal_state == expected  # ❌ BLOQUEAR
   ```

2. **Testa tipo interno**
   ```python
   assert isinstance(obj._queue, deque)  # ❌ BLOQUEAR
   ```

3. **Verifica ordem de chamadas internas**
   ```python
   assert mock1.called_before(mock2)  # ❌ BLOQUEAR
   ```

### 🟡 Médio Risco (Sugerir Melhoria)

1. **Nome genérico**
   ```python
   def test_storage()  # 🟡 Melhorar nome
   ```

2. **Muitos mocks internos**
   ```python
   # 🟡 Reduzir mocks, usar componentes reais
   @patch.object(pipeline, 'enricher')
   @patch.object(pipeline, 'storage')
   @patch.object(pipeline, 'deduplicator')
   ```

3. **Assert com `call_count` específico**
   ```python
   assert mock.call_count == 3  # 🟡 Verificar resultado ao invés
   ```

### 🟢 Baixo Risco (Opcional)

1. **Comentários explicando "como"**
   ```python
   # 🟢 OK, mas pode simplificar
   # First we add to buffer, then we flush
   await storage.store(tweet)
   ```

---

## 💬 Comentários de Review Sugeridos

### Para Acesso a Atributos Privados

```markdown
❌ Este teste acessa `storage._buffer` que é um detalhe de implementação.

**Sugestão**: Verifique o comportamento observável:
- Arquivo parquet foi criado?
- Tweet pode ser recuperado via `storage.get(id)`?
- Stats mostram contagem correta?

**Exemplo**:
```python
# Ao invés de:
assert len(storage._buffer) == 1

# Faça:
await storage.flush()
files = list(staging_dir.glob("*.parquet"))
assert len(files) > 0
```

---

### Para Verificação de Mocks Internos

```markdown
❌ Este teste verifica que `enricher.enrich()` foi chamado, o que é um detalhe de implementação.

**Sugestão**: Verifique que o tweet foi realmente enriquecido:

```python
# Ao invés de:
pipeline.enricher.enrich.assert_called_once()

# Faça:
result = await storage.get(tweet['id'])
assert 'sentiment' in result
assert result['sentiment'] in ['positive', 'negative', 'neutral']
```

---

### Para Nome Ruim

```markdown
🟡 O nome `test_storage_buffer()` descreve implementação, não comportamento.

**Sugestão**: Descreva O QUE o teste verifica:
- `test_storage_persists_tweets_to_parquet_file()`
- `test_storage_retrieves_previously_stored_tweets()`
- `test_storage_handles_concurrent_writes_safely()`
```

---

## ✅ Exemplos de Bons Testes

### Storage
```python
@pytest.mark.asyncio
async def test_storage_persists_tweets_and_allows_retrieval():
    """✅ Comportamento: armazenar e recuperar tweets."""
    storage = Storage(redis=redis, staging_dir=dir)
    tweet = {"id": "123", "text": "test"}
    
    await storage.store(tweet)
    retrieved = await storage.get(tweet['id'])
    
    assert retrieved is not None
    assert retrieved['id'] == "123"
```

### Pipeline
```python
@pytest.mark.asyncio
async def test_pipeline_processes_unique_tweets_only():
    """✅ Comportamento: ignorar duplicatas."""
    pipeline = Pipeline(...)
    tweet = {"id": "123", "text": "test"}
    
    # Processar mesmo tweet duas vezes
    result1 = await pipeline.process(tweet)
    result2 = await pipeline.process(tweet)
    
    # Apenas um deve ser armazenado
    all_tweets = await storage.get_all()
    assert len(all_tweets) == 1
```

### Enrichment
```python
@pytest.mark.asyncio
async def test_enricher_adds_sentiment_to_tweets():
    """✅ Comportamento: adicionar análise de sentimento."""
    enricher = TweetEnricher()
    tweet = {"id": "123", "text": "I love this!"}
    
    enriched = await enricher.enrich(tweet)
    
    assert 'sentiment' in enriched
    assert enriched['sentiment'] in ['positive', 'negative', 'neutral']
```

---

## 📊 Métricas de Qualidade

Ao final do review, avalie:

| Métrica | Meta | Como Medir |
|---------|------|------------|
| **Acesso a privados** | 0% | Grep por `\._[a-z]` em asserts |
| **Mocks internos** | < 10% | Count de `@patch.object(nosso_componente)` |
| **Testes com "implementation" no nome** | 0% | Grep por `test_.*implementation` |
| **Sobrevivência a refatoração** | 100% | Fazer refatoração segura e ver se passa |

---

## 🎓 Resumo

**Pergunta Fundamental**: 

> Se refatorarmos o código sem mudar o comportamento,  
> este teste ainda deve passar?

- ✅ **SIM** → Teste de comportamento (Aprovar)
- ❌ **NÃO** → Teste de implementação (Solicitar mudança)

**Lembre-se**: Bons testes documentam O QUE o sistema faz, não COMO ele faz!

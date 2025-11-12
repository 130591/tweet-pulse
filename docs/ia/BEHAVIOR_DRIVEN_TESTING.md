# 🎯 Guia de Testes Focados em Comportamento

## Princípio Fundamental

> **Teste o QUE o código faz, não COMO ele faz.**

Testes de comportamento (behavior-driven) focam em:
- ✅ **Entradas e saídas observáveis**
- ✅ **Contratos públicos**
- ✅ **Efeitos colaterais mensuráveis**
- ✅ **Requisitos de negócio**

Testes de implementação (implementation-driven) focam em:
- ❌ **Detalhes internos**
- ❌ **Estruturas de dados privadas**
- ❌ **Ordem de chamadas de métodos**
- ❌ **Como o código funciona por dentro**

## Por Que Focar em Comportamento?

### ✅ Vantagens

1. **Refatoração Segura**: Mudanças internas não quebram testes
2. **Testes Mais Duráveis**: Sobrevivem a mudanças de implementação
3. **Melhor Documentação**: Descrevem o que o sistema faz
4. **Menos Frágeis**: Não dependem de detalhes internos
5. **Foco em Valor**: Testam funcionalidades reais

### ❌ Problemas de Testar Implementação

1. **Testes Frágeis**: Qualquer mudança interna quebra testes
2. **Refatoração Difícil**: Medo de mudar código
3. **Falsa Segurança**: Testes passam mas sistema não funciona
4. **Acoplamento**: Testes acoplados à implementação
5. **Manutenção Cara**: Muitos testes precisam mudar juntos

## Exemplos Práticos

### ❌ RUIM: Testando Implementação

```python
@pytest.mark.asyncio
async def test_storage_buffer_management(storage):
    """Testa detalhes internos do buffer."""
    # RUIM: Testando estrutura interna
    await storage.store(tweet)
    
    # ❌ Verificando estado interno
    assert len(storage.staging_buffer) == 1
    assert storage.staging_buffer[0]['id'] == tweet['id']
    
    # ❌ Testando método privado
    assert storage._should_flush() == False
```

**Problemas:**
- Depende de `staging_buffer` (detalhe de implementação)
- Se mudarmos para usar lista ou deque, teste quebra
- Testa método privado `_should_flush`
- Não testa o comportamento real do sistema

### ✅ BOM: Testando Comportamento

```python
@pytest.mark.asyncio
async def test_storage_persists_tweets(storage, staging_dir):
    """Testa que tweets são persistidos corretamente."""
    # BOM: Testando comportamento observável
    await storage.store(tweet)
    await storage.flush()
    
    # ✅ Verificando efeito colateral observável
    files = list(staging_dir.glob("*.parquet"))
    assert len(files) > 0
    
    # ✅ Verificando conteúdo do arquivo
    data = read_parquet(files[0])
    assert data['id'][0] == tweet['id']
```

**Vantagens:**
- Testa o que importa: tweet foi salvo?
- Pode mudar implementação interna (buffer, deque, etc.)
- Verifica arquivo criado (efeito colateral real)
- Testa contrato público

## Padrões Anti-Pattern

### ❌ Anti-Pattern 1: Verificar Mocks Internos

```python
# RUIM
@pytest.mark.asyncio
async def test_pipeline_calls_enricher(pipeline):
    await pipeline.process(tweet)
    
    # ❌ Verificando chamada interna
    pipeline.enricher.enrich.assert_called_once()
    # ❌ Verificando argumentos exatos
    pipeline.enricher.enrich.assert_called_with(tweet)
```

**Por que é ruim:**
- Se renomear `enricher`, teste quebra
- Se mudar ordem de chamadas, teste quebra
- Não verifica se tweet foi realmente enriquecido

### ✅ Solução: Verificar Resultado

```python
# BOM
@pytest.mark.asyncio
async def test_pipeline_enriches_tweets(pipeline, storage):
    await pipeline.process(tweet)
    
    # ✅ Verificando resultado observável
    stored = await storage.get(tweet['id'])
    
    # ✅ Verificando que tweet tem campos enriquecidos
    assert 'sentiment' in stored
    assert 'language' in stored
    assert stored['sentiment'] in ['positive', 'negative', 'neutral']
```

### ❌ Anti-Pattern 2: Testar Estruturas Internas

```python
# RUIM
def test_consumer_message_queue(consumer):
    consumer.add_message(msg1)
    consumer.add_message(msg2)
    
    # ❌ Testando deque interno
    assert isinstance(consumer._queue, deque)
    assert len(consumer._queue) == 2
    assert consumer._queue[0] == msg1
```

**Por que é ruim:**
- Depende de implementação com `deque`
- Se mudar para `queue.Queue`, teste quebra
- Não testa comportamento real

### ✅ Solução: Testar Processamento

```python
# BOM
@pytest.mark.asyncio
async def test_consumer_processes_messages_in_order(consumer):
    processed = []
    
    async def track_processing(msg):
        processed.append(msg['id'])
    
    consumer.processor = track_processing
    await consumer.add_message(msg1)
    await consumer.add_message(msg2)
    await consumer.process_all()
    
    # ✅ Verificando comportamento: ordem de processamento
    assert processed == [msg1['id'], msg2['id']]
```

### ❌ Anti-Pattern 3: Verificar Ordem de Chamadas

```python
# RUIM
@pytest.mark.asyncio
async def test_pipeline_order(pipeline, mock_dedup, mock_enrich, mock_store):
    await pipeline.process(tweet)
    
    # ❌ Verificando ordem exata de chamadas
    assert mock_dedup.call_count == 1
    assert mock_enrich.call_count == 1
    assert mock_store.call_count == 1
    
    # ❌ Verificando que dedup foi antes de enrich
    assert mock_dedup.call_args < mock_enrich.call_args
```

**Por que é ruim:**
- Acoplado à ordem de execução interna
- Pode processar em paralelo no futuro
- Não verifica se pipeline funciona

### ✅ Solução: Testar Resultado Final

```python
# BOM
@pytest.mark.asyncio
async def test_pipeline_stores_enriched_unique_tweets(pipeline, storage):
    # Processar mesmo tweet duas vezes
    await pipeline.process(tweet)
    await pipeline.process(tweet)  # Duplicata
    
    # ✅ Verificar resultado: apenas 1 tweet armazenado
    all_tweets = await storage.get_all()
    assert len(all_tweets) == 1
    
    # ✅ Verificar que está enriquecido
    stored = all_tweets[0]
    assert 'sentiment' in stored
    assert stored['id'] == tweet['id']
```

## Checklist: Meu Teste é Focado em Comportamento?

Faça estas perguntas:

### ✅ Sinais de Bom Teste (Comportamento)

- [ ] Testa entrada → saída observável?
- [ ] Usa apenas APIs públicas?
- [ ] Verifica efeitos colaterais mensuráveis (arquivos, DB, cache)?
- [ ] Sobreviveria a refatoração interna?
- [ ] Descreve um requisito de negócio?
- [ ] Nome do teste descreve COMPORTAMENTO esperado?

### ❌ Sinais de Teste Ruim (Implementação)

- [ ] Acessa atributos privados (`._buffer`, `._queue`)?
- [ ] Verifica ordem exata de chamadas internas?
- [ ] Mock de métodos privados?
- [ ] Testa estruturas de dados internas?
- [ ] Verifica `assert_called_once()` em métodos internos?
- [ ] Quebraria se renomear variável interna?

## Guia de Refatoração

### Como Migrar de Implementação → Comportamento

1. **Identifique o Comportamento Real**
   ```
   Pergunta: "O que o usuário espera que aconteça?"
   Não: "storage.buffer tem 3 items"
   Sim: "3 tweets estão persistidos no arquivo"
   ```

2. **Remova Verificações de Mock Internos**
   ```python
   # Antes
   assert pipeline.enricher.enrich.called
   
   # Depois
   stored = await storage.get(tweet_id)
   assert 'sentiment' in stored
   ```

3. **Use Efeitos Observáveis**
   ```python
   # Antes
   assert len(storage._buffer) == 5
   
   # Depois
   files = list(staging_dir.glob("*.parquet"))
   assert len(files) > 0
   ```

4. **Teste Contratos, Não Detalhes**
   ```python
   # Antes
   assert isinstance(consumer._queue, deque)
   
   # Depois
   await consumer.process_all()
   assert len(processed_messages) == expected_count
   ```

## Exemplos por Componente

### Storage

```python
# ❌ RUIM: Implementação
async def test_storage_buffer_size():
    await storage.store(tweet)
    assert len(storage._buffer) == 1  # Detalhe interno

# ✅ BOM: Comportamento
async def test_storage_retrieves_stored_tweet():
    await storage.store(tweet)
    retrieved = await storage.get(tweet['id'])
    assert retrieved['id'] == tweet['id']
```

### Enrichment

```python
# ❌ RUIM: Implementação
async def test_enricher_calls_model():
    await enricher.enrich(tweet)
    enricher._model.assert_called_once()  # Mock interno

# ✅ BOM: Comportamento
async def test_enricher_adds_sentiment():
    enriched = await enricher.enrich(tweet)
    assert 'sentiment' in enriched
    assert enriched['sentiment'] in ['positive', 'negative', 'neutral']
```

### Pipeline

```python
# ❌ RUIM: Implementação
async def test_pipeline_component_calls():
    await pipeline.process(tweet)
    assert pipeline.dedup.check.call_count == 1  # Ordem interna
    assert pipeline.enrich.process.call_count == 1

# ✅ BOM: Comportamento
async def test_pipeline_processes_and_stores_tweet():
    await pipeline.process(tweet)
    stored = await storage.get(tweet['id'])
    assert stored is not None
    assert 'sentiment' in stored  # Foi enriquecido
```

## Quando Usar Mocks

### ✅ Use Mocks Para

1. **Dependências Externas**
   ```python
   # BOM: Mock de API externa
   with patch('requests.get') as mock_api:
       mock_api.return_value.json.return_value = {'data': 'test'}
       result = await service.fetch_data()
   ```

2. **Serviços Caros**
   ```python
   # BOM: Mock de ML model
   with patch('transformers.pipeline') as mock_model:
       mock_model.return_value = lambda x: [{'score': 0.9}]
       enriched = await enricher.process(tweet)
   ```

3. **Efeitos Colaterais Indesejados**
   ```python
   # BOM: Mock de email sender
   with patch('smtplib.SMTP') as mock_smtp:
       await notifier.send_alert(message)
   ```

### ❌ NÃO Use Mocks Para

1. **Componentes Internos do Sistema**
   ```python
   # RUIM: Mock de componente próprio
   with patch.object(pipeline, 'enricher'):  # Nosso código!
       await pipeline.process(tweet)
   ```

2. **Verificar Ordem de Chamadas**
   ```python
   # RUIM: Verificando ordem interna
   mock.method1.assert_called()
   mock.method2.assert_called()
   assert mock.method1.call_time < mock.method2.call_time
   ```

3. **Estruturas de Dados Simples**
   ```python
   # RUIM: Mock de lista ou dict
   with patch.object(storage, '_buffer', MagicMock()):
       # Apenas use lista/dict real!
   ```

## Naming Conventions

### ❌ Nomes Ruins (Focam em Implementação)

```python
def test_storage_buffer_append()
def test_enricher_calls_model()
def test_pipeline_component_order()
def test_consumer_queue_size()
```

### ✅ Nomes Bons (Focam em Comportamento)

```python
def test_storage_persists_tweets_to_file()
def test_enricher_adds_sentiment_to_tweets()
def test_pipeline_processes_unique_tweets_only()
def test_consumer_processes_messages_in_order()
```

## Resumo

| Aspecto | ❌ Implementação | ✅ Comportamento |
|---------|-----------------|------------------|
| **Foco** | Como funciona | O que faz |
| **Verificação** | Mocks internos | Saídas observáveis |
| **Acoplamento** | Alto | Baixo |
| **Refatoração** | Quebra testes | Testes passam |
| **Documentação** | Detalhes técnicos | Requisitos |
| **Manutenção** | Cara | Barata |

## Regra de Ouro

> **Se você pode refatorar a implementação sem mudar o comportamento,
> seus testes NÃO devem quebrar.**

---

**Lembre-se**: Testes de comportamento = código mais flexível! 🎯

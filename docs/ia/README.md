# Testes de Integração - Tweet Pulse

## 📋 Visão Geral

Testes de integração **determinísticos e não-flaky** para o módulo de ingestão do Tweet Pulse.

## 🎯 Princípios dos Testes

### 1. **Foco em Comportamento** ⭐ **PRINCIPAL**
- ✅ Testamos o **QUE** o código faz, não **COMO** faz
- ✅ Verificamos entradas → saídas observáveis
- ✅ Testamos contratos públicos, não implementação interna
- ✅ Testes sobrevivem a refatorações
- 📖 **Ver**: [Guia de Testes Focados em Comportamento](../BEHAVIOR_DRIVEN_TESTING.md)

### 2. **Determinismo**
- ✅ Sem dependências externas (Twitter API, banco de dados real)
- ✅ Uso de mocks e fixtures controlados
- ✅ Timestamps fixos com `deterministic_time` fixture
- ✅ Sem race conditions em testes assíncronos
- ✅ Ordem de execução não importa

### 3. **Isolamento**
- ✅ Cada teste é independente
- ✅ Setup/teardown automático com fixtures
- ✅ Redis fake (fakeredis) resetado entre testes
- ✅ Banco de dados em memória (SQLite)
- ✅ Diretórios temporários limpos

### 4. **Velocidade**
- ✅ Todos os testes rodam em < 5 segundos
- ✅ Sem esperas arbitrárias (sleep mínimo)
- ✅ Mocks ao invés de serviços reais
- ✅ Processamento paralelo quando possível

### 5. **Cobertura Completa**
- ✅ Happy path (fluxo normal)
- ✅ Edge cases (casos extremos)
- ✅ Error handling (tratamento de erros)
- ✅ Concurrent scenarios (cenários concorrentes)

## 🚀 Como Executar

### Executar Todos os Testes
```bash
# Todos os testes de integração
pytest tests/test_integration/ -v

# Com cobertura
pytest tests/test_integration/ --cov=tweetpulse.ingestion --cov-report=html

# Paralelo (mais rápido)
pytest tests/test_integration/ -n auto
```

### Executar Testes Específicos
```bash
# Por arquivo
pytest tests/test_integration/test_storage_integration.py -v

# Por classe
pytest tests/test_integration/test_storage_integration.py::TestStorageIntegration -v

# Por teste específico
pytest tests/test_integration/test_storage_integration.py::TestStorageIntegration::test_store_tweet_to_cache -v

# Por padrão de nome
pytest tests/test_integration/ -k "storage" -v
```

### Executar com Diferentes Níveis de Verbosidade
```bash
# Resumido
pytest tests/test_integration/ -q

# Verbose
pytest tests/test_integration/ -v

# Muito verbose (com prints)
pytest tests/test_integration/ -vv -s
```

### Executar com Markers
```bash
# Apenas testes async
pytest tests/test_integration/ -m asyncio

# Apenas testes lentos
pytest tests/test_integration/ -m slow

# Excluir testes lentos
pytest tests/test_integration/ -m "not slow"
```

## 📦 Dependências

```bash
# Instalar dependências de teste
pip install -r requirements-test.txt
```

**requirements-test.txt:**
```
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-timeout>=2.1.0
fakeredis[aioredis]>=2.19.0
```

## 📁 Estrutura de Arquivos

```
tests/test_integration/
├── __init__.py                           # Inicialização do módulo
├── conftest.py                           # Fixtures compartilhadas
├── README.md                             # Esta documentação
├── test_storage_integration.py           # Testes do Storage
├── test_enrichment_integration.py        # Testes do Enrichment
├── test_deduplication_integration.py     # Testes do Deduplication
├── test_pipeline_integration.py          # Testes do Pipeline completo
├── test_consumer_integration.py          # Testes do Consumer
└── test_batch_writer_integration.py      # Testes do BatchWriter
```

## 🔧 Fixtures Disponíveis

### Fixtures de Configuração
- **`test_settings`**: Configurações de teste determinísticas
- **`fake_redis`**: Instância de Redis fake
- **`clean_redis`**: Redis limpo antes/depois do teste
- **`in_memory_db`**: Banco SQLite em memória
- **`staging_dir`**: Diretório temporário para staging

### Fixtures de Dados
- **`sample_tweet_data`**: Tweet de exemplo
- **`sample_tweets_batch`**: Lote de 10 tweets
- **`enriched_tweet_data`**: Tweet enriquecido

### Fixtures de Mocks
- **`mock_twitter_client`**: Cliente Twitter mockado
- **`mock_sentiment_model`**: Modelo de sentimento mockado
- **`mock_langdetect`**: Detecção de idioma mockada
- **`deterministic_time`**: Timestamp fixo

## ✅ Boas Práticas Implementadas

### 1. Testes Assíncronos Determinísticos
```python
@pytest.mark.asyncio
async def test_async_operation(clean_redis):
    # Use asyncio.gather para operações paralelas
    results = await asyncio.gather(*[
        operation(i) for i in range(10)
    ])
    
    # Verifique resultados de forma determinística
    assert len(results) == 10
```

### 2. Mocks Controlados
```python
with patch('module.function') as mock_func:
    # Comportamento determinístico
    mock_func.return_value = "fixed_value"
    
    # Teste
    result = await my_function()
    
    # Verificação
    assert result == "expected"
    mock_func.assert_called_once()
```

### 3. Timestamps Fixos
```python
def test_with_fixed_time(deterministic_time):
    # deterministic_time sempre retorna 2024-01-15 10:30:00
    result = function_using_datetime()
    
    assert result['timestamp'] == "2024-01-15T10:30:00"
```

### 4. Limpeza Automática
```python
@pytest.fixture
async def clean_resource():
    resource = setup_resource()
    yield resource
    await resource.cleanup()  # Sempre executa
```

### 5. Testes de Concorrência
```python
async def test_concurrent_operations():
    # Operações concorrentes com locks para evitar race conditions
    results = await asyncio.gather(*[
        thread_safe_operation(i)
        for i in range(100)
    ])
    
    # Resultado deve ser determinístico
    assert sorted(results) == list(range(100))
```

## 🐛 Debug de Testes

### Executar com Debug
```bash
# Com pdb (debugger Python)
pytest tests/test_integration/ --pdb

# Parar no primeiro erro
pytest tests/test_integration/ -x

# Ver logs completos
pytest tests/test_integration/ -vv -s --log-cli-level=DEBUG
```

### Executar Teste Específico com Prints
```bash
pytest tests/test_integration/test_storage_integration.py::TestStorageIntegration::test_store_tweet_to_cache -vv -s
```

## 📊 Análise de Cobertura

```bash
# Gerar relatório de cobertura HTML
pytest tests/test_integration/ \
    --cov=tweetpulse.ingestion \
    --cov-report=html \
    --cov-report=term-missing

# Abrir relatório
open htmlcov/index.html
```

## 🔍 Anti-Padrões Evitados

❌ **Evitado:**
- `time.sleep()` arbitrário (flaky)
- Dependências de serviços externos (não-determinístico)
- Ordem de execução importante (frágil)
- Compartilhamento de estado entre testes (race conditions)
- Timestamps reais (não-determinístico)
- Números aleatórios sem seed (não-reproduzível)

✅ **Usado:**
- `asyncio.sleep()` mínimo necessário
- Mocks e fakes determinísticos
- Testes independentes
- Fixtures com cleanup
- Timestamps fixos
- Dados controlados

## 🎓 Referências

- [Pytest Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [Testing Async Code](https://pytest-asyncio.readthedocs.io/)
- [Deterministic Testing](https://martinfowler.com/articles/nonDeterminism.html)
- [Test Doubles](https://martinfowler.com/bliki/TestDouble.html)

## 📈 Métricas de Qualidade

| Métrica | Alvo | Atual |
|---------|------|-------|
| Cobertura | >80% | TBD |
| Tempo Total | <10s | TBD |
| Taxa de Sucesso | 100% | TBD |
| Flakiness | 0% | 0% |

## 🤝 Contribuindo

Ao adicionar novos testes:

1. ✅ Use fixtures existentes quando possível
2. ✅ Mantenha testes independentes
3. ✅ Use mocks para dependências externas
4. ✅ Adicione docstrings descritivas
5. ✅ Garanta determinismo (sem aleatoriedade)
6. ✅ Execute toda a suite antes de commit

```bash
# Verificar antes de commit
pytest tests/test_integration/ -v --tb=short
```

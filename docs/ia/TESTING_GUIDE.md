# 🧪 Guia de Testes - Tweet Pulse

## ⭐ Princípio Fundamental

> **Teste o COMPORTAMENTO, não a IMPLEMENTAÇÃO.**

Nossos testes focam em **O QUE** o código faz, não em **COMO** ele faz:
- ✅ Entradas → Saídas observáveis
- ✅ Contratos públicos
- ✅ Efeitos colaterais mensuráveis
- ❌ Detalhes internos de implementação

📖 **Leia**: [Guia Completo de Testes Focados em Comportamento](tests/BEHAVIOR_DRIVEN_TESTING.md)

## 🚀 Quick Start

### 1. Instalar Dependências
```bash
# Opção 1: Via Make
make install-dev

# Opção 2: Via pip
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 2. Executar Testes
```bash
# Opção 1: Via Make (recomendado)
make test

# Opção 2: Via script
./scripts/run_tests.sh -v

# Opção 3: Via pytest direto
pytest tests/test_integration/ -v
```

### 3. Ver Cobertura
```bash
make test-cov
# Abre: htmlcov/index.html
```

## 📚 Comandos Úteis

### Execução Básica
```bash
# Todos os testes
make test

# Testes em paralelo (mais rápido)
make test-fast

# Com saída verbose
make test-verbose

# Com cobertura
make test-cov
```

### Testes Específicos
```bash
# Por componente
make test-storage
make test-enrichment
make test-deduplication
make test-pipeline
make test-consumer
make test-batch-writer

# Por padrão de nome
pytest tests/test_integration/ -k "storage" -v
pytest tests/test_integration/ -k "concurrent" -v

# Teste específico
pytest tests/test_integration/test_storage_integration.py::TestStorageIntegration::test_store_tweet_to_cache -vv
```

### Debug
```bash
# Com debugger (para no erro)
make test-debug

# Para no primeiro erro
make test-failfast

# Re-executar apenas testes que falharam
make test-last-failed

# Ver logs completos
pytest tests/test_integration/ -vv -s --log-cli-level=DEBUG
```

## 🎯 Exemplos de Uso

### Exemplo 1: Testar Após Mudança no Storage
```bash
# 1. Executar testes do storage
make test-storage

# 2. Se passou, executar todos os testes relacionados
pytest tests/test_integration/ -k "storage or pipeline" -v

# 3. Verificar cobertura
make test-cov
```

### Exemplo 2: Debug de Teste Falhando
```bash
# 1. Executar teste específico com verbose
pytest tests/test_integration/test_storage_integration.py::TestStorageIntegration::test_store_tweet_to_cache -vv -s

# 2. Se ainda falha, usar debugger
pytest tests/test_integration/test_storage_integration.py::TestStorageIntegration::test_store_tweet_to_cache --pdb

# 3. Ver logs detalhados
pytest tests/test_integration/test_storage_integration.py::TestStorageIntegration::test_store_tweet_to_cache -vv -s --log-cli-level=DEBUG
```

### Exemplo 3: Desenvolvimento com Watch Mode
```bash
# Instalar pytest-watch
pip install pytest-watch

# Executar testes continuamente
make test-watch

# Ou manualmente
ptw tests/test_integration/ -- -v
```

### Exemplo 4: CI Local
```bash
# Executar mesma pipeline do CI
make ci

# Isso executa:
# 1. Limpeza
# 2. Instalação de dependências
# 3. Lint
# 4. Format check
# 5. Type check
# 6. Testes com cobertura
```

## 🔍 Estrutura dos Testes

### Anatomia de um Teste
```python
@pytest.mark.asyncio
async def test_storage_operation(
    clean_redis,           # Fixture: Redis limpo
    staging_dir,          # Fixture: Diretório temporário
    sample_tweet_data     # Fixture: Dados de exemplo
):
    """Test description explaining what is being tested."""
    # Arrange: Setup
    storage = Storage(redis=clean_redis, staging_dir=staging_dir)
    
    # Act: Execute operation
    await storage.store(sample_tweet_data)
    
    # Assert: Verify results
    cached = await storage.get_from_cache(sample_tweet_data['id'])
    assert cached is not None
    assert cached['id'] == sample_tweet_data['id']
```

### Fixtures Disponíveis

```python
# Configuração
test_settings           # Configurações de teste
fake_redis             # Redis fake
clean_redis            # Redis limpo (recomendado)
in_memory_db           # SQLite em memória
staging_dir            # Diretório temporário

# Dados
sample_tweet_data      # Um tweet
sample_tweets_batch    # 10 tweets
enriched_tweet_data    # Tweet enriquecido

# Mocks
mock_twitter_client    # Cliente Twitter mockado
mock_sentiment_model   # Modelo de sentimento mockado
mock_langdetect        # Detecção de idioma mockada
deterministic_time     # Timestamp fixo
```

## 📊 Interpretando Resultados

### Saída de Sucesso
```
tests/test_integration/test_storage_integration.py::TestStorageIntegration::test_store_tweet_to_cache PASSED [100%]

======================== 1 passed in 0.23s ========================
```

### Saída de Falha
```
tests/test_integration/test_storage_integration.py::TestStorageIntegration::test_store_tweet_to_cache FAILED [100%]

________________________ test_store_tweet_to_cache ________________________

    async def test_store_tweet_to_cache(clean_redis, staging_dir, enriched_tweet_data):
>       assert cached_tweet is not None
E       AssertionError: assert None is not None

tests/test_integration/test_storage_integration.py:45: AssertionError
======================== 1 failed in 0.45s ========================
```

### Relatório de Cobertura
```
Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
src/tweetpulse/ingestion/storage.py          125     15    88%   45-50, 78-82
src/tweetpulse/ingestion/enrichment.py        87      8    91%   32-35
src/tweetpulse/ingestion/deduplication.py     23      2    91%   18-19
-------------------------------------------------------------------------
TOTAL                                         235     25    89%
```

## 🐛 Troubleshooting

### Problema: Testes Falhando Aleatoriamente
```bash
# Verificar se há race conditions
pytest tests/test_integration/ -v --count=10  # Executar 10 vezes

# Se falha inconsistentemente, há problema de determinismo
# Verificar:
# 1. Uso de time.sleep() ao invés de asyncio.sleep()
# 2. Timestamps não-fixos
# 3. Operações concorrentes sem locks
```

### Problema: Testes Muito Lentos
```bash
# Identificar testes lentos
pytest tests/test_integration/ --durations=10

# Executar em paralelo
make test-fast

# Ou otimizar fixtures (usar scope="session" quando possível)
```

### Problema: Import Errors
```bash
# Verificar instalação
pip list | grep tweetpulse

# Re-instalar em modo dev
pip install -e .

# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Problema: Fixture Not Found
```bash
# Verificar se conftest.py está presente
ls tests/test_integration/conftest.py

# Verificar nome da fixture
pytest --fixtures tests/test_integration/
```

## 📈 Boas Práticas

### ✅ DO
- Use fixtures para setup/teardown
- Mantenha testes independentes
- Use mocks para dependências externas
- Escreva testes determinísticos
- Adicione docstrings descritivas
- Teste casos felizes e casos de erro
- Execute testes antes de commit

### ❌ DON'T
- Não use `time.sleep()` arbitrário
- Não dependa de serviços externos
- Não compartilhe estado entre testes
- Não use números aleatórios sem seed
- Não ignore testes falhando
- Não commite código sem testes
- Não deixe testes comentados

## 🔗 Recursos Adicionais

### Documentação
- [README de Testes](tests/test_integration/README.md)
- [Pytest Docs](https://docs.pytest.org/)
- [Pytest Asyncio](https://pytest-asyncio.readthedocs.io/)

### Comandos Úteis
```bash
# Ver todos os comandos disponíveis
make help

# Ver ajuda do script de testes
./scripts/run_tests.sh --help

# Ver documentação dos testes
make docs

# Ver estatísticas
make test-stats
```

### Integração com IDE

#### VSCode
```json
// .vscode/settings.json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests/test_integration",
    "-v"
  ]
}
```

#### PyCharm
1. Settings → Tools → Python Integrated Tools
2. Default test runner: pytest
3. Working directory: Project root

## 🎓 Aprendendo Mais

### Tutorial: Criar Novo Teste

1. **Criar arquivo de teste**
```bash
touch tests/test_integration/test_my_component_integration.py
```

2. **Estrutura básica**
```python
import pytest
from tweetpulse.ingestion.my_component import MyComponent

class TestMyComponentIntegration:
    """Test MyComponent with deterministic behavior."""
    
    @pytest.mark.asyncio
    async def test_basic_operation(self, clean_redis):
        """Test basic operation is deterministic."""
        # Arrange
        component = MyComponent(redis=clean_redis)
        
        # Act
        result = await component.operation()
        
        # Assert
        assert result is not None
```

3. **Executar teste**
```bash
pytest tests/test_integration/test_my_component_integration.py -vv
```

### Tutorial: Debug de Teste

1. **Adicionar breakpoint**
```python
@pytest.mark.asyncio
async def test_my_operation(clean_redis):
    component = MyComponent(redis=clean_redis)
    
    import pdb; pdb.set_trace()  # Breakpoint
    
    result = await component.operation()
    assert result is not None
```

2. **Executar com debugger**
```bash
pytest tests/test_integration/test_my_component_integration.py --pdb
```

3. **Comandos do debugger**
```
n - next line
s - step into
c - continue
l - list code
p variable - print variable
q - quit
```

## 📞 Ajuda

Se encontrar problemas:

1. ✅ Verifique a [documentação](tests/test_integration/README.md)
2. ✅ Execute `make help` para ver comandos
3. ✅ Verifique logs em `tests/test_run.log`
4. ✅ Execute `make ci` para pipeline completo
5. ✅ Abra uma issue no repositório

---

**Lembre-se**: Testes determinísticos = menos bugs + mais confiança! 🎯

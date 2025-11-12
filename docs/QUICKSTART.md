# TweetPulse - Quick Start Guide 🚀

Escolha a versão que melhor se adequa aos seus recursos:

## 🪶 Versão Lite (Recomendada para Desenvolvimento)

**Ideal para:** Desenvolvimento local, recursos limitados, builds rápidos

```bash
# Opção 1: Script helper (mais fácil)
./scripts/run-lite.sh up

# Opção 2: Docker Compose direto
docker-compose -f docker-compose-lite.yml up --build

# Opção 3: Instalação local
pip install -r requirements-lite.txt
export USE_LITE_ENRICHMENT=1
uvicorn tweetpulse.main:app --reload
```

**Características:**
- ✅ Imagem Docker: ~500 MB
- ✅ Memória: ~500 MB - 1 GB
- ✅ Build: ~2-3 minutos
- ✅ Análise de sentimento: VADER (otimizado para redes sociais)
- ✅ Acurácia: ~80-85%

## 🔥 Versão Completa (Máxima Precisão)

**Ideal para:** Produção, análise avançada, recursos abundantes

```bash
# Docker Compose
docker-compose up --build

# Instalação local
pip install -r requirements.txt
uvicorn tweetpulse.main:app --reload
```

**Características:**
- 🎯 Imagem Docker: ~3.5 GB
- 🎯 Memória: ~2-4 GB
- 🎯 Build: ~10-15 minutos
- 🎯 Análise de sentimento: DistilBERT (Transformers)
- 🎯 Acurácia: ~90-95%

## 📊 Comparação Lado a Lado

| Métrica | Lite | Completa |
|---------|------|----------|
| Tamanho Docker | 500 MB | 3.5 GB |
| RAM | 500 MB - 1 GB | 2-4 GB |
| Tempo Build | 2-3 min | 10-15 min |
| Velocidade | Muito rápida | Moderada |
| Acurácia | 80-85% | 90-95% |
| GPU | Não precisa | Opcional |

## 🔧 Configuração Inicial

1. **Clone o repositório:**
```bash
git clone https://github.com/130591/tweetpulse.git
cd tweetpulse
```

2. **Configure variáveis de ambiente:**
```bash
cp .env.example .env
# Edite .env com suas credenciais
```

3. **Escolha e rode sua versão** (veja acima)

## 🌐 Acessando a Aplicação

Após iniciar, acesse:

- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:5173 (se rodando separadamente)

## 📚 Documentação Adicional

- [Versão Lite - Detalhes](docs/LITE_VERSION.md)
- [README Completo](README.md)
- [Contribuindo](CONTRIBUTING.md)

## 🆘 Problemas Comuns

### "Docker build muito lento"
➡️ Use a versão lite: `./scripts/run-lite.sh up`

### "Memória insuficiente"
➡️ Use a versão lite (usa 70% menos memória)

### "Module not found"
➡️ Certifique-se de instalar as dependências corretas:
- Lite: `pip install -r requirements-lite.txt`
- Completa: `pip install -r requirements.txt`

## 💡 Dica Pro

Para desenvolvimento iterativo rápido, use a versão lite. Para deploy em produção com máxima acurácia, use a versão completa.

Você pode alternar entre as versões a qualquer momento sem perder dados!

# 🌊 Pulse CLI - Quick Start

## 🎯 Instalação Rápida

```bash
# Na pasta do projeto
./install-cli.sh
```

Ou manualmente:

```bash
pip3 install -r requirements-cli.txt
chmod +x pulse.py
```

## 🚀 Uso Mais Comum

### 1. Modo Interativo (Recomendado)

```bash
python3 pulse.py
```

Você verá um menu bonito:

```
╔══════════════════════════════════════╗
║   🌊  PULSE CLI - TweetPulse  🌊    ║
║   Controle Total do seu Projeto      ║
╚══════════════════════════════════════╝

Escolha o que deseja rodar:

  1. ⚙️ Worker - Processa tweets do Kafka
  2. 🚀 Backend API - API FastAPI
  3. 💻 Frontend - Interface React
  4. 🔥 API Completa - Workers + Backend
  5. 🌊 Ambiente Completo - Todos os serviços + Frontend
  6. ❌ Parar tudo
  7. 🚪 Sair

Sua escolha [5]:
```

### 2. Comandos Diretos

```bash
# Desenvolvimento completo (mais usado)
python3 pulse.py dev all

# Apenas frontend
python3 pulse.py dev frontend

# Apenas backend + workers
python3 pulse.py dev api

# Ver status
python3 pulse.py status

# Ver logs
python3 pulse.py logs -f

# Parar tudo
python3 pulse.py stop
```

## 📊 Comandos Úteis

### Durante o desenvolvimento:

```bash
# 1. Iniciar ambiente
python3 pulse.py dev all

# 2. Em outro terminal, ver logs
python3 pulse.py logs -f

# 3. Verificar status
python3 pulse.py status
```

### Problemas? Limpe tudo:

```bash
# Parar
python3 pulse.py stop

# Limpar completamente
python3 pulse.py clean --all

# Rebuildar
python3 pulse.py rebuild

# Tentar novamente
python3 pulse.py dev all
```

## 🎨 Features da CLI

- ✨ **Bonita**: Interface colorida com emojis
- 🎯 **Interativa**: Menu fácil de usar
- ⚡ **Rápida**: Comandos diretos disponíveis
- 📊 **Informativa**: Status e logs em tempo real
- 🧹 **Completa**: Limpeza e rebuild fáceis

## 🔥 Workflows Recomendados

### Workflow 1: Desenvolvimento Frontend

```bash
# Terminal 1
python3 pulse.py dev frontend

# Acesse: http://localhost:5173
```

### Workflow 2: Desenvolvimento Backend

```bash
# Terminal 1
python3 pulse.py dev api

# Terminal 2
python3 pulse.py logs app -f

# Acesse: http://localhost:8000
```

### Workflow 3: Desenvolvimento Full Stack

```bash
# Terminal 1
python3 pulse.py dev all -d  # Roda tudo em background

# Terminal 2
python3 pulse.py logs -f

# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

### Workflow 4: Teste Completo

```bash
# Limpar ambiente
python3 pulse.py clean --all

# Rebuildar
python3 pulse.py rebuild

# Rodar tudo
python3 pulse.py dev all

# Verificar status
python3 pulse.py status
```

## 💡 Dicas Pro

### Criar alias permanente:

Adicione ao `~/.bashrc`:

```bash
alias pulse='python3 /home/evertonpaixao/projects/tweet-pulse/pulse.py'
```

Depois:

```bash
source ~/.bashrc

# Agora você pode usar apenas:
pulse
pulse dev all
pulse status
```

### Ver apenas logs de um serviço:

```bash
python3 pulse.py logs worker -f
python3 pulse.py logs app -f
```

### Rodar em background:

```bash
python3 pulse.py dev all -d
```

### Rebuild com start:

```bash
python3 pulse.py dev all -b
```

## 🆘 Troubleshooting

### Docker não inicia?

```bash
sudo service docker start
python3 pulse.py dev all
```

### Porta em uso?

```bash
python3 pulse.py stop
python3 pulse.py dev all
```

### Mudou código?

```bash
python3 pulse.py rebuild
python3 pulse.py dev all
```

### Tudo quebrado?

```bash
python3 pulse.py clean --all
python3 pulse.py rebuild
python3 pulse.py dev all
```

## 📚 Mais Informações

Ver documentação completa: `CLI_README.md`

---

**Comandos mais usados:**

```bash
python3 pulse.py              # Modo interativo
python3 pulse.py dev all      # Rodar tudo
python3 pulse.py dev frontend # Só frontend
python3 pulse.py status       # Ver status
python3 pulse.py logs -f      # Ver logs
python3 pulse.py stop         # Parar tudo
```

🌊 **Happy coding!**

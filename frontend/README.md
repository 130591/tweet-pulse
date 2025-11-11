# TweetPulse Frontend

Frontend moderno para o TweetPulse - Sistema de análise de tweets em tempo real.

## 🚀 Stack Tecnológica

- **React 18** com TypeScript
- **Vite** - Build tool rápido
- **Ant Design** - Biblioteca de componentes UI
- **Recharts** - Gráficos e visualizações
- **Lucide React** - Ícones modernos

## 📦 Instalação

```bash
npm install
```

## 🏃 Executar em Desenvolvimento

```bash
npm run dev
```

O frontend estará disponível em `http://localhost:5173`

## 🏗️ Build para Produção

```bash
npm run build
```

## 📁 Estrutura do Projeto

```
frontend/
├── src/
│   ├── components/
│   │   ├── Sidebar.tsx        # Navegação lateral
│   │   ├── Header.tsx         # Cabeçalho com busca
│   │   ├── MainContent.tsx    # Conteúdo principal com gráficos
│   │   └── RightPanel.tsx     # Painel de filtros
│   ├── App.tsx                # Componente raiz
│   ├── App.css                # Estilos globais
│   └── main.tsx              # Ponto de entrada
└── package.json
```

## 🎨 Componentes Principais

### Sidebar
- Logo do TweetPulse
- Lista de projetos/hashtags monitoradas
- Menu de navegação (Mentions, Analysis)

### Header
- Barra de pesquisa
- Botão de upgrade
- Notificações
- Avatar do usuário
- Filtros ativos

### MainContent
- Tabs (Mentions & Reach, Sentiment)
- Gráficos de linha com Recharts
- Lista de menções/tweets
- Paginação

### RightPanel
- Filtro de fontes (Twitter/X)
- Filtro de sentimento (Positive/Neutral/Negative)
- Slider de Influence Score
- Filtros de geolocalização
- Filtros de idioma

## 🔧 Funcionalidades

- ✅ Interface responsiva
- ✅ Gráficos interativos
- ✅ Filtros dinâmicos
- ✅ Componentes Ant Design
- ✅ TypeScript para type safety

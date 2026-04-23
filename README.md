# 💹 Carteira Financeira — Gestão Local de Investimentos

Aplicativo web local para gerenciar sua carteira de investimentos com cotações automáticas da B3 e NYSE/NASDAQ, banco de dados SQLite e interface dark moderna.

---

## 🚧 Status do Projeto

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-local-green?logo=sqlite)
![yfinance](https://img.shields.io/badge/yfinance-cotações%20automáticas-orange)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

---

## 📚 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades Principais](#-funcionalidades-principais)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Instalação e Execução](#-instalação-e-execução)
- [Estrutura de Pastas](#-estrutura-de-pastas)
- [Como Usar](#-como-usar)
- [Backup e Restauração](#-backup-e-restauração)

---

## 📝 Sobre o Projeto

Este projeto nasceu da necessidade de ter uma visão clara e centralizada da carteira de investimentos, sem depender de aplicativos de terceiros ou expor dados financeiros em nuvens externas.

Em vez de anotar tudo em bloco de notas ou planilhas espalhadas, o objetivo foi criar uma ferramenta local, simples de rodar no Windows, com banco de dados real e cotações automáticas da B3 e da bolsa americana.

O projeto foi desenvolvido com foco em:

- **Privacidade** — todos os dados ficam no seu próprio computador
- **Simplicidade** — um único comando para iniciar, sem configurações complexas
- **Praticidade** — cotações atualizadas automaticamente a cada 15 minutos via Yahoo Finance
- **Completude** — suporte a Ações, FIIs, Stocks, REITs e Renda Fixa

---

## ✨ Funcionalidades Principais

- 📊 **Resumo** — patrimônio total, ganho de capital, rentabilidade, gráficos de distribuição e aportes mês a mês com rendimento
- 💼 **Carteira** — todas as posições com preço médio, preço atual, ganho por ativo, variação percentual e histórico de preços dos últimos 6 meses (botão 📈)
- 💰 **Proventos** — registro e histórico de dividendos, JCP, rendimentos de FII e cupons; gráfico mensal com linha de meta; suporte a proventos em dólar (REITs/Stocks) com conversão automática
- 📈 **Planejamento** — metas editáveis de patrimônio, proventos mensais e aporte mensal; metas de alocação por tipo editáveis; barras de progresso em tempo real
- 📥 **Aportes** — histórico de aportes com data, valor e descrição livre (origem do dinheiro); gráfico mensal; integrado com o Planejamento
- ➕ **Lançamentos** — cadastro de ativos com preço médio ponderado automático ao lançar compras adicionais; DY buscado automaticamente via yfinance
- 🔄 **Cotações automáticas** — atualização a cada 15 minutos via yfinance (B3 e NYSE/NASDAQ); DY automático ao cadastrar
- 💵 **Suporte a dólar** — Stocks e REITs exibem valores em US$ com conversão automática para R$ via cotação em tempo real
- 🏦 **Renda Fixa detalhada** — subtipo (CDB, LCI, LCA, Tesouro...), taxa contratada (IPCA+, CDI, % fixo), data de vencimento, dias restantes e rentabilidade estimada no vencimento
- ✏️ **Edição inline** — editar e remover ativos, proventos e aportes diretamente pelo app
- 🔒 **Modo sigilo** — ocultar todos os valores com um clique (botão 👁 na sidebar)
- 🌙 **Tema claro/escuro** — alternável com persistência entre sessões
- 💾 **Backup/Restauração** — exportar e importar dados em JSON a qualquer momento

---

## 🛠 Tecnologias Utilizadas

### 🖥 Backend
- **Linguagem:** Python 3.8+
- **Framework:** Flask
- **Banco de dados:** SQLite (arquivo local `carteira.db`)
- **Cotações:** yfinance (Yahoo Finance) — B3, NYSE, NASDAQ e câmbio USD/BRL

### 💻 Frontend
- **HTML + CSS + JavaScript** puro — sem frameworks, sem dependências externas
- **Fontes:** Inter + JetBrains Mono (Google Fonts)
- **Gráficos:** Chart.js

### ☁️ Infraestrutura
- Roda 100% localmente — sem internet obrigatória (exceto para cotações)
- Compatível com Windows 10/11

---

## 🔧 Instalação e Execução

### Pré-requisitos

- Windows 10 ou 11
- [Python 3.8+](https://www.python.org/downloads/) — marque **"Add Python to PATH"** na instalação
- Chrome ou Edge

### Passos

**1. Baixe e extraia o projeto:**
```
carteira_app/
├── server.py
├── instalar.bat
├── iniciar.bat
└── static/
    └── index.html
```

**2. Instale as dependências (só na primeira vez):**
```bash
# Clique duas vezes em instalar.bat
# Ou rode no terminal:
pip install flask yfinance
```

**3. Inicie o servidor:**
```bash
# Clique duas vezes em iniciar.bat
# Ou rode no terminal:
python server.py
```

**4. Acesse no navegador:**
```
http://localhost:5000
```

> ⚠️ Mantenha a janela do terminal aberta enquanto usa o app. Feche-a para encerrar o servidor.

---

## 📂 Estrutura de Pastas

```
carteira_app/
├── server.py          # Servidor Flask + API REST + integração yfinance
├── carteira.db        # Banco de dados SQLite (criado automaticamente)
├── instalar.bat       # Instala Flask e yfinance (rodar uma vez)
├── iniciar.bat        # Inicia o servidor e abre o navegador
└── static/
    └── index.html     # Frontend completo (HTML + CSS + JS)
```

---

## 📖 Como Usar

### Cadastrar um ativo
1. Acesse a aba **Lançamentos**
2. Preencha o ticker (ex: `PETR4`, `MXRF11`, `AAPL`, `O`), tipo, quantidade e preço médio
3. O preço atual e o DY são buscados automaticamente para Ações, FIIs, Stocks e REITs
4. Para **Renda Fixa**, aparece uma seção extra com subtipo, taxa contratada e data de vencimento

> 💡 Ao cadastrar um ativo que já existe, o app soma a quantidade e recalcula o preço médio ponderado automaticamente.

### Tipos de ativo suportados

| Tipo | Cotação automática | Moeda | Exemplo |
|---|---|---|---|
| Ações | ✅ (B3) | R$ | PETR4, VALE3 |
| FIIs | ✅ (B3) | R$ | MXRF11, HGLG11 |
| Stocks | ✅ (NYSE/NASDAQ) | US$ → R$ | AAPL, GOOGL |
| REITs | ✅ (NYSE) | US$ → R$ | O, PLD |
| Renda Fixa | ❌ (manual) | R$ | Tesouro IPCA+ 2029, CDB |

### Stocks e REITs (ativos em dólar)
- Informe o ticker americano direto (ex: `GOOGL`, `PLD`)
- Selecione o tipo `Stocks` ou `REITs`
- Preencha quantidade e preço médio **em dólares**
- O app busca a cotação atual em US$ e converte automaticamente para R$ usando a cotação em tempo real

### Renda Fixa
- **Subtipo:** CDB, LCI, LCA, Tesouro Direto, etc.
- **Taxa:** informe como `IPCA+6%`, `110% CDI` ou `12% a.a.`
- **Vencimento:** o app calcula os dias restantes e estima o valor no vencimento

### Registrar proventos
1. Acesse a aba **Proventos**
2. Preencha o ativo, valor total recebido, data e tipo
3. Para REITs e Stocks, use a seção de **Proventos em dólar** com conversão automática

> 💡 O valor a ser lançado é o **total recebido** (quantidade × valor por cota). Exemplo: 10 cotas × R$ 0,12 = **R$ 1,20**.

### Registrar aportes
1. Acesse a aba **Aportes**
2. Preencha a data, valor e descrição (ex: "Salário", "Educat")
3. O Planejamento mostra automaticamente o total aportado no mês atual vs sua meta

### Atualizar cotações manualmente
- Clique no botão **⟳ Atualizar cotações** nas abas Resumo ou Carteira
- As cotações também atualizam automaticamente a cada **15 minutos**

### Modo sigilo
- Clique no botão **👁** na parte inferior da sidebar para ocultar todos os valores com blur
- A preferência é salva entre sessões

---

## 💾 Backup e Restauração

### Exportar dados
- Clique em **↓ Backup JSON** na aba Lançamentos
- Um arquivo `carteira_backup_AAAA-MM-DD.json` será baixado

### Restaurar dados
- Clique em **↑ Restaurar JSON** e selecione o arquivo de backup
- Os dados existentes serão substituídos pelos do backup

### Backup manual do banco
- Copie o arquivo `carteira.db` para um local seguro
- Para restaurar, substitua o arquivo na pasta do app

---

## 👤 Autor

| 👤 Nome | :octocat: GitHub | 💼 LinkedIn | 📤 Email |
|---|---|---|---|
| Caio Souza de Resende | [CaioSResende](https://github.com/CaioSResende) | [caiosouzaderesende](https://linkedin.com/in/caiosouzaderesende) | caiosouzamresende@gmail.com |

Junior Cloud Architect @ ForceOne | Estudante de Engenharia de Software @ PUC Minas

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT.

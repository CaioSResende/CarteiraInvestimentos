# 💹 Carteira Financeira — Gestão Local de Investimentos

Aplicativo web local para gerenciar sua carteira de investimentos com cotações automáticas da B3, banco de dados SQLite e interface dark moderna.

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

- 📊 **Resumo** — patrimônio total, ganho de capital, rentabilidade e gráficos de distribuição e evolução
- 💼 **Carteira** — todas as posições com preço médio, preço atual, ganho por ativo e variação percentual
- 💰 **Proventos** — registro e histórico de dividendos, JCP, rendimentos de FII e cupons de renda fixa, com gráfico mensal
- 📈 **Planejamento** — metas de alocação por tipo de ativo e calculadora de prazo para atingir patrimônio-alvo
- ➕ **Lançamentos** — cadastro de ativos com preço médio ponderado automático ao lançar compras adicionais
- 🔄 **Cotações automáticas** — atualização a cada 15 minutos via yfinance (B3 e NYSE/NASDAQ)
- ✏️ **Edição inline** — editar e remover ativos e proventos diretamente pelo app
- 💾 **Backup/Restauração** — exportar e importar dados em JSON a qualquer momento

---

## 🛠 Tecnologias Utilizadas

### 🖥 Backend
- **Linguagem:** Python 3.8+
- **Framework:** Flask
- **Banco de dados:** SQLite (arquivo local `carteira.db`)
- **Cotações:** yfinance (Yahoo Finance)

### 💻 Frontend
- **HTML + CSS + JavaScript** puro — sem frameworks, sem dependências externas
- **Fontes:** DM Sans + DM Mono (Google Fonts)
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
2. Preencha o ticker (ex: `PETR4`, `MXRF11`, `AAPL`), tipo, quantidade e preço médio
3. O preço atual é buscado automaticamente para Ações, FIIs, Stocks e REITs
4. Para **Renda Fixa**, preencha o preço atual manualmente

> 💡 Ao cadastrar um ativo que já existe na carteira, o app soma a quantidade e recalcula o preço médio ponderado automaticamente.

### Tipos de ativo suportados

| Tipo | Cotação automática | Exemplo |
|---|---|---|
| Ações | ✅ (B3) | PETR4, VALE3 |
| FIIs | ✅ (B3) | MXRF11, HGLG11 |
| Stocks | ✅ (NYSE/NASDAQ) | AAPL, MSFT |
| REITs | ✅ (NYSE) | O, REALTY |
| Renda Fixa | ❌ (manual) | Tesouro IPCA+ 2029 |

### Registrar proventos
1. Acesse a aba **Proventos**
2. Preencha o ativo, valor total recebido, data e tipo
3. O histórico fica salvo e é exibido no gráfico mensal

> 💡 O valor a ser lançado é o **total recebido** (quantidade de cotas × valor por cota). Exemplo: 10 cotas × R$ 0,12 = R$ 1,20.

### Atualizar cotações manualmente
- Clique no botão **⟳ Atualizar cotações** nas abas Resumo ou Carteira
- As cotações também são atualizadas automaticamente a cada **15 minutos** enquanto o servidor estiver rodando

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

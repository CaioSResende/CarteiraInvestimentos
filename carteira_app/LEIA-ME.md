# 💹 Carteira Financeira — Guia de Instalação

## O que você vai precisar
- Windows 10 ou 11
- Python (gratuito, você instala uma vez)
- O Chrome ou Edge para acessar o app

---

## Passo 1 — Instalar o Python (só na primeira vez)

1. Acesse: https://www.python.org/downloads/
2. Clique em **"Download Python"** (o botão amarelo grande)
3. Abra o instalador baixado
4. **IMPORTANTE:** Marque a caixa **"Add Python to PATH"** antes de clicar em Install
5. Clique em **Install Now** e aguarde

---

## Passo 2 — Preparar a pasta do app

1. Crie uma pasta em qualquer lugar, por exemplo: `C:\MeuApp\carteira`
2. Coloque os arquivos assim:
   ```
   carteira\
   ├── server.py
   ├── instalar.bat
   ├── iniciar.bat
   └── static\
       └── index.html
   ```

---

## Passo 3 — Instalar dependências (só na primeira vez)

1. Abra a pasta `carteira`
2. Clique duas vezes em **`instalar.bat`**
3. Aguarde aparecer "Tudo pronto!"

---

## Passo 4 — Usar o app

1. Clique duas vezes em **`iniciar.bat`**
2. Uma janela preta vai abrir (não feche ela — é o servidor rodando)
3. O navegador abre automaticamente em `http://localhost:5000`
4. Pronto! Seu app está rodando ✅

**Para fechar o app:** Feche a janela preta ou pressione `Ctrl+C` nela.

---

## Onde ficam seus dados?

Seus dados ficam salvos no arquivo **`carteira.db`** dentro da pasta do app.
Esse arquivo é criado automaticamente na primeira vez que você rodar o servidor.

- **Para fazer backup:** Clique em "Backup JSON" dentro do app, ou simplesmente copie o arquivo `carteira.db`
- **Para restaurar:** Use o botão "Restaurar JSON" no app

---

## Perguntas frequentes

**O app abre mas não carrega os dados?**
Verifique se a janela preta (servidor) está aberta e sem erros.

**Aparece "Python não encontrado"?**
Reinstale o Python marcando a opção "Add Python to PATH".

**Posso acessar de outro computador?**
Sim! Outros computadores na mesma rede podem acessar pelo endereço IP do seu PC:
`http://SEU_IP:5000` (descubra seu IP com `ipconfig` no terminal).

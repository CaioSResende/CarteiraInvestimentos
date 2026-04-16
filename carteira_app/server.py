"""
Carteira Financeira - Servidor local com cotações automáticas (yfinance)
Rode com: python server.py
Acesse em: http://localhost:5000
"""

from flask import Flask, jsonify, request, send_from_directory
import sqlite3, os, json, threading, time
from datetime import datetime

# yfinance é importado com tratamento de erro caso não esteja instalado ainda
try:
    import yfinance as yf
    YFINANCE_OK = True
except ImportError:
    YFINANCE_OK = False
    print("⚠ yfinance não encontrado. Execute instalar.bat novamente.")

app = Flask(__name__, static_folder='static')
DB  = 'carteira.db'

# ── BANCO DE DADOS ─────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ativos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker      TEXT NOT NULL,
            tipo        TEXT NOT NULL,
            qtd         REAL NOT NULL,
            medio       REAL NOT NULL,
            atual       REAL NOT NULL,
            dy          REAL DEFAULT 0,
            auto_cotacao INTEGER DEFAULT 1,
            ultima_atualizacao TEXT,
            criado      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS proventos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo   TEXT NOT NULL,
            valor   REAL NOT NULL,
            data    TEXT NOT NULL,
            tipo    TEXT DEFAULT 'Dividendo',
            criado  TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    conn.close()
    print("✓ Banco de dados pronto.")

# ── COTAÇÕES (yfinance) ────────────────────────────────────────────────────────
# Tickers americanos conhecidos não levam .SA
TICKERS_USA = set()  # populado dinamicamente pelo tipo

def ticker_b3(ticker, tipo=''):
    """
    Converte o ticker para o formato do Yahoo Finance.
    - Ações/FIIs brasileiros: adiciona .SA (ex: PETR4 → PETR4.SA)
    - Stocks/REITs americanos: usa o ticker direto (ex: AAPL, O)
    - Renda Fixa: retorna None (sem cotação automática)
    """
    ignorar = ['tesouro', 'cdb', 'lci', 'lca', 'debenture', 'poupança']
    if any(p in ticker.lower() for p in ignorar):
        return None
    if tipo in ('Stocks', 'REITs'):
        return ticker  # ticker americano, sem sufixo
    if ticker.endswith('.SA'):
        return ticker
    return ticker + '.SA'

def buscar_cotacao(ticker, tipo=''):
    """Busca o preço atual de um ticker via yfinance. Retorna None se falhar."""
    if not YFINANCE_OK:
        return None
    t = ticker_b3(ticker, tipo)
    if not t:
        return None
    try:
        dados = yf.Ticker(t)
        info  = dados.fast_info
        preco = getattr(info, 'last_price', None) or getattr(info, 'regular_market_price', None)
        if preco and preco > 0:
            return round(float(preco), 2)
    except Exception as e:
        print(f"  ⚠ Erro ao buscar {ticker}: {e}")
    return None

def atualizar_cotacoes():
    """Atualiza o preço atual de todos os ativos com auto_cotacao=1."""
    if not YFINANCE_OK:
        return
    conn = get_db()
    ativos = conn.execute(
        "SELECT id, ticker, tipo FROM ativos WHERE auto_cotacao=1"
    ).fetchall()
    conn.close()

    if not ativos:
        return

    print(f"\n🔄 Atualizando cotações de {len(ativos)} ativo(s)...")
    atualizados = 0
    for a in ativos:
        preco = buscar_cotacao(a['ticker'], a['tipo'])
        if preco:
            conn = get_db()
            conn.execute(
                "UPDATE ativos SET atual=?, ultima_atualizacao=? WHERE id=?",
                (preco, datetime.now().strftime('%d/%m/%Y %H:%M'), a['id'])
            )
            conn.commit()
            conn.close()
            print(f"  ✓ {a['ticker']}: R$ {preco}")
            atualizados += 1
        else:
            print(f"  — {a['ticker']}: sem cotação automática (Renda Fixa ou erro)")

    print(f"✓ {atualizados} ativo(s) atualizado(s).\n")

def loop_atualizacao(intervalo_minutos=15):
    """Atualiza cotações automaticamente a cada N minutos em background."""
    while True:
        atualizar_cotacoes()
        time.sleep(intervalo_minutos * 60)

# ── ROTAS: FRONTEND ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── ROTAS: ATIVOS ──────────────────────────────────────────────────────────────
@app.route('/api/ativos', methods=['GET'])
def listar_ativos():
    conn = get_db()
    rows = conn.execute('SELECT * FROM ativos ORDER BY tipo, ticker').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ativos', methods=['POST'])
def criar_ativo():
    d = request.json
    ticker = d['ticker'].strip().upper()
    qtd_nova   = float(d['qtd'])
    medio_novo = float(d['medio'])
    dy_novo    = float(d.get('dy', 0))

    # Tenta buscar cotação atual ao cadastrar
    cotacao = buscar_cotacao(ticker, d.get('tipo',''))
    preco_atual = cotacao if cotacao else float(d.get('atual', 0))
    if cotacao:
        print(f"  ✓ Cotação ao cadastrar {ticker}: R$ {cotacao}")

    conn = get_db()

    # Verifica se o ticker já existe na carteira
    existente = conn.execute(
        'SELECT * FROM ativos WHERE ticker=?', (ticker,)
    ).fetchone()

    if existente:
        # Calcula novo preço médio ponderado e soma as quantidades
        qtd_atual   = existente['qtd']
        medio_atual = existente['medio']
        nova_qtd    = qtd_atual + qtd_nova
        novo_medio  = (qtd_atual * medio_atual + qtd_nova * medio_novo) / nova_qtd

        conn.execute(
            'UPDATE ativos SET qtd=?, medio=?, atual=?, dy=?, ultima_atualizacao=? WHERE id=?',
            (nova_qtd, round(novo_medio, 4), preco_atual,
             dy_novo if dy_novo else existente['dy'],
             datetime.now().strftime('%d/%m/%Y %H:%M') if cotacao else existente['ultima_atualizacao'],
             existente['id'])
        )
        conn.commit()
        row = conn.execute('SELECT * FROM ativos WHERE id=?', (existente['id'],)).fetchone()
        print(f"  ✓ {ticker} atualizado: {qtd_atual} + {qtd_nova} = {nova_qtd} cotas, P.M. R$ {round(novo_medio,2)}")
    else:
        conn.execute(
            'INSERT INTO ativos (ticker, tipo, qtd, medio, atual, dy, auto_cotacao, ultima_atualizacao) VALUES (?,?,?,?,?,?,?,?)',
            (ticker, d['tipo'], qtd_nova, medio_novo, preco_atual,
             dy_novo, d.get('auto_cotacao', 1),
             datetime.now().strftime('%d/%m/%Y %H:%M') if cotacao else None)
        )
        conn.commit()
        id_ = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        row = conn.execute('SELECT * FROM ativos WHERE id=?', (id_,)).fetchone()

    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/ativos/<int:id>', methods=['PUT'])
def atualizar_ativo(id):
    d = request.json
    conn = get_db()
    conn.execute(
        'UPDATE ativos SET ticker=?, tipo=?, qtd=?, medio=?, atual=?, dy=?, auto_cotacao=? WHERE id=?',
        (d['ticker'].upper(), d['tipo'], d['qtd'], d['medio'],
         d['atual'], d.get('dy', 0), d.get('auto_cotacao', 1), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM ativos WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/api/ativos/<int:id>', methods=['DELETE'])
def deletar_ativo(id):
    conn = get_db()
    conn.execute('DELETE FROM ativos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ── ROTA: FORÇAR ATUALIZAÇÃO MANUAL ───────────────────────────────────────────
@app.route('/api/atualizar-cotacoes', methods=['POST'])
def forcar_atualizacao():
    """Atualiza cotações imediatamente ao clicar no botão do app."""
    thread = threading.Thread(target=atualizar_cotacoes, daemon=True)
    thread.start()
    thread.join(timeout=30)  # aguarda até 30s
    # Retorna os ativos já atualizados
    conn = get_db()
    rows = conn.execute('SELECT * FROM ativos ORDER BY tipo, ticker').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── ROTAS: PROVENTOS ───────────────────────────────────────────────────────────
@app.route('/api/proventos', methods=['GET'])
def listar_proventos():
    conn = get_db()
    rows = conn.execute('SELECT * FROM proventos ORDER BY data DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/proventos', methods=['POST'])
def criar_provento():
    d = request.json
    conn = get_db()
    conn.execute(
        'INSERT INTO proventos (ativo, valor, data, tipo) VALUES (?,?,?,?)',
        (d['ativo'].upper(), d['valor'], d['data'], d.get('tipo', 'Dividendo'))
    )
    conn.commit()
    id_ = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    row = conn.execute('SELECT * FROM proventos WHERE id=?', (id_,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/proventos/<int:id>', methods=['PUT'])
def atualizar_provento(id):
    d = request.json
    conn = get_db()
    conn.execute(
        'UPDATE proventos SET ativo=?, valor=?, data=?, tipo=? WHERE id=?',
        (d['ativo'].upper(), d['valor'], d['data'], d.get('tipo','Dividendo'), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM proventos WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/api/proventos/<int:id>', methods=['DELETE'])
def deletar_provento(id):
    conn = get_db()
    conn.execute('DELETE FROM proventos WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ── ROTAS: BACKUP / RESTAURAR ─────────────────────────────────────────────────
@app.route('/api/backup', methods=['GET'])
def backup():
    conn = get_db()
    ativos    = [dict(r) for r in conn.execute('SELECT * FROM ativos').fetchall()]
    proventos = [dict(r) for r in conn.execute('SELECT * FROM proventos').fetchall()]
    conn.close()
    return jsonify({'ativos': ativos, 'proventos': proventos, 'exportado': datetime.now().isoformat()})

@app.route('/api/restaurar', methods=['POST'])
def restaurar():
    d = request.json
    conn = get_db()
    if 'ativos' in d:
        conn.execute('DELETE FROM ativos')
        for a in d['ativos']:
            conn.execute(
                'INSERT INTO ativos (ticker,tipo,qtd,medio,atual,dy,auto_cotacao) VALUES (?,?,?,?,?,?,?)',
                (a['ticker'], a['tipo'], a['qtd'], a['medio'], a['atual'], a.get('dy',0), a.get('auto_cotacao',1))
            )
    if 'proventos' in d:
        conn.execute('DELETE FROM proventos')
        for p in d['proventos']:
            conn.execute('INSERT INTO proventos (ativo,valor,data,tipo) VALUES (?,?,?,?)',
                (p['ativo'], p['valor'], p['data'], p.get('tipo','Dividendo')))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ── INICIAR ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()

    # Atualiza cotações ao iniciar e depois a cada 15 minutos em background
    if YFINANCE_OK:
        t = threading.Thread(target=loop_atualizacao, args=(15,), daemon=True)
        t.start()
        print("✓ Atualização automática de cotações ativada (a cada 15 min).")
    else:
        print("⚠ Cotações automáticas desativadas (yfinance não instalado).")

    print("\n" + "="*45)
    print("  💹 Carteira Financeira rodando!")
    print("  Acesse: http://localhost:5000")
    print("  Para parar: pressione Ctrl+C")
    print("="*45 + "\n")
    app.run(debug=False, port=5000)

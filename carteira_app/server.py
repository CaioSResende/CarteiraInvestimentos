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
            criado      TEXT DEFAULT (datetime('now','localtime')),
            rf_subtipo  TEXT,
            rf_taxa     TEXT,
            rf_vencimento TEXT,
            moeda       TEXT DEFAULT 'BRL'
        );
        CREATE TABLE IF NOT EXISTS proventos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo   TEXT NOT NULL,
            valor   REAL NOT NULL,
            data    TEXT NOT NULL,
            tipo    TEXT DEFAULT 'Dividendo',
            criado  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS snapshots (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            mes         TEXT NOT NULL UNIQUE,
            patrimonio  REAL NOT NULL,
            investido   REAL NOT NULL,
            criado      TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS hist_precos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker  TEXT NOT NULL,
            mes     TEXT NOT NULL,
            preco   REAL NOT NULL,
            UNIQUE(ticker, mes)
        );
        CREATE TABLE IF NOT EXISTS aportes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            data    TEXT NOT NULL,
            valor   REAL NOT NULL,
            descricao TEXT,
            origem  TEXT DEFAULT 'manual',
            criado  TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()

    # Migração: adicionar colunas de renda fixa se não existirem
    cols = [r[1] for r in conn.execute("PRAGMA table_info(ativos)").fetchall()]
    for col, defval in [('rf_subtipo','TEXT'), ('rf_taxa','TEXT'), ('rf_vencimento','TEXT'), ('moeda',"TEXT DEFAULT 'BRL'")]:
        if col not in cols:
            conn.execute(f"ALTER TABLE ativos ADD COLUMN {col} {defval}")
            print(f"  ✓ Coluna '{col}' adicionada à tabela ativos.")
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

def buscar_dy(ticker, tipo=''):
    """Busca o Dividend Yield anual via yfinance. Retorna 0 se não disponível."""
    if not YFINANCE_OK:
        return 0
    t = ticker_b3(ticker, tipo)
    if not t:
        return 0
    try:
        dados = yf.Ticker(t)
        info  = dados.info
        # dividendYield já vem como fração (ex: 0.085 = 8.5%)
        dy = info.get('dividendYield') or info.get('trailingAnnualDividendYield') or 0
        if dy and dy > 0:
            return round(float(dy) * 100, 2)
    except Exception as e:
        print(f"  ⚠ Erro ao buscar DY de {ticker}: {e}")
    return 0

def buscar_historico_precos(ticker, tipo='', periodo='6mo'):
    """Busca histórico de preços fechamento mensal via yfinance."""
    if not YFINANCE_OK:
        return []
    t = ticker_b3(ticker, tipo)
    if not t:
        return []
    try:
        dados = yf.Ticker(t)
        hist  = dados.history(period=periodo, interval='1mo')
        result = []
        for dt, row in hist.iterrows():
            result.append({
                'data': dt.strftime('%Y-%m'),
                'preco': round(float(row['Close']), 2)
            })
        return result
    except Exception as e:
        print(f"  ⚠ Erro ao buscar histórico de {ticker}: {e}")
    return []

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
    salvar_snapshot()

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
    dy_novo       = float(str(d.get('dy', 0) or 0).replace(',', '.'))
    tipo_ativo    = d.get('tipo','')
    rf_subtipo    = d.get('rf_subtipo', '') or ''
    rf_taxa       = d.get('rf_taxa', '') or ''
    rf_vencimento = d.get('rf_vencimento', '') or '' 

    # Tenta buscar cotação e DY automaticamente ao cadastrar
    cotacao = buscar_cotacao(ticker, tipo_ativo)
    preco_atual = cotacao if cotacao else float(d.get('atual', 0))
    if cotacao:
        print(f"  ✓ Cotação ao cadastrar {ticker}: R$ {cotacao}")

    # Busca DY se não informado pelo usuário
    if not dy_novo and tipo_ativo != 'Renda Fixa':
        dy_auto = buscar_dy(ticker, tipo_ativo)
        if dy_auto:
            dy_novo = dy_auto
            print(f"  ✓ DY automático {ticker}: {dy_auto}%")

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
            'INSERT INTO ativos (ticker, tipo, qtd, medio, atual, dy, auto_cotacao, ultima_atualizacao, rf_subtipo, rf_taxa, rf_vencimento, moeda) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (ticker, d['tipo'], qtd_nova, medio_novo, preco_atual,
             dy_novo, d.get('auto_cotacao', 1),
             datetime.now().strftime('%d/%m/%Y %H:%M') if cotacao else None,
             rf_subtipo, rf_taxa, rf_vencimento,
             'USD' if d.get('tipo','') in ('Stocks','REITs') else 'BRL')
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
        'UPDATE ativos SET ticker=?, tipo=?, qtd=?, medio=?, atual=?, dy=?, auto_cotacao=?, rf_subtipo=?, rf_taxa=?, rf_vencimento=?, moeda=? WHERE id=?',
        (d['ticker'].upper(), d['tipo'], d['qtd'], d['medio'],
         d['atual'], d.get('dy', 0), d.get('auto_cotacao', 1),
         d.get('rf_subtipo',''), d.get('rf_taxa',''), d.get('rf_vencimento',''),
         'USD' if d.get('tipo','') in ('Stocks','REITs') else d.get('moeda','BRL'), id)
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

# ── ROTAS: SNAPSHOTS ──────────────────────────────────────────────────────────
def salvar_snapshot():
    """Salva ou atualiza o snapshot do mês atual com patrimônio e investido."""
    conn = get_db()
    ativos = conn.execute('SELECT qtd, medio, atual FROM ativos').fetchall()
    if not ativos:
        conn.close()
        return
    patrimonio = sum(a['qtd'] * a['atual']  for a in ativos)
    investido  = sum(a['qtd'] * a['medio'] for a in ativos)
    mes = datetime.now().strftime('%Y-%m')
    conn.execute(
        'INSERT INTO snapshots (mes, patrimonio, investido) VALUES (?,?,?) '
        'ON CONFLICT(mes) DO UPDATE SET patrimonio=excluded.patrimonio, investido=excluded.investido',
        (mes, round(patrimonio,2), round(investido,2))
    )
    conn.commit()
    conn.close()
    print(f"  ✓ Snapshot {mes}: patrimônio={patrimonio:.2f} investido={investido:.2f}")

@app.route('/api/historico/<string:ticker>', methods=['GET'])
def historico_ativo(ticker):
    """Retorna histórico de preços do ativo + preço médio para comparação."""
    conn = get_db()
    ativo = conn.execute('SELECT * FROM ativos WHERE ticker=?', (ticker.upper(),)).fetchone()
    conn.close()
    if not ativo:
        return jsonify({'error': 'Ativo não encontrado'}), 404

    # Busca histórico via yfinance
    hist = buscar_historico_precos(ticker, ativo['tipo'])

    # Salva no banco para cache
    if hist:
        conn = get_db()
        for h in hist:
            conn.execute(
                'INSERT INTO hist_precos (ticker, mes, preco) VALUES (?,?,?) '
                'ON CONFLICT(ticker, mes) DO UPDATE SET preco=excluded.preco',
                (ticker.upper(), h['data'], h['preco'])
            )
        conn.commit()
        conn.close()

    return jsonify({
        'ticker': ticker.upper(),
        'medio': ativo['medio'],
        'atual': ativo['atual'],
        'tipo': ativo['tipo'],
        'historico': hist
    })

@app.route('/api/snapshots', methods=['GET'])
def listar_snapshots():
    conn = get_db()
    rows = conn.execute('SELECT * FROM snapshots ORDER BY mes').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/rf/rentabilidade', methods=['POST'])
def calcular_rentabilidade_rf():
    """Calcula rentabilidade estimada de renda fixa com base na taxa e data de vencimento."""
    from datetime import date
    import math
    d = request.json
    investido   = float(d.get('investido', 0))
    taxa_str    = d.get('taxa', '')
    vencimento  = d.get('vencimento', '')

    if not investido or not taxa_str or not vencimento:
        return jsonify({'erro': 'Dados insuficientes'}), 400

    hoje = date.today()
    try:
        venc = date.fromisoformat(vencimento)
    except:
        return jsonify({'erro': 'Data inválida'}), 400

    dias_totais    = (venc - hoje).days
    anos_restantes = dias_totais / 365

    # Interpretar taxa
    taxa_str_lower = taxa_str.lower().strip()
    taxa_anual = 0

    # CDI atual aproximado
    CDI_ATUAL = 10.65  # % a.a.
    IPCA_ATUAL = 4.83  # % a.a.
    SELIC_ATUAL = 13.25

    if 'cdi' in taxa_str_lower:
        try:
            pct = float(''.join(c for c in taxa_str_lower.split('cdi')[0] if c.isdigit() or c == '.')) 
            taxa_anual = CDI_ATUAL * pct / 100
        except:
            taxa_anual = CDI_ATUAL
    elif 'ipca' in taxa_str_lower:
        try:
            spread = float(''.join(c for c in taxa_str_lower.replace('ipca','').replace('+','').strip() if c.isdigit() or c == '.'))
            taxa_anual = IPCA_ATUAL + spread
        except:
            taxa_anual = IPCA_ATUAL
    elif 'selic' in taxa_str_lower:
        try:
            pct = float(''.join(c for c in taxa_str_lower.split('selic')[0] if c.isdigit() or c == '.'))
            taxa_anual = SELIC_ATUAL * (pct/100) if pct else SELIC_ATUAL
        except:
            taxa_anual = SELIC_ATUAL
    else:
        try:
            taxa_anual = float(''.join(c for c in taxa_str_lower if c.isdigit() or c == '.'))
        except:
            taxa_anual = 0

    valor_futuro = investido * ((1 + taxa_anual/100) ** anos_restantes) if anos_restantes > 0 else investido
    rendimento_estimado = valor_futuro - investido
    rentab_pct = (valor_futuro / investido - 1) * 100 if investido else 0

    return jsonify({
        'investido': round(investido, 2),
        'valor_futuro': round(valor_futuro, 2),
        'rendimento_estimado': round(rendimento_estimado, 2),
        'rentabilidade_pct': round(rentab_pct, 2),
        'taxa_anual_estimada': round(taxa_anual, 2),
        'dias_restantes': dias_totais,
        'anos_restantes': round(anos_restantes, 2),
        'cdi_referencia': CDI_ATUAL,
        'ipca_referencia': IPCA_ATUAL,
    })

@app.route('/api/cotacao-dolar', methods=['GET'])
def cotacao_dolar():
    """Retorna a cotação atual do dólar via yfinance."""
    try:
        t = yf.Ticker('USDBRL=X')
        info = t.fast_info
        preco = getattr(info, 'last_price', None) or getattr(info, 'regular_market_price', None)
        if preco and preco > 0:
            return jsonify({'brl': round(float(preco), 4)})
    except Exception as e:
        print(f"  ⚠ Erro ao buscar dólar: {e}")
    return jsonify({'brl': None})

@app.route('/api/dy/<string:ticker>', methods=['GET'])
def buscar_dy_ticker(ticker):
    """Busca o DY atual de um ticker via yfinance."""
    conn = get_db()
    ativo = conn.execute('SELECT tipo FROM ativos WHERE ticker=?', (ticker.upper(),)).fetchone()
    tipo = ativo['tipo'] if ativo else ''
    conn.close()
    dy = buscar_dy(ticker, tipo)
    return jsonify({'ticker': ticker.upper(), 'dy': dy})

@app.route('/api/snapshots/salvar', methods=['POST'])
def forcar_snapshot():
    salvar_snapshot()
    return jsonify({'ok': True})

# ── ROTAS: APORTES ────────────────────────────────────────────────────────────
@app.route('/api/aportes', methods=['GET'])
def listar_aportes():
    conn = get_db()
    rows = conn.execute('SELECT * FROM aportes ORDER BY data DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/aportes', methods=['POST'])
def criar_aporte():
    d = request.json
    conn = get_db()
    conn.execute(
        'INSERT INTO aportes (data, valor, descricao, origem) VALUES (?,?,?,?)',
        (d['data'], float(d['valor']), d.get('descricao',''), d.get('origem','manual'))
    )
    conn.commit()
    id_ = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    row = conn.execute('SELECT * FROM aportes WHERE id=?', (id_,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/aportes/<int:id>', methods=['PUT'])
def atualizar_aporte(id):
    d = request.json
    conn = get_db()
    conn.execute(
        'UPDATE aportes SET data=?, valor=?, descricao=? WHERE id=?',
        (d['data'], float(d['valor']), d.get('descricao',''), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM aportes WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/api/aportes/<int:id>', methods=['DELETE'])
def deletar_aporte(id):
    conn = get_db()
    conn.execute('DELETE FROM aportes WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/aportes/mes/<string:mes>', methods=['GET'])
def aportes_do_mes(mes):
    """Retorna total aportado em um mês (formato YYYY-MM)."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM aportes WHERE strftime('%Y-%m', data)=? ORDER BY data DESC", (mes,)
    ).fetchall()
    total = sum(r['valor'] for r in rows)
    conn.close()
    return jsonify({'mes': mes, 'total': round(total,2), 'aportes': [dict(r) for r in rows]})

# ── ROTAS: BACKUP / RESTAURAR ─────────────────────────────────────────────────
@app.route('/api/backup', methods=['GET'])
def backup():
    conn = get_db()
    ativos    = [dict(r) for r in conn.execute('SELECT * FROM ativos').fetchall()]
    proventos = [dict(r) for r in conn.execute('SELECT * FROM proventos').fetchall()]
    aportes   = [dict(r) for r in conn.execute('SELECT * FROM aportes').fetchall()]
    conn.close()
    return jsonify({'ativos': ativos, 'proventos': proventos, 'aportes': aportes, 'exportado': datetime.now().isoformat()})

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
    if 'aportes' in d:
        conn.execute('DELETE FROM aportes')
        for a in d['aportes']:
            conn.execute('INSERT INTO aportes (data,valor,descricao,origem) VALUES (?,?,?,?)',
                (a['data'], a['valor'], a.get('descricao',''), a.get('origem','manual')))
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

    salvar_snapshot()
    print("\n" + "="*45)
    print("  💹 Carteira Financeira rodando!")
    print("  Acesse: http://localhost:5000")
    print("  Para parar: pressione Ctrl+C")
    print("="*45 + "\n")
    app.run(debug=False, port=5000)
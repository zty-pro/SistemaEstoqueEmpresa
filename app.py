import os
import csv
import io
from flask import Flask, render_template_string, request, redirect, url_for, session, Response, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_para_sessoes_estoque_123")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Gestão de Estoque</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .login-card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 380px; }
        h2 { color: #1a73e8; margin-top: 0; text-align: center; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; font-size: 13px; }
        input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-size: 14px; }
        button { width: 100%; padding: 12px; background-color: #1a73e8; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 15px; margin-top: 10px; }
        button:hover { background-color: #1557b0; }
        .alert-error { background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 15px; text-align: center; font-size: 14px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 Acesso ao Sistema</h2>
        
        {% if erro %}
            <div class="alert-error">{{ erro }}</div>
        {% endif %}

        <form action="/login" method="POST">
            <div class="form-group">
                <label for="email">E-mail do Usuário:</label>
                <input type="email" id="email" name="email" required placeholder="admin@empresa.com">
            </div>
            <div class="form-group">
                <label for="senha">Senha:</label>
                <input type="password" id="senha" name="senha" required placeholder="******">
            </div>
            <button type="submit">Entrar no Sistema</button>
        </form>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Gestão de Estoque</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 950px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header-user { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eef3fc; padding-bottom: 10px; margin-bottom: 20px; }
        .user-info { font-size: 14px; color: #555; }
        .btn-logout { background: #dc3545; color: white; padding: 6px 12px; text-decoration: none; border-radius: 5px; font-size: 13px; font-weight: bold; }
        .btn-logout:hover { background: #bd2130; }
        h1 { color: #1a73e8; margin-top: 0; }
        .card { background: #eef3fc; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .card h3 { margin: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; vertical-align: middle; }
        th { background-color: #1a73e8; color: white; }
        tr:hover { background-color: #f1f1f1; }
        .grid-forms { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        @media (max-width: 768px) { .grid-forms { grid-template-columns: 1fr; } }
        .box-form { background: #fafafa; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }
        .box-form h3 { margin-top: 0; color: #1a73e8; }
        .form-group { margin-bottom: 12px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; font-size: 13px; }
        input, select, button { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-size: 14px; }
        button.btn-venda { background-color: #28a745; color: white; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button.btn-venda:hover { background-color: #218838; }
        button.btn-cadastrar { background-color: #1a73e8; color: white; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button.btn-cadastrar:hover { background-color: #1557b0; }
        .btn-excel { background-color: #17a2b8; color: white; text-decoration: none; padding: 8px 14px; border-radius: 5px; font-size: 13px; font-weight: bold; display: inline-block; margin-right: 5px; }
        .btn-excel:hover { background-color: #138496; }
        .btn-pdf { background-color: #ffc107; color: #333; text-decoration: none; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .btn-pdf:hover { background-color: #e0a800; }
        .nav-lojas { margin-bottom: 20px; }
        .nav-lojas a { text-decoration: none; padding: 8px 16px; background: #6c757d; color: white; border-radius: 5px; margin-right: 5px; display: inline-block; margin-bottom: 5px; }
        .nav-lojas a.active { background: #1a73e8; font-weight: bold; }
        .empty-msg { text-align: center; color: #777; padding: 20px; font-style: italic; }
        .chart-box { background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 25px; }
        .excel-actions { background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        
        .form-ajuste-qtd { display: flex; gap: 5px; align-items: center; }
        .input-qtd-ajuste { width: 70px !important; padding: 5px !important; font-size: 13px !important; text-align: center; }
        .btn-salvar-qtd { width: auto !important; padding: 5px 10px !important; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 12px; font-weight: bold; cursor: pointer; }
        .btn-salvar-qtd:hover { background: #5a6268; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-user">
            <div class="user-info">
                👤 Olá, <strong>{{ usuario_nome }}</strong> | Cargo: <strong>{{ usuario_cargo|upper }}</strong>
            </div>
            <a href="/logout" class="btn-logout">Sair do Sistema</a>
        </div>

        <h1>📦 Sistema Unificado de Estoque & Caixa</h1>
        
        <div class="nav-lojas">
            <strong>Selecionar Loja:</strong><br><br>
            {% for l in lojas %}
                <a href="/?loja_id={{ l.real_id }}" class="{% if l.real_id|string == loja_atual_id|string %}active{% endif %}">
                    {{ l.get('nome', 'Loja') }} ({{ l.get('cnpj', 'N/A') }})
                </a>
            {% endfor %}
        </div>

        <div class="card">
            <div>
                <h3>{{ loja_atual.get('nome', 'Loja') }}</h3>
                <small>CNPJ: {{ loja_atual.get('cnpj', 'N/A') }}</small>
            </div>
            <div>
                <h2>Saldo em Caixa: <span style="color: #28a745;">R$ {{ "%.2f"|format(loja_atual.get('saldo_caixa', 0)|float) }}</span></h2>
            </div>
        </div>

        <!-- EXPORTAÇÃO E IMPORTAÇÃO -->
        <div class="excel-actions">
            <div>
                <strong>Gerir Produtos por Planilha:</strong><br>
                <small>Exporte ou importe dados em massa (CSV).</small>
            </div>
            <div>
                <a href="/exportar_estoque?loja_id={{ loja_atual_id }}" class="btn-excel">📥 Exportar Estoque (CSV)</a>
            </div>
        </div>

        <div class="box-form" style="margin-bottom: 25px;">
            <h3>📤 Importar Produtos via Planilha (CSV)</h3>
            <form action="/importar_estoque" method="POST" enctype="multipart/form-data" style="display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap;">
                <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
                <div style="flex: 1; min-width: 250px;">
                    <label for="arquivo_csv">Selecione o arquivo CSV (Colunas: codigo, nome, preco, quantidade):</label>
                    <input type="file" id="arquivo_csv" name="arquivo_csv" accept=".csv" required>
                </div>
                <div>
                    <button type="submit" class="btn-cadastrar" style="margin-top: 0;">Importar Produtos</button>
                </div>
            </form>
        </div>

        <!-- RELATÓRIO E GRÁFICO -->
        <div class="chart-box">
            <h3>📊 Relatório de Desempenho de Vendas</h3>
            {% if grafico_labels and grafico_dados %}
                <canvas id="vendasChart" style="max-height: 250px;"></canvas>
                <script>
                    const ctx = document.getElementById('vendasChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: {{ grafico_labels|tojson }},
                            datasets: [{
                                label: 'Total Vendido (R$)',
                                data: {{ grafico_dados|tojson }},
                                backgroundColor: '#1a73e8',
                                borderRadius: 5
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: { legend: { display: false } },
                            scales: { y: { beginAtZero: true } }
                        }
                    });
                </script>
            {% else %}
                <div class="empty-msg">Nenhuma venda registrada nesta loja ainda para gerar o gráfico.</div>
            {% endif %}
        </div>

        <!-- HISTÓRICO RECENTE DE VENDAS -->
        <h2>📜 Histórico Recente de Vendas</h2>
        {% if ultimas_vendas %}
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Produto</th>
                    <th>Qtd</th>
                    <th>Total (R$)</th>
                    <th>Data/Hora</th>
                    <th>Ação</th>
                </tr>
            </thead>
            <tbody>
                {% for v in ultimas_vendas %}
                <tr>
                    <td>#{{ v.get('id') }}</td>
                    <td>{{ v.get('produto_nome') }}</td>
                    <td>{{ v.get('quantidade') }} un</td>
                    <td>R$ {{ "%.2f"|format(v.get('valor_total', 0)|float) }}</td>
                    <td>{{ v.get('data_venda') }}</td>
                    <td><a href="/comprovante_pdf/{{ v.get('id') }}" target="_blank" class="btn-pdf">📄 Baixar PDF</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
            <div class="empty-msg">Nenhuma venda efetuada recentemente.</div>
        {% endif %}

        <h2>Produtos em Estoque</h2>
        {% if produtos %}
        <table>
            <thead>
                <tr>
                    <th>Código</th>
                    <th>Nome do Produto</th>
                    <th>Preço (R$)</th>
                    <th>Quantidade em Estoque</th>
                </tr>
            </thead>
            <tbody>
                {% for p in produtos %}
                {% set p_cod = p.get('codigo', p.get('id', '')) %}
                <tr>
                    <td><strong>{{ p_cod }}</strong></td>
                    <td>{{ p.get('nome', '') }}</td>
                    <td>R$ {{ "%.2f"|format(p.get('preco', 0)|float) }}</td>
                    <td>
                        <form action="/editar_estoque" method="POST" class="form-ajuste-qtd">
                            <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
                            <input type="hidden" name="produto_codigo" value="{{ p_cod }}">
                            <input type="number" name="nova_quantidade" value="{{ p.get('quantidade', 0) }}" min="0" class="input-qtd-ajuste" required>
                            <button type="submit" class="btn-salvar-qtd" title="Atualizar quantidade manual">✏️ Salvar</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
            <div class="empty-msg">Nenhum produto cadastrado para esta loja ainda. Utilize o formulário abaixo ou importe uma planilha!</div>
        {% endif %}

        <div class="grid-forms">
            <!-- FORMULÁRIO DE VENDA -->
            <div class="box-form">
                <h3>🛒 Registrar Nova Venda</h3>
                <form action="/vender" method="POST">
                    <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
                    
                    <div class="form-group">
                        <label for="produto_codigo">Selecione o Produto:</label>
                        <select name="produto_codigo" id="produto_codigo" required {% if not produtos %}disabled{% endif %}>
                            {% if produtos %}
                                {% for p in produtos %}
                                    {% set p_cod = p.get('codigo', p.get('id', '')) %}
                                    <option value="{{ p_cod }}">{{ p_cod }} - {{ p.get('nome', '') }} (R$ {{ "%.2f"|format(p.get('preco', 0)|float) }}) - Restam {{ p.get('quantidade', 0) }} un</option>
                                {% endfor %}
                            {% else %}
                                <option>Cadastre um produto primeiro...</option>
                            {% endif %}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="quantidade">Quantidade a Vender:</label>
                        <input type="number" id="quantidade" name="quantidade" min="1" value="1" required {% if not produtos %}disabled{% endif %}>
                    </div>

                    <button type="submit" class="btn-venda" {% if not produtos %}disabled{% endif %}>Confirmar Venda e Dar Baixa</button>
                </form>
            </div>

            <!-- FORMULÁRIO DE CADASTRO DE NOVO PRODUTO -->
            <div class="box-form">
                <h3>➕ Cadastrar Novo Produto</h3>
                <form action="/cadastrar_produto" method="POST">
                    <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
                    
                    <div class="form-group">
                        <label for="cad_codigo">Código do Produto (ex: P001):</label>
                        <input type="text" id="cad_codigo" name="codigo" required placeholder="P001">
                    </div>

                    <div class="form-group">
                        <label for="cad_nome">Nome do Produto:</label>
                        <input type="text" id="cad_nome" name="nome" required placeholder="Ex: Camiseta P, Suplemento X">
                    </div>

                    <div class="form-group">
                        <label for="cad_preco">Preço de Venda (R$):</label>
                        <input type="number" step="0.01" id="cad_preco" name="preco" required placeholder="49.90">
                    </div>

                    <div class="form-group">
                        <label for="cad_qtd">Quantidade Inicial em Estoque:</label>
                        <input type="number" id="cad_qtd" name="quantidade" min="0" value="10" required>
                    </div>

                    <button type="submit" class="btn-cadastrar">Cadastrar Produto no Banco</button>
                </form>
            </div>
        </div>

        <!-- CADASTRAR NOVA LOJA -->
        <div class="box-form" style="margin-top: 20px;">
            <h3>🏢 Cadastrar Nova Loja / Filial</h3>
            <form action="/cadastrar_loja" method="POST" style="display: flex; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <label for="loja_nome">Nome da Loja:</label>
                    <input type="text" id="loja_nome" name="nome" required placeholder="Ex: Filial Centro">
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <label for="loja_cnpj">CNPJ:</label>
                    <input type="text" id="loja_cnpj" name="cnpj" required placeholder="00.000.000/0001-00">
                </div>
                <div style="width: 100%;">
                    <button type="submit" class="btn-cadastrar">Cadastrar Nova Loja</button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT * FROM usuarios WHERE email = %s AND senha = %s;", (email, senha))
            user = cur.fetchone()
        except Exception:
            user = None
            
        cur.close()
        conn.close()
        
        if user:
            session["usuario_id"] = user.get("id")
            session["usuario_nome"] = user.get("nome", "Usuário")
            session["usuario_cargo"] = user.get("cargo", "admin")
            session["loja_id"] = user.get("loja_id")
            return redirect(url_for("index"))
        else:
            return render_template_string(LOGIN_TEMPLATE, erro="E-mail ou senha incorretos.")
            
    return render_template_string(LOGIN_TEMPLATE)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    loja_id_param = request.args.get("loja_id")
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM lojas;")
    lojas = cur.fetchall()
    
    if not lojas:
        cur.close()
        conn.close()
        return "Nenhuma loja cadastrada.", 404

    for idx, l in enumerate(lojas):
        l['real_id'] = str(l.get('loja_id', l.get('id', idx + 1)))

    loja_atual = None
    if loja_id_param:
        for l in lojas:
            if str(l['real_id']) == str(loja_id_param):
                loja_atual = l
                break
                
    if not loja_atual:
        loja_atual = lojas[0]
        
    loja_atual_id = str(loja_atual['real_id'])
    
    # Recalcula e sincroniza o saldo em caixa direto do somatório de vendas
    try:
        cur.execute("SELECT COALESCE(SUM(valor_total), 0) as total FROM vendas WHERE loja_id::text = %s;", (loja_atual_id,))
        res_caixa = cur.fetchone()
        if res_caixa:
            loja_atual['saldo_caixa'] = float(res_caixa['total'])
    except Exception:
        pass
    
    cur.execute("SELECT * FROM estoque;")
    todos_produtos = cur.fetchall()
    produtos = []
    for p in todos_produtos:
        p_loja = str(p.get('loja_id', ''))
        if not p_loja or p_loja == loja_atual_id or p_loja == 'None':
            produtos.append(p)

    grafico_labels = []
    grafico_dados = []
    try:
        cur.execute("""
            SELECT produto_nome, SUM(valor_total) as total 
            FROM vendas 
            WHERE loja_id::text = %s 
            GROUP BY produto_nome 
            ORDER BY total DESC 
            LIMIT 5;
        """, (loja_atual_id,))
        vendas_res = cur.fetchall()
        for v in vendas_res:
            grafico_labels.append(v['produto_nome'])
            grafico_dados.append(float(v['total']))
    except Exception:
        pass

    ultimas_vendas = []
    try:
        cur.execute("""
            SELECT id, produto_nome, quantidade, valor_total, data_venda 
            FROM vendas 
            WHERE loja_id::text = %s
            ORDER BY id DESC 
            LIMIT 10;
        """, (loja_atual_id,))
        ultimas_vendas = cur.fetchall()
    except Exception:
        pass

    cur.close()
    conn.close()
    
    return render_template_string(
        HTML_TEMPLATE, 
        lojas=lojas, 
        loja_atual=loja_atual, 
        loja_atual_id=loja_atual_id, 
        produtos=produtos,
        grafico_labels=grafico_labels,
        grafico_dados=grafico_dados,
        ultimas_vendas=ultimas_vendas,
        usuario_nome=session.get("usuario_nome"),
        usuario_cargo=session.get("usuario_cargo")
    )

@app.route("/editar_estoque", methods=["POST"])
def editar_estoque():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    loja_id = request.form.get("loja_id")
    codigo = request.form.get("produto_codigo")
    nova_qtd = request.form.get("nova_quantidade", type=int)
    
    if codigo and nova_qtd is not None and nova_qtd >= 0:
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("UPDATE estoque SET quantidade = %s WHERE codigo = %s;", (nova_qtd, str(codigo)))
            conn.commit()
        except Exception:
            conn.rollback()
            if str(codigo).isdigit():
                try:
                    cur.execute("UPDATE estoque SET quantidade = %s WHERE id = %s;", (nova_qtd, int(codigo)))
                    conn.commit()
                except Exception:
                    conn.rollback()
                    
        cur.close()
        conn.close()
        
    return redirect(url_for("index", loja_id=loja_id))

@app.route("/vender", methods=["POST"])
def vender():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    loja_id = request.form.get("loja_id")
    codigo = request.form.get("produto_codigo")
    qtd_venda = request.form.get("quantidade", type=int)
    
    if not codigo or not qtd_venda or qtd_venda <= 0:
        return redirect(url_for("index", loja_id=loja_id))
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM estoque WHERE codigo = %s;", (str(codigo),))
    prod = cur.fetchone()
    
    if not prod and str(codigo).isdigit():
        cur.execute("SELECT * FROM estoque WHERE id = %s;", (int(codigo),))
        prod = cur.fetchone()
    
    if prod and int(prod.get('quantidade', 0)) >= qtd_venda:
        novo_estoque = int(prod['quantidade']) - qtd_venda
        valor_total = float(prod['preco']) * qtd_venda
        
        try:
            if 'codigo' in prod and prod['codigo']:
                cur.execute("UPDATE estoque SET quantidade = %s WHERE codigo = %s;", (novo_estoque, str(prod['codigo'])))
            elif 'id' in prod and prod['id'] is not None:
                cur.execute("UPDATE estoque SET quantidade = %s WHERE id = %s;", (novo_estoque, prod['id']))
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            loja_id_num = int(loja_id) if loja_id and str(loja_id).isdigit() else 1
            try:
                cur.execute("UPDATE lojas SET saldo_caixa = COALESCE(saldo_caixa, 0) + %s WHERE loja_id = %s;", (valor_total, loja_id_num))
                conn.commit()
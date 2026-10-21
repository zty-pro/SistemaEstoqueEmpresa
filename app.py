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
        * { box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
            margin: 0; 
            padding: 20px; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
        }
        .login-card { 
            background: #ffffff; 
            padding: 40px 30px; 
            border-radius: 16px; 
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3); 
            width: 100%; 
            max-width: 400px; 
        }
        h2 { 
            color: #0f172a; 
            margin-top: 0; 
            margin-bottom: 24px;
            text-align: center; 
            font-size: 24px;
            font-weight: 700;
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-weight: 600; margin-bottom: 8px; font-size: 13px; color: #475569; }
        input { 
            width: 100%; 
            padding: 12px 16px; 
            border: 1px solid #cbd5e1; 
            border-radius: 8px; 
            font-size: 14px; 
            transition: all 0.2s ease;
            outline: none;
        }
        input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15); }
        button { 
            width: 100%; 
            padding: 12px; 
            background-color: #2563eb; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-weight: 600; 
            cursor: pointer; 
            font-size: 15px; 
            margin-top: 10px; 
            transition: background-color 0.2s;
        }
        button:hover { background-color: #1d4ed8; }
        .alert-error { 
            background-color: #fee2e2; 
            color: #991b1b; 
            padding: 12px; 
            border-radius: 8px; 
            margin-bottom: 20px; 
            text-align: center; 
            font-size: 13px; 
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 Painel de Acesso</h2>
        
        {% if erro %}
            <div class="alert-error">{{ erro }}</div>
        {% endif %}

        <form action="/login" method="POST">
            <div class="form-group">
                <label for="email">E-mail do Usuário</label>
                <input type="email" id="email" name="email" required placeholder="admin@empresa.com">
            </div>
            <div class="form-group">
                <label for="senha">Senha</label>
                <input type="password" id="senha" name="senha" required placeholder="••••••••">
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
    <title>Sistema de Gestão de Estoque & Caixa</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
            background-color: #f8fafc; 
            margin: 0; 
            padding: 30px 20px; 
            color: #1e293b; 
        }
        .container { 
            max-width: 1050px; 
            margin: 0 auto; 
            background: white; 
            padding: 35px; 
            border-radius: 16px; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); 
            border: 1px solid #e2e8f0;
        }
        .header-user { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-bottom: 1px solid #f1f5f9; 
            padding-bottom: 15px; 
            margin-bottom: 25px; 
        }
        .user-info { font-size: 14px; color: #64748b; }
        .user-info strong { color: #0f172a; }
        .btn-logout { 
            background: #f1f5f9; 
            color: #ef4444; 
            padding: 8px 16px; 
            text-decoration: none; 
            border-radius: 8px; 
            font-size: 13px; 
            font-weight: 600; 
            transition: all 0.2s;
        }
        .btn-logout:hover { background: #fee2e2; }
        h1 { color: #0f172a; margin-top: 0; font-size: 26px; font-weight: 700; margin-bottom: 20px;}
        h2 { color: #1e293b; font-size: 18px; font-weight: 600; margin-top: 30px; margin-bottom: 15px; }
        
        .card { 
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); 
            padding: 20px 25px; 
            border-radius: 12px; 
            margin-bottom: 25px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border: 1px solid #bbf7d0;
        }
        .card h3 { margin: 0; color: #166534; font-size: 18px; }
        .card small { color: #15803d; font-weight: 500; }
        .card h2 { margin: 0; color: #166534; font-size: 24px; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 25px; background: white; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; }
        th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #f1f5f9; vertical-align: middle; font-size: 14px; }
        th { background-color: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }
        tr:hover { background-color: #f8fafc; }
        
        .grid-forms { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; margin-top: 25px; }
        @media (max-width: 768px) { .grid-forms { grid-template-columns: 1fr; } }
        
        .box-form { background: #f8fafc; padding: 25px; border: 1px solid #e2e8f0; border-radius: 12px; }
        .box-form h3 { margin-top: 0; color: #0f172a; font-size: 16px; font-weight: 600; margin-bottom: 16px; }
        
        .form-group { margin-bottom: 16px; }
        label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.03em;}
        input, select, button { width: 100%; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 14px; background: white; outline: none; transition: all 0.2s; }
        input:focus, select:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15); }
        
        button.btn-venda { background-color: #16a34a; color: white; border: none; font-weight: 600; cursor: pointer; margin-top: 5px; }
        button.btn-venda:hover { background-color: #15803d; }
        button.btn-cadastrar { background-color: #2563eb; color: white; border: none; font-weight: 600; cursor: pointer; margin-top: 5px; }
        button.btn-cadastrar:hover { background-color: #1d4ed8; }
        
        .btn-excel { background-color: #0ea5e9; color: white; text-decoration: none; padding: 10px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; display: inline-block; transition: background 0.2s; }
        .btn-excel:hover { background-color: #0284c7; }
        
        .btn-pdf { background-color: #f59e0b; color: white; text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; transition: background 0.2s; }
        .btn-pdf:hover { background-color: #d97706; }
        
        .nav-lojas { margin-bottom: 25px; background: #f1f5f9; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; }
        .nav-lojas strong { color: #475569; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }
        .nav-lojas a { text-decoration: none; padding: 8px 16px; background: white; color: #475569; border-radius: 6px; margin-right: 8px; display: inline-block; margin-top: 8px; font-size: 13px; font-weight: 500; border: 1px solid #cbd5e1; transition: all 0.2s; }
        .nav-lojas a:hover { border-color: #94a3b8; }
        .nav-lojas a.active { background: #2563eb; color: white; border-color: #2563eb; font-weight: 600; }
        
        .empty-msg { text-align: center; color: #94a3b8; padding: 25px; font-style: italic; font-size: 14px; background: #f8fafc; border-radius: 8px; border: 1px dashed #cbd5e1; }
        .chart-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 25px; }
        .excel-actions { background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        
        .acoes-estoque { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .input-qtd-ajuste { width: 65px !important; padding: 6px !important; font-size: 13px !important; text-align: center; }
        .btn-salvar-qtd { width: auto !important; padding: 6px 10px !important; background: #64748b; color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }
        .btn-salvar-qtd:hover { background: #475569; }
        .btn-remover-qtd { width: auto !important; padding: 6px 10px !important; background: #ea580c; color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; }
        .btn-remover-qtd:hover { background: #c2410c; }
        .btn-excluir-prod { width: auto !important; padding: 6px 10px !important; background: #ef4444; color: white; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-excluir-prod:hover { background: #dc2626; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-user">
            <div class="user-info">
                👋 Olá, <strong>{{ usuario_nome }}</strong> &bull; Cargo: <strong>{{ usuario_cargo|upper }}</strong>
            </div>
            <a href="/logout" class="btn-logout">Sair do Sistema</a>
        </div>

        <h1>📦 Painel de Controle: Estoque & Caixa</h1>
        
        <div class="nav-lojas">
            <strong>Selecionar Filial:</strong><br>
            {% for l in lojas %}
                <a href="/?loja_id={{ l.real_id }}" class="{% if l.real_id|string == loja_atual_id|string %}active{% endif %}">
                    📍 {{ l.get('nome', 'Loja') }} <span style="font-size: 11px; opacity: 0.8;">({{ l.get('cnpj', 'N/A') }})</span>
                </a>
            {% endfor %}
        </div>

        <div class="card">
            <div>
                <h3 style="margin-bottom: 4px;">{{ loja_atual.get('nome', 'Loja') }}</h3>
                <small>CNPJ: {{ loja_atual.get('cnpj', 'N/A') }}</small>
            </div>
            <div>
                <span style="font-size: 12px; font-weight: 600; color: #166534; text-transform: uppercase; display: block; text-align: right;">Saldo em Caixa</span>
                <h2>R$ {{ "%.2f"|format(loja_atual.get('saldo_caixa', 0)|float) }}</h2>
            </div>
        </div>

        <!-- EXPORTAÇÃO E IMPORTAÇÃO -->
        <div class="excel-actions">
            <div>
                <strong style="color: #0f172a; font-size: 15px;">Gestão de Dados via Planilha</strong><br>
                <small style="color: #64748b;">Faça backup exportando em CSV ou importe novos produtos em lote.</small>
            </div>
            <div>
                <a href="/exportar_estoque?loja_id={{ loja_atual_id }}" class="btn-excel">📥 Exportar Estoque (CSV)</a>
            </div>
        </div>

        <div class="box-form" style="margin-bottom: 25px;">
            <h3>📤 Importar Produtos via Planilha (CSV)</h3>
            <form action="/importar_estoque" method="POST" enctype="multipart/form-data" style="display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap;">
                <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
                <div style="flex: 1; min-width: 250px;">
                    <label for="arquivo_csv">Arquivo CSV (Colunas: codigo, nome, preco, quantidade)</label>
                    <input type="file" id="arquivo_csv" name="arquivo_csv" accept=".csv" required style="padding: 8px;">
                </div>
                <div>
                    <button type="submit" class="btn-cadastrar" style="margin-top: 0; padding: 10px 20px;">Processar Importação</button>
                </div>
            </form>
        </div>

        <!-- RELATÓRIO E GRÁFICO -->
        <div class="chart-box">
            <h3 style="margin-top: 0; color: #0f172a; font-size: 16px; font-weight: 600; margin-bottom: 15px;">📊 Desempenho de Vendas (Top Produtos)</h3>
            {% if grafico_labels and grafico_dados %}
                <canvas id="vendasChart" style="max-height: 240px;"></canvas>
                <script>
                    const ctx = document.getElementById('vendasChart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: {{ grafico_labels|tojson }},
                            datasets: [{
                                label: 'Total Vendido (R$)',
                                data: {{ grafico_dados|tojson }},
                                backgroundColor: '#2563eb',
                                borderRadius: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: { legend: { display: false } },
                            scales: { y: { beginAtZero: true, grid: { color: '#f1f5f9' } }, x: { grid: { display: false } } }
                        }
                    });
                </script>
            {% else %}
                <div class="empty-msg">Nenhuma venda registrada nesta filial para gerar gráficos estatísticos ainda.</div>
            {% endif %}
        </div>

        <!-- HISTÓRICO RECENTE DE VENDAS -->
        <h2>📜 Histórico Recente de Transações</h2>
        {% if ultimas_vendas %}
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Produto</th>
                    <th>Qtd</th>
                    <th>Total</th>
                    <th>Data/Hora</th>
                    <th>Comprovante</th>
                </tr>
            </thead>
            <tbody>
                {% for v in ultimas_vendas %}
                <tr>
                    <td><strong>#{{ v.get('id') }}</strong></td>
                    <td>{{ v.get('produto_nome') }}</td>
                    <td>{{ v.get('quantidade') }} un</td>
                    <td><strong>R$ {{ "%.2f"|format(v.get('valor_total', 0)|float) }}</strong></td>
                    <td style="color: #64748b; font-size: 13px;">{{ v.get('data_venda') }}</td>
                    <td><a href="/comprovante_pdf/{{ v.get('id') }}" target="_blank" class="btn-pdf">📄 PDF</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
            <div class="empty-msg">Nenhuma venda efetuada recentemente.</div>
        {% endif %}

        <h2>📦 Produtos em Estoque</h2>
        {% if produtos %}
        <table>
            <thead>
                <tr>
                    <th>Código</th>
                    <th>Nome do Produto</th>
                    <th>Preço Unitário</th>
                    <th>Gerenciamento de Estoque</th>
                </tr>
            </thead>
            <tbody>
                {% for p in produtos %}
                {% set p_cod = p.get('codigo', p.get('id', '')) %}
                <tr>
                    <td><span style="background: #f1f5f9; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 13px;">{{ p_cod }}</span></td>
                    <td><strong>{{ p.get('nome', '') }}</strong></td>
                    <td>R$ {{ "%.2f"|format(p.get('preco', 0)|float) }}</td>
                    <td>
                        <div class="acoes-estoque">
                            <!-- Ajuste Manual -->
                            <form action="/editar_estoque" method="POST" style="display: flex; gap: 4px; align-items: center; margin: 0;">
                                <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
                                <input type="hidden" name="produto_codigo" value="{{ p_cod }}">
                                <input type="number" name="nova_quantidade" value="{{ p.get('quantidade', 0) }}" min="0" class="input-qtd-ajuste" required title="Estoque exato">
                                <button type="submit" class="btn-salvar-qtd" title="Atualizar estoque total">✏️ Salvar</button>
                            </form>
                            
                            <!-- Baixa Rápida -->
                            <form action="/remover_quantidade" method="POST" style="display: flex; gap: 4px; align-items: center; margin: 0;">
                                <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
                                <input type="hidden" name="codigo" value="{{ p_cod }}">
                                <input type="number" name="qtd_remover" value="1" min="1" max="{{ p.get('quantidade', 0) }}" class="input-qtd-ajuste" required title="Qtd para baixar">
                                <button type="submit" class="btn-remover-qtd" title="Baixa rápida de quantidade">➖ Baixar</button>
                            </form>

                            <!-- Excluir -->
                            <a href="/excluir_produto?codigo={{ p_cod }}&loja_id={{ loja_atual_id }}" class="btn-excluir-prod" onclick="return confirm('Deseja realmente excluir este produto desta filial?');" title="Excluir produto">🗑️ Excluir</a>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
            <div class="empty-msg">Nenhum produto cadastrado para esta filial. Utilize o formulário abaixo ou importe uma planilha!</div>
        {% endif %}

        <div class="grid-forms">
            <!-- FORMULÁRIO DE VENDA -->
            <div class="box-form">
                <h3>🛒 Registrar Nova Venda</h3>
                <form action="/vender" method="POST">
                    <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
                    
                    <div class="form-group">
                        <label for="produto_codigo">Selecione o Produto</label>
                        <select name="produto_codigo" id="produto_codigo" required {% if not produtos %}disabled{% endif %}>
                            {% if produtos %}
                                {% for p in produtos %}
                                    {% set p_cod = p.get('codigo', p.get('id', '')) %}
                                    <option value="{{ p_cod }}">{{ p_cod }} - {{ p.get('nome', '') }} (R$ {{ "%.2f"|format(p.get('preco', 0)|float) }}) [Estoque: {{ p.get('quantidade', 0) }}]</option>
                                {% endfor %}
                            {% else %}
                                <option>Cadastre um produto primeiro...</option>
                            {% endif %}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="quantidade">Quantidade a Vender</label>
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
                        <label for="cad_codigo">Código do Produto</label>
                        <input type="text" id="cad_codigo" name="codigo" required placeholder="Ex: P001">
                    </div>

                    <div class="form-group">
                        <label for="cad_nome">Nome do Produto</label>
                        <input type="text" id="cad_nome" name="nome" required placeholder="Ex: Camiseta Básica M">
                    </div>

                    <div class="form-group">
                        <label for="cad_preco">Preço de Venda (R$)</label>
                        <input type="number" step="0.01" id="cad_preco" name="preco" required placeholder="49.90">
                    </div>

                    <div class="form-group">
                        <label for="cad_qtd">Quantidade Inicial</label>
                        <input type="number" id="cad_qtd" name="quantidade" min="0" value="10" required>
                    </div>

                    <button type="submit" class="btn-cadastrar">Adicionar ao Estoque</button>
                </form>
            </div>
        </div>

        <!-- CADASTRAR NOVA LOJA -->
        <div class="box-form" style="margin-top: 25px;">
            <h3>🏢 Cadastrar Nova Loja / Filial</h3>
            <form action="/cadastrar_loja" method="POST" style="display: flex; gap: 15px; flex-wrap: wrap; align-items: flex-end;">
                <div style="flex: 1; min-width: 220px; margin-bottom: 0;">
                    <label for="loja_nome">Nome da Filial</label>
                    <input type="text" id="loja_nome" name="nome" required placeholder="Ex: Loja Centro">
                </div>
                <div style="flex: 1; min-width: 220px; margin-bottom: 0;">
                    <label for="loja_cnpj">CNPJ</label>
                    <input type="text" id="loja_cnpj" name="cnpj" required placeholder="00.000.000/0001-00">
                </div>
                <div>
                    <button type="submit" class="btn-cadastrar" style="margin-top: 0; padding: 10px 20px;">Cadastrar Filial</button>
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
    
    try:
        cur.execute("SELECT COALESCE(SUM(valor_total), 0) as total FROM vendas WHERE loja_id::text = %s;", (loja_atual_id,))
        res_caixa = cur.fetchone()
        if res_caixa:
            loja_atual['saldo_caixa'] = float(res_caixa['total'])
    except Exception:
        pass
    
    produtos = []
    try:
        cur.execute("SELECT * FROM estoque WHERE loja_id::text = %s;", (loja_atual_id,))
        produtos = cur.fetchall()
    except Exception:
        conn.rollback()
        cur.execute("SELECT * FROM estoque;")
        todos = cur.fetchall()
        produtos = [p for p in todos if str(p.get('loja_id', '')) == loja_atual_id]

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
            cur.execute("UPDATE estoque SET quantidade = %s WHERE codigo = %s AND loja_id::text = %s;", (nova_qtd, str(codigo), str(loja_id)))
            conn.commit()
        except Exception:
            conn.rollback()
            try:
                cur.execute("UPDATE estoque SET quantidade = %s WHERE codigo = %s;", (nova_qtd, str(codigo)))
                conn.commit()
            except Exception:
                conn.rollback()
                
        cur.close()
        conn.close()
        
    return redirect(url_for("index", loja_id=loja_id))

@app.route("/remover_quantidade", methods=["POST"])
def remover_quantidade():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    loja_id = request.form.get("loja_id")
    codigo = request.form.get("codigo")
    qtd_remover = request.form.get("qtd_remover", type=int)
    
    if codigo and qtd_remover and qtd_remover > 0:
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT quantidade FROM estoque WHERE codigo = %s AND loja_id::text = %s;", (str(codigo), str(loja_id)))
            prod = cur.fetchone()
            
            if not prod:
                cur.execute("SELECT quantidade FROM estoque WHERE codigo = %s;", (str(codigo),))
                prod = cur.fetchone()
                
            if prod:
                qtd_atual = int(prod.get('quantidade', 0))
                nova_qtd = max(0, qtd_atual - qtd_remover)
                
                cur.execute("UPDATE estoque SET quantidade = %s WHERE codigo = %s AND loja_id::text = %s;", (nova_qtd, str(codigo), str(loja_id)))
                conn.commit()
        except Exception:
            conn.rollback()
        finally:
            cur.close()
            conn.close()
            
    return redirect(url_for("index", loja_id=loja_id))

@app.route("/excluir_produto")
def excluir_produto():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    loja_id = request.args.get("loja_id")
    codigo = request.args.get("codigo")
    
    if codigo and loja_id:
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("DELETE FROM estoque WHERE codigo = %s AND loja_id::text = %s;", (str(codigo), str(loja_id)))
            conn.commit()
        except Exception:
            conn.rollback()
            try:
                cur.execute("DELETE FROM estoque WHERE codigo = %s;", (str(codigo),))
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
    
    cur.execute("SELECT * FROM estoque WHERE codigo = %s AND loja_id::text = %s;", (str(codigo), str(loja_id)))
    prod = cur.fetchone()
    
    if not prod:
        cur.execute("SELECT * FROM estoque WHERE codigo = %s;", (str(codigo),))
        prod = cur.fetchone()
    
    if prod and int(prod.get('quantidade', 0)) >= qtd_venda:
        novo_estoque = int(prod['quantidade']) - qtd_venda
        valor_total = float(prod['preco']) * qtd_venda
        
        try:
            cur.execute("UPDATE estoque SET quantidade = %s WHERE codigo = %s AND loja_id::text = %s;", (novo_estoque, str(codigo), str(loja_id)))
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            loja_id_num = int(loja_id) if loja_id and str(loja_id).isdigit() else 1
            try:
                cur.execute("UPDATE lojas SET saldo_caixa = COALESCE(saldo_caixa, 0) + %s WHERE loja_id = %s;", (valor_total, loja_id_num))
                conn.commit()
            except Exception:
                conn.rollback()
                cur.execute("UPDATE lojas SET saldo_caixa = COALESCE(saldo_caixa, 0) + %s WHERE id = %s;", (valor_total, loja_id_num))
                conn.commit()
        except Exception:
            conn.rollback()

        try:
            loja_id_num = int(loja_id) if loja_id and str(loja_id).isdigit() else 1
            cur.execute(
                "INSERT INTO vendas (loja_id, produto_codigo, produto_nome, quantidade, valor_total) VALUES (%s, %s, %s, %s, %s);",
                (loja_id_num, str(codigo), prod.get('nome', 'Produto'), qtd_venda, valor_total)
            )
            conn.commit()
        except Exception:
            conn.rollback()
                
    cur.close()
    conn.close()
    
    return redirect(url_for("index", loja_id=loja_id))

@app.route("/cadastrar_produto", methods=["POST"])
def cadastrar_produto():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    loja_id = request.form.get("loja_id")
    codigo = request.form.get("codigo")
    nome = request.form.get("nome")
    preco = request.form.get("preco", type=float)
    quantidade = request.form.get("quantidade", type=int)
    
    if codigo and nome and preco is not None and quantidade is not None:
        conn = get_db_connection()
        cur = conn.cursor()
        
        loja_id_num = int(loja_id) if loja_id and str(loja_id).isdigit() else 1
        try:
            cur.execute(
                "INSERT INTO estoque (loja_id, codigo, nome, preco, quantidade) VALUES (%s, %s, %s, %s, %s);",
                (loja_id_num, codigo, nome, preco, quantidade)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            try:
                cur.execute(
                    "INSERT INTO estoque (codigo, nome, preco, quantidade) VALUES (%s, %s, %s, %s);",
                    (codigo, nome, preco, quantidade)
                )
                conn.commit()
            except Exception:
                conn.rollback()
            
        cur.close()
        conn.close()
        
    return redirect(url_for("index", loja_id=loja_id))

@app.route("/comprovante_pdf/<int:venda_id>")
def comprovante_pdf(venda_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM vendas WHERE id = %s;", (venda_id,))
    venda = cur.fetchone()
    
    if not venda:
        cur.close()
        conn.close()
        return "Comprovante não encontrado.", 404
        
    loja = None
    try:
        cur.execute("SELECT * FROM lojas WHERE loja_id = %s LIMIT 1;", (venda['loja_id'],))
        loja = cur.fetchone()
    except Exception:
        conn.rollback()
        try:
            cur.execute("SELECT * FROM lojas WHERE id = %s LIMIT 1;", (venda['loja_id'],))
            loja = cur.fetchone()
        except Exception:
            conn.rollback()
            
    cur.close()
    conn.close()
    
    loja_nome = loja.get('nome', 'Empresa / Loja') if loja else 'Sistema de Estoque'
    loja_cnpj = loja.get('cnpj', 'N/A') if loja else 'N/A'
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"COMPROVANTE DE VENDA")
    
    p.setFont("Helvetica", 11)
    p.drawString(50, height - 75, f"Loja: {loja_nome} | CNPJ: {loja_cnpj}")
    p.drawString(50, height - 95, f"Transação ID: #{venda['id']}")
    p.drawString(50, height - 115, f"Data e Hora: {venda['data_venda']}")
    
    p.setStrokeColorRGB(0.2, 0.4, 0.8)
    p.setLineWidth(1)
    p.line(50, height - 130, width - 50, height - 130)
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 160, "Item Adquirido:")
    
    p.setFont("Helvetica", 11)
    p.drawString(70, height - 185, f"Produto: {venda['produto_nome']} (Cód: {venda['produto_codigo']})")
    p.drawString(70, height - 205, f"Quantidade: {venda['quantidade']} unidade(s)")
    p.drawString(70, height - 225, f"Valor Total: R$ {float(venda['valor_total']):.2f}")
    
    p.line(50, height - 250, width - 50, height - 250)
    
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(50, height - 280, "Documento gerado eletronicamente pelo Sistema de Gestão de Estoque & Caixa.")
    p.drawString(50, height - 295, "Obrigado pela preferência!")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"comprovante_venda_{venda_id}.pdf", mimetype="application/pdf")

@app.route("/exportar_estoque")
def exportar_estoque():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    loja_id = request.args.get("loja_id")
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT codigo, nome, preco, quantidade FROM estoque WHERE loja_id::text = %s;", (str(loja_id),))
        produtos = cur.fetchall()
    except Exception:
        conn.rollback()
        cur.execute("SELECT codigo, nome, preco, quantidade FROM estoque;")
        produtos = cur.fetchall()
        
    cur.close()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['codigo', 'nome', 'preco', 'quantidade'])
    
    for p in produtos:
        writer.writerow([p.get('codigo'), p.get('nome'), p.get('preco'), p.get('quantidade')])
        
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=estoque_loja.csv"}
    )

@app.route("/importar_estoque", methods=["POST"])
def importar_estoque():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    loja_id = request.form.get("loja_id")
    arquivo = request.files.get("arquivo_csv")
    
    if arquivo and arquivo.filename.endswith('.csv'):
        stream = io.TextIOWrapper(arquivo.stream, encoding="utf-8")
        reader = csv.DictReader(stream)
        
        conn = get_db_connection()
        cur = conn.cursor()
        loja_id_num = int(loja_id) if loja_id and str(loja_id).isdigit() else 1
        
        for row in reader:
            codigo = row.get('codigo')
            nome = row.get('nome')
            preco = float(row.get('preco', 0))
            quantidade = int(row.get('quantidade', 0))
            
            if codigo and nome:
                try:
                    cur.execute(
                        "INSERT INTO estoque (loja_id, codigo, nome, preco, quantidade) VALUES (%s, %s, %s, %s, %s);",
                        (loja_id_num, codigo, nome, preco, quantidade)
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    try:
                        cur.execute(
                            "INSERT INTO estoque (codigo, nome, preco, quantidade) VALUES (%s, %s, %s, %s);",
                            (codigo, nome, preco, quantidade)
                        )
                        conn.commit()
                    except Exception:
                        conn.rollback()
                        
        cur.close()
        conn.close()
        
    return redirect(url_for("index", loja_id=loja_id))

@app.route("/cadastrar_loja", methods=["POST"])
def cadastrar_loja():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    nome = request.form.get("nome")
    cnpj = request.form.get("cnpj")
    
    if nome and cnpj:
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("INSERT INTO lojas (nome, cnpj, saldo_caixa) VALUES (%s, %s, 0);", (nome, cnpj))
            conn.commit()
        except Exception:
            conn.rollback()
            
        cur.close()
        conn.close()
        
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
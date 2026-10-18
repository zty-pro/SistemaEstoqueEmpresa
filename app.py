import os
from flask import Flask, render_template_string, request, redirect, url_for, session
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

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
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
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
        .nav-lojas { margin-bottom: 20px; }
        .nav-lojas a { text-decoration: none; padding: 8px 16px; background: #6c757d; color: white; border-radius: 5px; margin-right: 5px; display: inline-block; margin-bottom: 5px; }
        .nav-lojas a.active { background: #1a73e8; font-weight: bold; }
        .empty-msg { text-align: center; color: #777; padding: 20px; font-style: italic; }
        .chart-box { background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 25px; }
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
                {% set l_id = l.get('id', l.get('loja_id', loop.index0)) %}
                <a href="/?loja_id={{ l_id }}" class="{% if l_id|string == loja_atual_id|string %}active{% endif %}">
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

        <!-- MÓDULO DE RELATÓRIO E GRÁFICO -->
        <div class="chart-box">
            <h3>📊 Relatório de Desempenho de Vendas</h3>
            {% if grafico_labels and grafico_dados %}
                <canvas id="vendasChart" style="max-height: 300px;"></canvas>
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

        <h2>Produtos em Estoque</h2>
        {% if produtos %}
        <table>
            <thead>
                <tr>
                    <th>Código</th>
                    <th>Nome do Produto</th>
                    <th>Preço (R$)</th>
                    <th>Quantidade</th>
                </tr>
            </thead>
            <tbody>
                {% for p in produtos %}
                <tr>
                    <td><strong>{{ p.get('codigo', p.get('id', '')) }}</strong></td>
                    <td>{{ p.get('nome', '') }}</td>
                    <td>R$ {{ "%.2f"|format(p.get('preco', 0)|float) }}</td>
                    <td><span style="font-weight:bold; color: {% if p.get('quantidade', 0) < 10 %}#dc3545{% else %}#28a745{% endif %};">{{ p.get('quantidade', 0) }} un</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
            <div class="empty-msg">Nenhum produto cadastrado para esta loja ainda. Utilize o formulário abaixo para cadastrar!</div>
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
        
    primeira_loja = lojas[0]
    id_col = 'id' if 'id' in primeira_loja else ('loja_id' if 'loja_id' in primeira_loja else list(primeira_loja.keys())[0])
    
    loja_atual = None
    if loja_id_param:
        for l in lojas:
            if str(l.get(id_col)) == str(loja_id_param):
                loja_atual = l
                break
                
    if not loja_atual:
        loja_atual = lojas[0]
        
    loja_atual_id = loja_atual.get(id_col)
    
    # Busca produtos da loja
    try:
        cur.execute("SELECT * FROM estoque WHERE loja_id = %s;", (loja_atual_id,))
    except Exception:
        try:
            cur.execute("SELECT * FROM estoque;")
        except Exception:
            pass
            
    produtos = cur.fetchall() if 'produtos' in locals() and isinstance(produtos, list) else []
    if produtos and 'loja_id' in produtos[0]:
        produtos = [p for p in produtos if str(p.get('loja_id')) == str(loja_atual_id)]

    # Dados para o Gráfico de Vendas por Produto
    grafico_labels = []
    grafico_dados = []
    try:
        cur.execute("""
            SELECT produto_nome, SUM(valor_total) as total 
            FROM vendas 
            WHERE loja_id = %s 
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
        usuario_nome=session.get("usuario_nome"),
        usuario_cargo=session.get("usuario_cargo")
    )

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
    
    cur.execute("SELECT * FROM estoque WHERE codigo = %s;", (codigo,))
    prod = cur.fetchone()
    
    if prod and prod.get('quantidade', 0) >= qtd_venda:
        novo_estoque = prod['quantidade'] - qtd_venda
        valor_total = float(prod['preco']) * qtd_venda
        
        # 1. Atualiza Estoque
        if 'id' in prod:
            cur.execute("UPDATE estoque SET quantidade = %s WHERE id = %s;", (novo_estoque, prod['id']))
        else:
            cur.execute("UPDATE estoque SET quantidade = %s WHERE codigo = %s;", (novo_estoque, codigo))
        
        # 2. Atualiza Caixa
        try:
            cur.execute("SELECT * FROM lojas LIMIT 1;")
            exemplo_loja = cur.fetchone()
            loja_id_col = 'id' if 'id' in exemplo_loja else ('loja_id' if 'loja_id' in exemplo_loja else list(exemplo_loja.keys())[0])
            cur.execute(f"UPDATE lojas SET saldo_caixa = saldo_caixa + %s WHERE {loja_id_col} = %s;", (valor_total, loja_id))
        except Exception:
            pass

        # 3. Registra na tabela de Vendas para Relatórios
        try:
            cur.execute(
                "INSERT INTO vendas (loja_id, produto_codigo, produto_nome, quantidade, valor_total) VALUES (%s, %s, %s, %s, %s);",
                (loja_id, codigo, prod.get('nome', 'Produto'), qtd_venda, valor_total)
            )
        except Exception:
            pass
                
        conn.commit()
        
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
        
        try:
            cur.execute(
                "INSERT INTO estoque (loja_id, codigo, nome, preco, quantidade) VALUES (%s, %s, %s, %s, %s);",
                (loja_id, codigo, nome, preco, quantidade)
            )
        except Exception:
            try:
                cur.execute(
                    "INSERT INTO estoque (codigo, nome, preco, quantidade) VALUES (%s, %s, %s, %s);",
                    (codigo, nome, preco, quantidade)
                )
            except Exception:
                pass
            
        conn.commit()
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
            cur.execute(
                "INSERT INTO lojas (nome, cnpj, saldo_caixa) VALUES (%s, %s, 0.0);",
                (nome, cnpj)
            )
        except Exception:
            try:
                cur.execute(
                    "INSERT INTO lojas (nome, cnpj) VALUES (%s, %s);",
                    (nome, cnpj)
                )
            except Exception:
                pass
            
        conn.commit()
        cur.close()
        conn.close()
        
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
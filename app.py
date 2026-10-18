import os
from flask import Flask, render_template_string, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    """Garante que as tabelas existem no Supabase"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Cria a tabela de lojas caso não exista nenhuma
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lojas (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                cnpj VARCHAR(20) NOT NULL,
                saldo_caixa NUMERIC(12, 2) DEFAULT 0.00
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                loja_id INTEGER,
                codigo VARCHAR(50) NOT NULL,
                nome VARCHAR(150) NOT NULL,
                preco NUMERIC(12, 2) NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 0
            );
        """)
        
        # Verifica se há lojas cadastradas
        cur.execute("SELECT * FROM lojas;")
        lojas = cur.fetchall()
        if not lojas:
            cur.execute("INSERT INTO lojas (nome, cnpj, saldo_caixa) VALUES (%s, %s, %s);", 
                        ("Loja Matriz", "12.345.678/0001-01", 0.00))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Erro na inicialização: {e}")

init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Gestão de Estoque</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 950px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
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
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Sistema Unificado de Estoque & Caixa</h1>
        
        <div class="nav-lojas">
            <strong>Selecionar Loja:</strong><br><br>
            {% for l in lojas %}
                {% set l_id = l.get('id', l.get('loja_id', list(l.keys())[0])) %}
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

@app.route("/")
def index():
    loja_id_param = request.args.get("loja_id")
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Busca todas as colunas da tabela lojas sem depender de um nome fixo
    cur.execute("SELECT * FROM lojas;")
    lojas = cur.fetchall()
    
    if not lojas:
        cur.close()
        conn.close()
        return "Nenhuma loja encontrada.", 404
        
    primeira_loja = lojas[0]
    # Identifica dinamicamente a coluna de ID da loja
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
    
    # Busca produtos da loja atual
    try:
        cur.execute("SELECT * FROM produtos WHERE loja_id = %s;", (loja_atual_id,))
    except Exception:
        try:
            cur.execute("SELECT * FROM produtos;")
        except Exception:
            pass
            
    produtos = cur.fetchall() if 'produtos' in locals() and isinstance(produtos, list) else []
    # Garante filtragem em memória caso a coluna loja_id não exista exatamente
    if produtos and 'loja_id' in produtos[0]:
        produtos = [p for p in produtos if str(p.get('loja_id')) == str(loja_atual_id)]
        
    cur.close()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, lojas=lojas, loja_atual=loja_atual, loja_atual_id=loja_atual_id, produtos=produtos)

@app.route("/vender", methods=["POST"])
def vender():
    loja_id = request.form.get("loja_id")
    codigo = request.form.get("produto_codigo")
    qtd_venda = request.form.get("quantidade", type=int)
    
    if not codigo or not qtd_venda or qtd_venda <= 0:
        return redirect(url_for("index", loja_id=loja_id))
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM produtos WHERE codigo = %s;", (codigo,))
    prod = cur.fetchone()
    
    if
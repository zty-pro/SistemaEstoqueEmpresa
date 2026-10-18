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
                {% set l_id = l.get('id', l.get('loja_id', loop.index)) %}
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
    loja_id_param = request.args.get("loja_id", type=int)
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM lojas;")
    lojas = cur.fetchall()
    
    if not lojas:
        cur.close()
        conn.close()
        return "Nenhuma loja cadastrada no banco de dados.", 404
        
    primeira_loja = lojas[0]
    id_coluna = 'id' if 'id' in primeira_loja else ('loja_id' if 'loja_id' in primeira_loja else list(primeira_loja.keys())[0])
    
    loja_atual = None
    if loja_id_param:
        for l in lojas:
            if str(l.get(id_coluna)) == str(loja_id_param):
                loja_atual = l
                break
    
    if not loja_atual:
        loja_atual = lojas[0]
        
    loja_atual_id = loja_atual.get(id_coluna)
    
    cur.execute("SELECT * FROM produtos WHERE loja_id = %s ORDER BY id;", (loja_atual_id,))
    produtos = cur.fetchall()
    
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
    
    cur.execute("SELECT * FROM produtos WHERE codigo = %s AND loja_id = %s;", (codigo, loja_id))
    prod = cur.fetchone()
    
    if prod and prod.get('quantidade', 0) >= qtd_venda:
        novo_estoque = prod['quantidade'] - qtd_venda
        valor_total = float(prod['preco']) * qtd_venda
        
        cur.execute("UPDATE produtos SET quantidade = %s WHERE id = %s;", (novo_estoque, prod['id']))
        
        try:
            cur.execute("UPDATE lojas SET saldo_caixa = saldo_caixa + %s WHERE id = %s;", (valor_total, loja_id))
        except Exception:
            try:
                cur.execute("UPDATE lojas SET saldo_caixa = saldo_caixa + %s WHERE loja_id = %s;", (valor_total, loja_id))
            except Exception:
                pass
                
        conn.commit()
        
    cur.close()
    conn.close()
    
    return redirect(url_for("index", loja_id=loja_id))

@app.route("/cadastrar_produto", methods=["POST"])
def cadastrar_produto():
    loja_id = request.form.get("loja_id")
    codigo = request.form.get("codigo")
    nome = request.form.get("nome")
    preco = request.form.get("preco", type=float)
    quantidade = request.form.get("quantidade", type=int)
    
    if loja_id and codigo and nome and preco is not None and quantidade is not None:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO produtos (loja_id, codigo, nome, preco, quantidade) VALUES (%s, %s, %s, %s, %s);",
            (loja_id, codigo, nome, preco, quantidade)
        )
        conn.commit()
        cur.close()
        conn.close()
        
    return redirect(url_for("index", loja_id=loja_id))

@app.route("/cadastrar_loja", methods=["POST"])
def cadastrar_loja():
    nome = request.form.get("nome")
    cnpj = request.form.get("cnpj")
    
    if nome and cnpj:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO lojas (nome, cnpj, saldo_caixa) VALUES (%s, %s, 0.0);",
            (nome, cnpj)
        )
        conn.commit()
        cur.close()
        conn.close()
        
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
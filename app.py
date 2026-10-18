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
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h1 { color: #1a73e8; margin-top: 0; }
        .card { background: #eef3fc; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .card h3 { margin: 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #1a73e8; color: white; }
        tr:hover { background-color: #f1f1f1; }
        form { margin-top: 25px; background: #fafafa; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input, select, button { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; font-size: 14px; }
        button { background-color: #28a745; color: white; border: none; font-weight: bold; cursor: pointer; transition: background 0.3s; margin-top: 10px; }
        button:hover { background-color: #218838; }
        .nav-lojas { margin-bottom: 20px; }
        .nav-lojas a { text-decoration: none; padding: 8px 16px; background: #6c757d; color: white; border-radius: 5px; margin-right: 5px; display: inline-block; }
        .nav-lojas a.active { background: #1a73e8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Sistema de Estoque & Caixa</h1>
        
        <div class="nav-lojas">
            <strong>Selecionar Loja:</strong><br><br>
            {% for l in lojas %}
                <a href="/?loja_id={{ l.id }}" class="{% if l.id == loja_atual.id %}active{% endif %}">
                    {{ l.nome }} ({{ l.cnpj }})
                </a>
            {% endfor %}
        </div>

        <div class="card">
            <div>
                <h3>{{ loja_atual.nome }}</h3>
                <small>CNPJ: {{ loja_atual.cnpj }}</small>
            </div>
            <div>
                <h2>Saldo em Caixa: <span style="color: #28a745;">R$ {{ "%.2f"|format(loja_atual.saldo_caixa|float) }}</span></h2>
            </div>
        </div>

        <h2>Produtos em Estoque</h2>
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
                    <td><strong>{{ p.codigo }}</strong></td>
                    <td>{{ p.nome }}</td>
                    <td>R$ {{ "%.2f"|format(p.preco|float) }}</td>
                    <td><span style="font-weight:bold; color: {% if p.quantidade < 10 %}#dc3545{% else %}#333{% endif %};">{{ p.quantidade }} un</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <form action="/vender" method="POST">
            <h3>🛒 Registrar Nova Venda</h3>
            <input type="hidden" name="loja_id" value="{{ loja_atual.id }}">
            
            <div class="form-group">
                <label for="produto_codigo">Selecione o Produto:</label>
                <select name="produto_codigo" id="produto_codigo" required>
                    {% for p in produtos %}
                        <option value="{{ p.codigo }}">{{ p.codigo }} - {{ p.nome }} (R$ {{ "%.2f"|format(p.preco|float) }}) - Restam {{ p.quantidade }} un</option>
                    {% endfor %}
                </select>
            </div>

            <div class="form-group">
                <label for="quantidade">Quantidade a Vender:</label>
                <input type="number" id="quantidade" name="quantidade" min="1" value="1" required>
            </div>

            <button type="submit">Confirmar Venda e Dar Baixa</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    loja_id = request.args.get("loja_id", 1, type=int)
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM lojas ORDER BY id;")
    lojas = cur.fetchall()
    
    cur.execute("SELECT * FROM lojas WHERE id = %s;", (loja_id,))
    loja_atual = cur.fetchone()
    if not loja_atual and lojas:
        loja_atual = lojas[0]
        
    cur.execute("SELECT * FROM produtos WHERE loja_id = %s ORDER BY id;", (loja_atual['id'],))
    produtos = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, lojas=lojas, loja_atual=loja_atual, produtos=produtos)

@app.route("/vender", methods=["POST"])
def vender():
    loja_id = request.form.get("loja_id", type=int)
    codigo = request.form.get("produto_codigo")
    qtd_venda = request.form.get("quantidade", type=int)
    
    if not loja_id or not codigo or not qtd_venda or qtd_venda <= 0:
        return redirect(url_for("index", loja_id=loja_id))
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM produtos WHERE loja_id = %s AND codigo = %s;", (loja_id, codigo))
    prod = cur.fetchone()
    
    if prod and prod['quantidade'] >= qtd_venda:
        novo_estoque = prod['quantidade'] - qtd_venda
        valor_total = float(prod['preco']) * qtd_venda
        
        cur.execute("UPDATE produtos SET quantidade = %s WHERE id = %s;", (novo_estoque, prod['id']))
        cur.execute("UPDATE lojas SET saldo_caixa = saldo_caixa + %s WHERE id = %s;", (valor_total, loja_id))
        conn.commit()
        
    cur.close()
    conn.close()
    
    return redirect(url_for("index", loja_id=loja_id))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
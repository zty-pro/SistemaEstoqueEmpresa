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
                    <td><span style="font-weight:bold; color: {% if p.get('quantidade', 0) < 10 %}#dc3545{% else %}#333{% endif %};">{{ p.get('quantidade', 0) }} un</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <form action="/vender" method="POST">
            <h3>🛒 Registrar Nova Venda</h3>
            <input type="hidden" name="loja_id" value="{{ loja_atual_id }}">
            
            <div class="form-group">
                <label for="produto_codigo">Selecione o Produto:</label>
                <select name="produto_codigo" id="produto_codigo" required>
                    {% for p in produtos %}
                        {% set p_cod = p.get('codigo', p.get('id', '')) %}
                        <option value="{{ p_cod }}">{{ p_cod }} - {{ p.get('nome', '') }} (R$ {{ "%.2f"|format(p.get('preco', 0)|float) }}) - Restam {{ p.get('quantidade', 0) }} un</option>
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
    loja_id_param = request.args.get("loja_id", type=int)
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM lojas;")
    lojas = cur.fetchall()
    
    if not lojas:
        cur.close()
        conn.close()
        return "Nenhuma loja cadastrada no banco de dados.", 404
        
    # Identifica qual coluna é a chave primária da loja dinamicamente
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
    
    # Busca produtos da loja
    try:
        cur.execute("SELECT * FROM produtos WHERE loja_id = %s;", (loja_atual_id,))
    except Exception:
        try:
            cur.execute("SELECT * FROM produtos;")
        except Exception:
            produtos = []
    produtos = cur.fetchall() if 'produtos' not in locals() or not isinstance(produtos, list) else produtos
    
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
    
    if prod and prod.get('quantidade', 0) >= qtd_venda:
        novo_estoque = prod['quantidade'] - qtd_venda
        valor_total = float(prod['preco']) * qtd_venda
        
        cur.execute("UPDATE produtos SET quantidade = %s WHERE id = %s;", (novo_estoque, prod['id']))
        
        # Atualiza caixa da loja
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
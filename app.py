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

# ... (MANTENHA O SEU HTML_TEMPLATE E ROTA INDEX AQUI) ...

@app.route("/vender", methods=["POST"])
def vender():
    loja_id = request.form.get("loja_id")
    codigo = request.form.get("produto_codigo")
    qtd_venda = request.form.get("quantidade", type=int)

    if not codigo or not qtd_venda or qtd_venda <= 0:
        return redirect(url_for("index", loja_id=loja_id))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Busca o produto pelo código e (se houver) pela loja
        if loja_id:
            cur.execute("SELECT * FROM estoque WHERE codigo = %s AND loja_id = %s;", (str(codigo).strip(), loja_id))
            prod = cur.fetchone()
        else:
            prod = None

        if not prod:
            # Fallback buscando apenas por código
            cur.execute("SELECT * FROM estoque WHERE codigo = %s;", (str(codigo).strip(),))
            prod = cur.fetchone()

        if prod and int(prod.get('quantidade', 0)) >= qtd_venda:
            novo_estoque = int(prod['quantidade']) - qtd_venda
            valor_total = float(prod.get('preco', 0)) * qtd_venda

            # Executa UPDATE diretamente na chave primária ou no código
            if 'id' in prod and prod['id']:
                cur.execute("UPDATE estoque SET quantidade = %s WHERE id = %s;", (novo_estoque, prod['id']))
            else:
                cur.execute("UPDATE estoque SET quantidade = %s WHERE codigo = %s;", (novo_estoque, str(codigo).strip()))

            # Atualiza saldo de caixa se existir loja_id
            if loja_id:
                try:
                    cur.execute("UPDATE lojas SET saldo_caixa = COALESCE(saldo_caixa, 0) + %s WHERE id = %s;", (valor_total, loja_id))
                except Exception:
                    try:
                        cur.execute("UPDATE lojas SET saldo_caixa = COALESCE(saldo_caixa, 0) + %s WHERE loja_id = %s;", (valor_total, loja_id))
                    except Exception:
                        pass

            # O COMMIT É FUNDAMENTAL PARA SALVAR NO SUPABASE
            conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Erro ao processar venda: {e}")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for("index", loja_id=loja_id))
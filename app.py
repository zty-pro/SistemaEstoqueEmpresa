import os
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "sistema": "Sistema de Estoque Unificado",
        "endpoints": {
            "lojas": "/lojas",
            "estoque": "/estoque/<loja_id>",
            "caixa": "/caixa/<loja_id>"
        }
    })

@app.route("/lojas", methods=["GET"])
def listar_lojas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lojas;")
    lojas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(lojas)

@app.route("/estoque/<int:loja_id>", methods=["GET"])
def visualizar_estoque(loja_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM produtos WHERE loja_id = %s;", (loja_id,))
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(produtos)

@app.route("/caixa/<int:loja_id>", methods=["GET"])
def visualizar_caixa(loja_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT saldo_caixa FROM lojas WHERE id = %s;", (loja_id,))
    caixa = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify(caixa)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
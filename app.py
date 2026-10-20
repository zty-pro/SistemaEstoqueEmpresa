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
        .box-form { background: #fafafa; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8
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
                    <th>Código / ID</th>
                    <th>Nome do Produto</th>
                    <th>Preço (R$)</th>
                    <th>Quantidade</th>
                </tr>
            </thead>
            <tbody>
                {% for p in produtos %}
                {% set p_identifier = p.get('codigo') if p.get('codigo') else p.get('id') %}
                <tr>
                    <td><strong>{{ p_identifier }}</strong></td>
                    <td>{{ p.get('nome', '') }}</td>
                    <td>R$ {{ "%.2f"|format(p.get('preco', 0)|float) }}</td>
                    <td><span style="font-weight:bold; color: {% if p.get('quantidade', 0)|int < 10 %}#dc3545{% else %}#28a745{% endif %};">{{ p.get('quantidade', 0) }} un</span></td>
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
                                    {% set p_identifier = p.get('codigo') if p.get('codigo') else p.get('id') %}
                                    <option value="{{ p_identifier }}">{{ p_identifier }} - {{ p.get('nome', '') }} (R$ {{ "%.2f"|format(p.get('preco', 0)|float) }}) - Restam {{ p.get('quantidade', 0) }} un</option>
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
                    <input type="hidden" name="loja_
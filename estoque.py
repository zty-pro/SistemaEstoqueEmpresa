import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (para ler o link do Supabase)
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Cria a conexão com o banco de dados PostgreSQL no Supabase."""
    return psycopg2.connect(DATABASE_URL)

def inicializar_banco():
    """Cria as tabelas no Supabase caso elas ainda não existam."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de Lojas/CNPJs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lojas (
            cnpj VARCHAR(20) PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            caixa NUMERIC(10, 2) DEFAULT 0.0
        );
    """)
    
    # Tabela de Produtos vinculados a cada loja
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id SERIAL PRIMARY KEY,
            cnpj VARCHAR(20) REFERENCES lojas(cnpj),
            codigo VARCHAR(20) NOT NULL,
            nome VARCHAR(100) NOT NULL,
            quantidade INT NOT NULL,
            preco NUMERIC(10, 2) NOT NULL
        );
    """)
    
    conn.commit()
    
    # Insere dados iniciais se a tabela de lojas estiver vazia
    cursor.execute("SELECT COUNT(*) FROM lojas;")
    if cursor.fetchone()[0] == 0:
        # Cadastra as duas lojas padrão
        cursor.execute("INSERT INTO lojas (cnpj, nome, caixa) VALUES (%s, %s, %s)", 
                       ("12.345.678/0001-01", "Loja Matriz", 0.0))
        cursor.execute("INSERT INTO lojas (cnpj, nome, caixa) VALUES (%s, %s, %s)", 
                       ("12.345.678/0002-02", "Filial Shopping", 0.0))
        
        # Produtos da Matriz
        cursor.execute("INSERT INTO estoque (cnpj, codigo, nome, quantidade, preco) VALUES (%s, %s, %s, %s, %s)",
                       ("12.345.678/0001-01", "P001", "Camiseta Básica", 50, 39.90))
        cursor.execute("INSERT INTO estoque (cnpj, codigo, nome, quantidade, preco) VALUES (%s, %s, %s, %s, %s)",
                       ("12.345.678/0001-01", "P002", "Calça Jeans", 30, 89.90))
        
        # Produtos da Filial
        cursor.execute("INSERT INTO estoque (cnpj, codigo, nome, quantidade, preco) VALUES (%s, %s, %s, %s, %s)",
                       ("12.345.678/0002-02", "P001", "Camiseta Básica", 20, 39.90))
        cursor.execute("INSERT INTO estoque (cnpj, codigo, nome, quantidade, preco) VALUES (%s, %s, %s, %s, %s)",
                       ("12.345.678/0002-02", "P003", "Tênis Esportivo", 15, 149.90))
        
        conn.commit()
        
    cursor.close()
    conn.close()

def selecionar_loja():
    """Exibe as lojas disponíveis consultando o banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT cnpj, nome FROM lojas;")
    lojas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    print("\n--- SELEÇÃO DE LOJA / CNPJ ---")
    for index, loja in enumerate(lojas, start=1):
        print(f"{index}. {loja['nome']} (CNPJ: {loja['cnpj']})")
        
    opcao = input("Escolha o número da loja: ")
    try:
        idx = int(opcao) - 1
        if 0 <= idx < len(lojas):
            return lojas[idx]['cnpj']
        else:
            print("❌ Opção inválida!")
            return None
    except ValueError:
        print("❌ Entrada inválida!")
        return None

def visualizar_estoque(cnpj):
    """Exibe os produtos e saldos do caixa direto do banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Busca dados da loja
    cursor.execute("SELECT nome, caixa FROM lojas WHERE cnpj = %s;", (cnpj,))
    loja = cursor.fetchone()
    
    # Busca produtos do estoque da loja
    cursor.execute("SELECT codigo, nome, quantidade, preco FROM estoque WHERE cnpj = %s;", (cnpj,))
    produtos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    print(f"\n=== ESTOQUE: {loja['nome']} ({cnpj}) ===")
    print(f"Saldo em Caixa: R$ {loja['caixa']:.2f}")
    print("-" * 55)
    print(f"{'Cód.':<8} | {'Produto':<20} | {'Qtd':<5} | {'Preço (R$)':<10}")
    print("-" * 55)
    for prod in produtos:
        print(f"{prod['codigo']:<8} | {prod['nome']:<20} | {prod['quantidade']:<5} | R$ {prod['preco']:<8.2f}")
    print("-" * 55)

def realizar_venda(cnpj):
    """Regista uma venda no banco, atualizando estoque e caixa da loja em tempo real."""
    visualizar_estoque(cnpj)
    
    cod_produto = input("\nDigite o código do produto para vender (ou ENTER para cancelar): ").strip().upper()
    if not cod_produto:
        return
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Verifica se o produto existe na loja
    cursor.execute("SELECT * FROM estoque WHERE cnpj = %s AND codigo = %s;", (cnpj, cod_produto))
    produto = cursor.fetchone()
    
    if not produto:
        print("❌ Produto não encontrado nesta loja!")
        cursor.close()
        conn.close()
        return
        
    try:
        qtd_venda = int(input(f"Quantidade a vender de '{produto['nome']}': "))
        if qtd_venda <= 0:
            print("❌ A quantidade deve ser maior que zero!")
            cursor.close()
            conn.close()
            return
            
        if qtd_venda > produto['quantidade']:
            print(f"❌ Estoque insuficiente! Disponível: {produto['quantidade']}")
            cursor.close()
            conn.close()
            return
            
        # Calcula valores
        valor_total = qtd_venda * float(produto['preco'])
        nova_quantidade = produto['quantidade'] - qtd_venda
        
        # Atualiza a quantidade do produto no estoque
        cursor.execute("UPDATE estoque SET quantidade = %s WHERE cnpj = %s AND codigo = %s;", 
                       (nova_quantidade, cnpj, cod_produto))
        
        # Atualiza o saldo em caixa da loja
        cursor.execute("UPDATE lojas SET caixa = caixa + %s WHERE cnpj = %s;", 
                       (valor_total, cnpj))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n✅ Venda realizada com sucesso!")
        print(f"Total: R$ {valor_total:.2f} adicionado ao caixa da loja.")
        
    except ValueError:
        print("❌ Digite um número válido para a quantidade.")
        cursor.close()
        conn.close()

def menu_principal():
    """Menu interativo do sistema ligado ao Supabase."""
    inicializar_banco()
    cnpj_atual = None
    
    while True:
        if not cnpj_atual:
            cnpj_atual = selecionar_loja()
            if not cnpj_atual:
                continue

        # Busca o nome atualizado da loja para o menu
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT nome FROM lojas WHERE cnpj = %s;", (cnpj_atual,))
        loja_info = cursor.fetchone()
        cursor.close()
        conn.close()

        loja_nome = loja_info['nome'] if loja_info else "Loja"
        
        print(f"\n>>> PAINEL PRINCIPAL - {loja_nome} <<<")
        print("1. Visualizar Estoque e Caixa")
        print("2. Registrar Venda (Baixa de Estoque + Caixa)")
        print("3. Trocar de Loja / CNPJ")
        print("4. Sair do Sistema")
        
        opcao = input("Opção desejada: ").strip()
        
        if opcao == "1":
            visualizar_estoque(cnpj_atual)
        elif opcao == "2":
            realizar_venda(cnpj_atual)
        elif opcao == "3":
            cnpj_atual = None
        elif opcao == "4":
            print("\nEncerrando o sistema... Até logo!")
            break
        else:
            print("❌ Opção inválida! Tente novamente.")

if __name__ == "__main__":
    menu_principal()
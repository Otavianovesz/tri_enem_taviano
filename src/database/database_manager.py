import sqlite3
from sqlite3 import Error
import os
import pandas as pd
from datetime import datetime

def create_connection(db_file):
    """ 
    Cria uma conexão com o banco de dados SQLite especificado por db_file.
    :param db_file: caminho para o arquivo do banco de dados
    :return: Objeto de conexão ou None
    """
    conn = None
    try:
        # Garante que o diretório para o db exista
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
    return conn

def create_table(conn, create_table_sql):
    """ 
    Cria uma tabela a partir da instrução SQL fornecida.
    :param conn: Objeto de conexão
    :param create_table_sql: Uma instrução SQL CREATE TABLE
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(f"Erro ao criar tabela: {e}")

def setup_database(db_path):
    """
    Função principal para configurar o banco de dados e criar todas as tabelas necessárias.
    """
    sql_create_itens_table = """
    CREATE TABLE IF NOT EXISTS ItensOficiaisENEM (
        id_item INTEGER PRIMARY KEY,
        ano_enem INTEGER NOT NULL,
        area_conhecimento TEXT NOT NULL,
        param_a REAL,
        param_b REAL,
        param_c REAL,
        gabarito TEXT,
        topico_matriz TEXT
    );
    """

    sql_create_analises_table = """
    CREATE TABLE IF NOT EXISTS AnalisesManuais (
        id_analise INTEGER PRIMARY KEY AUTOINCREMENT,
        param_a REAL NOT NULL,
        param_b REAL NOT NULL,
        param_c REAL NOT NULL,
        justificativa TEXT,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    sql_create_resultados_table = """
    CREATE TABLE IF NOT EXISTS ResultadosSimulados (
        id_resultado INTEGER PRIMARY KEY AUTOINCREMENT,
        data_simulado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        area_conhecimento TEXT NOT NULL,
        nota_tri REAL NOT NULL,
        acertos INTEGER NOT NULL,
        total_itens INTEGER NOT NULL
    );
    """

    conn = create_connection(db_path)
    if conn is not None:
        create_table(conn, sql_create_itens_table)
        create_table(conn, sql_create_analises_table)
        create_table(conn, sql_create_resultados_table)
        conn.close()
    else:
        print("Erro! Não foi possível criar a conexão com o banco de dados.")

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---

def add_analise_manual(db_path, a, b, c, justificativa):
    """
    Adiciona uma nova análise manual no banco de dados.
    :param db_path: Caminho para o banco de dados.
    :param a: Parâmetro 'a' (discriminação).
    :param b: Parâmetro 'b' (dificuldade).
    :param c: Parâmetro 'c' (acerto casual).
    :param justificativa: Texto da análise.
    :return: True se sucesso, False caso contrário.
    """
    sql = ''' INSERT INTO AnalisesManuais(param_a, param_b, param_c, justificativa)
              VALUES(?,?,?,?) '''
    conn = create_connection(db_path)
    if not conn: return False
    
    try:
        cur = conn.cursor()
        cur.execute(sql, (a, b, c, justificativa))
        conn.commit()
        return True
    except Error as e:
        print(f"Erro ao inserir análise manual: {e}")
        return False
    finally:
        if conn:
            conn.close()

def fetch_random_items(db_path, area, count):
    """
    Busca um número específico de itens aleatórios de uma determinada área.
    :param db_path: Caminho para o banco de dados.
    :param area: A área de conhecimento (ex: 'CH', 'CN', 'LC', 'MT').
    :param count: O número de itens a serem retornados.
    :return: Um DataFrame do pandas com os itens ou None.
    """
    conn = create_connection(db_path)
    if not conn: return None
    
    try:
        # A consulta SQL normaliza a busca pela sigla da área.
        # Adiciona a condição para garantir que os parâmetros TRI não sejam nulos.
        query = f"""
            SELECT id_item, gabarito, param_a, param_b, param_c 
            FROM ItensOficiaisENEM 
            WHERE area_conhecimento = ? 
            AND param_a IS NOT NULL
            AND param_b IS NOT NULL
            AND param_c IS NOT NULL
            ORDER BY RANDOM() 
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(area, count))
        return df
    except Error as e:
        print(f"Erro ao buscar itens aleatórios: {e}")
        return None
    finally:
        if conn:
            conn.close()
            
def save_simulation_result(db_path, area, nota, acertos, total):
    """
    Salva o resultado de um simulado no banco de dados.
    :param db_path: Caminho para o banco de dados.
    :param area: Área de conhecimento do simulado.
    :param nota: Nota TRI final.
    :param acertos: Número de acertos.
    :param total: Número total de itens.
    :return: True se sucesso, False caso contrário.
    """
    sql = ''' INSERT INTO ResultadosSimulados(area_conhecimento, nota_tri, acertos, total_itens)
              VALUES(?,?,?,?) '''
    conn = create_connection(db_path)
    if not conn: return False
    
    try:
        cur = conn.cursor()
        cur.execute(sql, (area, nota, acertos, total))
        conn.commit()
        return True
    except Error as e:
        print(f"Erro ao salvar resultado do simulado: {e}")
        return False
    finally:
        if conn:
            conn.close()

def fetch_all_simulation_results(db_path):
    """
    Busca todos os resultados de simulados salvos para o dashboard.
    :param db_path: Caminho para o banco de dados.
    :return: Um DataFrame do pandas com os resultados ou None.
    """
    conn = create_connection(db_path)
    if not conn: return None
    
    try:
        query = "SELECT data_simulado, area_conhecimento, nota_tri, acertos, total_itens FROM ResultadosSimulados ORDER BY data_simulado ASC"
        df = pd.read_sql_query(query, conn, parse_dates=['data_simulado'])
        return df
    except Error as e:
        print(f"Erro ao buscar resultados de simulados: {e}")
        return None
    finally:
        if conn:
            conn.close()


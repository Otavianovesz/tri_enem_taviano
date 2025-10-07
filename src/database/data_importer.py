import pandas as pd
import sqlite3
from sqlite3 import Error
import os
import argparse
import sys

# Garante que o diretório 'src' esteja no path para importação correta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = os.path.join('data', 'tri_database.db')

# --- MAPEAMENTO FLEXÍVEL DE COLUNAS ---
# Os nomes das colunas nos arquivos do INEP podem variar.
# Este dicionário mapeia os nomes de colunas do nosso banco para possíveis nomes nos arquivos CSV.
COLUMN_MAPPING = {
    'id_item': ['ID_ITEM', 'CO_ITEM'],
    'area_conhecimento': ['SG_AREA', 'CO_PROVA'], # CO_PROVA pode precisar de um mapeamento adicional
    'param_a': ['NU_PARAM_A', 'PARAM_A'],
    'param_b': ['NU_PARAM_B', 'PARAM_B'],
    'param_c': ['NU_PARAM_C', 'PARAM_C'],
    'gabarito': ['TX_GABARITO', 'GABARITO']
}

# Mapeamento de códigos de prova para siglas de área (exemplo, pode precisar de ajuste)
AREA_CODE_MAPPING = {
    '511': 'LC', '512': 'CH', '513': 'CN', '514': 'MT', # Exemplo ENEM 2017
    '1': 'LC', '2': 'CH', '3': 'CN', '4': 'MT'      # Outros exemplos
}

def find_column_name(df_columns, target_columns):
    """ Encontra qual dos nomes de coluna possíveis existe no DataFrame. """
    for col in target_columns:
        if col in df_columns:
            return col
    return None

def import_data_from_csv(csv_path, ano_enem):
    """
    Lê um arquivo CSV de microdados do INEP, processa e insere os dados
    dos itens na tabela ItensOficiaisENEM do banco de dados.

    :param csv_path: Caminho para o arquivo .csv dos microdados.
    :param ano_enem: Ano do ENEM correspondente aos dados.
    """
    if not os.path.exists(csv_path):
        print(f"Erro: O arquivo não foi encontrado em '{csv_path}'")
        return

    print(f"Iniciando a importação do arquivo: {csv_path}")
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        # Processa o arquivo em chunks para não sobrecarregar a memória
        chunk_size = 50000
        total_rows = 0
        
        for chunk in pd.read_csv(csv_path, chunksize=chunk_size, encoding='latin1', sep=';', low_memory=False):
            
            # --- Identificação e Renomeação Dinâmica de Colunas ---
            current_mapping = {}
            for db_col, possible_cols in COLUMN_MAPPING.items():
                found_col = find_column_name(chunk.columns, possible_cols)
                if found_col:
                    current_mapping[found_col] = db_col
                else:
                    print(f"Aviso: Nenhuma coluna encontrada para '{db_col}' neste chunk.")

            # Renomeia as colunas do chunk para o padrão do nosso banco
            chunk.rename(columns=current_mapping, inplace=True)
            
            # Filtra para ter apenas as colunas que realmente precisamos
            required_cols = list(COLUMN_MAPPING.keys())
            chunk = chunk[[col for col in required_cols if col in chunk.columns]]

            # --- Limpeza e Transformação dos Dados ---
            if 'param_a' in chunk.columns and 'param_b' in chunk.columns and 'param_c' in chunk.columns:
                # Remove linhas onde os parâmetros TRI são nulos
                chunk.dropna(subset=['param_a', 'param_b', 'param_c'], inplace=True)
                
                # Converte parâmetros para numérico, tratando vírgula como decimal
                for param in ['param_a', 'param_b', 'param_c']:
                    if chunk[param].dtype == 'object':
                        chunk[param] = chunk[param].str.replace(',', '.').astype(float)
            
            # Adiciona a coluna do ano do ENEM
            chunk['ano_enem'] = ano_enem
            
            # Lógica para mapear código de área para sigla
            if 'area_conhecimento' in chunk.columns and chunk['area_conhecimento'].dtype != 'object':
                 chunk['area_conhecimento'] = chunk['area_conhecimento'].astype(str).map(AREA_CODE_MAPPING)

            # Insere o chunk processado no banco de dados
            if not chunk.empty:
                chunk.to_sql('ItensOficiaisENEM', conn, if_exists='append', index=False)
                rows_in_chunk = len(chunk)
                total_rows += rows_in_chunk
                print(f"Processado e inserido um chunk. {total_rows} linhas importadas até agora.")

    except Error as e:
        print(f"Ocorreu um erro de banco de dados: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("Importação concluída. Conexão com o banco de dados fechada.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Importador de Microdados do ENEM para o banco de dados TRI.")
    parser.add_argument("csv_file", help="Caminho para o arquivo CSV dos microdados do INEP.")
    parser.add__actions[1].help = "Ano do ENEM a que os dados se referem (ex: 2022)."
    parser.add_argument("ano_enem", type=int, help="Ano do ENEM a que os dados se referem (ex: 2022).")
    
    args = parser.parse_args()
    
    import_data_from_csv(args.csv_file, args.ano_enem)


import sys
import os
from PyQt6.QtWidgets import QApplication

# Adiciona o diretório raiz ao path do sistema para permitir importações absolutas
# de qualquer lugar que o script seja executado.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.gui.gui_manager import MainWindow
from src.database import database_manager

def main():
    """
    Função principal que prepara o ambiente e inicia a aplicação.
    """
    # 1. Garante que o diretório de dados exista
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Diretório '{data_dir}' criado.")

    # 2. Caminho completo para o banco de dados
    db_path = os.path.join(data_dir, 'tri_database.db')

    # 3. Garante que o banco de dados e suas tabelas estejam configurados
    print("Verificando e configurando o banco de dados...")
    database_manager.setup_database(db_path)
    print("Banco de dados pronto.")

    # 4. Inicia a aplicação PyQt
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    print("Aplicação iniciada com sucesso. Feche a janela para encerrar o programa.")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()


import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QMessageBox,
    QComboBox, QSpinBox, QGroupBox, QRadioButton, QButtonGroup, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

# Importa os módulos de lógica e banco de dados
from src.database import database_manager
from src.logic import tri_engine

# --- Widget de Gráfico Matplotlib para Integração com PyQt ---
class MplCanvas(FigureCanvas):
    """ Classe base para um widget Matplotlib. """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)

# --- Janela Principal da Aplicação ---
class MainWindow(QMainWindow):
    """
    Classe principal que define a interface gráfica, suas abas e toda a lógica de interação.
    """
    # Sinal para ser emitido quando um simulado for concluído
    simulation_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Painel de Controle de Performance TRI")
        self.setGeometry(100, 100, 1200, 800)
        self.db_path = os.path.join('data', 'tri_database.db')

        # Estrutura de abas
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Conecta a mudança de aba para a função de atualização do dashboard
        self.tabs.currentChanged.connect(self.on_tab_changed)
        # Conecta o sinal de finalização de simulado à atualização do dashboard
        self.simulation_finished.connect(self.update_dashboard)

        # Variáveis de estado para o simulado
        self.current_simulado_items = None
        self.current_question_index = 0
        self.user_answers = {}

        # Cria as abas
        self.create_dashboard_tab()
        self.create_simulado_tab()
        self.create_analise_experimental_tab()
        
    def on_tab_changed(self, index):
        """ Chamado quando o usuário troca de aba. """
        # Se a aba selecionada for a do Dashboard (índice 0), atualiza os gráficos.
        if index == 0:
            self.update_dashboard()

    def create_dashboard_tab(self):
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Cria dois canvases para os gráficos
        self.score_canvas = MplCanvas(self, width=8, height=4, dpi=100)
        self.accuracy_canvas = MplCanvas(self, width=8, height=4, dpi=100)
        
        layout.addWidget(QLabel("Evolução da Nota TRI por Área"))
        layout.addWidget(self.score_canvas)
        layout.addWidget(QLabel("Evolução da Porcentagem de Acertos por Área"))
        layout.addWidget(self.accuracy_canvas)
        
        self.tabs.addTab(dashboard_widget, "Dashboard")

    def update_dashboard(self):
        """ Busca os dados e redesenha os gráficos do dashboard. """
        df = database_manager.fetch_all_simulation_results(self.db_path)
        
        # Limpa os gráficos antigos
        self.score_canvas.axes.cla()
        self.accuracy_canvas.axes.cla()

        if df is not None and not df.empty:
            df['percentual_acertos'] = (df['acertos'] / df['total_itens']) * 100
            
            # Gráfico de Nota TRI
            for area in df['area_conhecimento'].unique():
                subset = df[df['area_conhecimento'] == area]
                self.score_canvas.axes.plot(subset['data_simulado'], subset['nota_tri'], marker='o', linestyle='-', label=area)
            
            # Gráfico de Porcentagem de Acertos
            for area in df['area_conhecimento'].unique():
                subset = df[df['area_conhecimento'] == area]
                self.accuracy_canvas.axes.plot(subset['data_simulado'], subset['percentual_acertos'], marker='x', linestyle='--', label=area)

        # Formatando o Gráfico de Notas
        self.score_canvas.axes.set_title("Evolução da Nota TRI")
        self.score_canvas.axes.set_xlabel("Data")
        self.score_canvas.axes.set_ylabel("Nota TRI")
        self.score_canvas.axes.legend()
        self.score_canvas.axes.grid(True)
        self.score_canvas.fig.autofmt_xdate()
        self.score_canvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))

        # Formatando o Gráfico de Acertos
        self.accuracy_canvas.axes.set_title("Evolução da Porcentagem de Acertos")
        self.accuracy_canvas.axes.set_xlabel("Data")
        self.accuracy_canvas.axes.set_ylabel("Acertos (%)")
        self.accuracy_canvas.axes.legend()
        self.accuracy_canvas.axes.grid(True)
        self.accuracy_canvas.fig.autofmt_xdate()
        self.accuracy_canvas.axes.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        
        self.score_canvas.draw()
        self.accuracy_canvas.draw()

    def create_simulado_tab(self):
        """ Cria a aba de Simulado com uma tela de setup e uma tela de prova. """
        self.simulado_stack = QStackedWidget()

        # Tela 1: Setup do Simulado
        setup_widget = QWidget()
        setup_layout = QVBoxLayout(setup_widget)
        setup_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        setup_layout.addWidget(QLabel("Área do Conhecimento:"))
        self.area_combo = QComboBox()
        self.area_combo.addItems(["Linguagens e Códigos (LC)", "Ciências Humanas (CH)", "Ciências da Natureza (CN)", "Matemática (MT)"])
        setup_layout.addWidget(self.area_combo)

        setup_layout.addWidget(QLabel("Número de Questões:"))
        self.questoes_spinbox = QSpinBox()
        self.questoes_spinbox.setMinimum(5)
        self.questoes_spinbox.setMaximum(45)
        self.questoes_spinbox.setValue(10)
        setup_layout.addWidget(self.questoes_spinbox)
        
        start_button = QPushButton("Iniciar Simulado")
        start_button.clicked.connect(self.handle_start_simulado)
        setup_layout.addWidget(start_button)
        
        self.simulado_stack.addWidget(setup_widget)

        # Tela 2: Prova em Andamento
        self.prova_widget = self.create_prova_widget()
        self.simulado_stack.addWidget(self.prova_widget)
        
        self.tabs.addTab(self.simulado_stack, "Iniciar Simulado")

    def create_prova_widget(self):
        """ Cria o widget que exibirá as questões durante o simulado. """
        prova_widget = QWidget()
        layout = QVBoxLayout(prova_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.question_label = QLabel("Questão 1 de X")
        layout.addWidget(self.question_label)

        self.item_id_label = QLabel("ID do Item: N/A")
        layout.addWidget(self.item_id_label)

        self.options_group = QGroupBox("Alternativas")
        options_layout = QVBoxLayout()
        self.radio_buttons = [QRadioButton(chr(65 + i)) for i in range(5)] # A, B, C, D, E
        self.button_group = QButtonGroup()
        for i, rb in enumerate(self.radio_buttons):
            options_layout.addWidget(rb)
            self.button_group.addButton(rb, i)
        self.options_group.setLayout(options_layout)
        layout.addWidget(self.options_group)

        self.next_button = QPushButton("Próxima Questão")
        self.next_button.clicked.connect(self.handle_next_question)
        layout.addWidget(self.next_button)

        return prova_widget

    def handle_start_simulado(self):
        area_texto = self.area_combo.currentText().split('(')[1][:-1] # Extrai 'LC' de 'Linguagens (LC)'
        num_questoes = self.questoes_spinbox.value()
        
        self.current_simulado_items = database_manager.fetch_random_items(self.db_path, area_texto, num_questoes)
        
        if self.current_simulado_items is None or len(self.current_simulado_items) < num_questoes:
            QMessageBox.warning(self, "Erro", "Não foi possível carregar o número de questões solicitado do banco de dados para esta área.")
            return

        self.current_question_index = 0
        self.user_answers = {}
        self.display_current_question()
        self.simulado_stack.setCurrentIndex(1) # Muda para a tela da prova

    def display_current_question(self):
        """ Atualiza a tela com os dados da questão atual. """
        total_questions = len(self.current_simulado_items)
        self.question_label.setText(f"Questão {self.current_question_index + 1} de {total_questions}")
        
        item_id = self.current_simulado_items.iloc[self.current_question_index]['id_item']
        self.item_id_label.setText(f"ID do Item: {item_id}")
        
        self.button_group.setExclusive(False)
        for rb in self.radio_buttons:
            rb.setChecked(False)
        self.button_group.setExclusive(True)

        if self.current_question_index == total_questions - 1:
            self.next_button.setText("Finalizar Simulado")
        else:
            self.next_button.setText("Próxima Questão")

    def handle_next_question(self):
        """ Salva a resposta do usuário e avança para a próxima questão ou finaliza. """
        selected_button = self.button_group.checkedButton()
        if selected_button is None:
            QMessageBox.warning(self, "Atenção", "Por favor, selecione uma alternativa.")
            return
            
        answer = selected_button.text()
        item_id = self.current_simulado_items.iloc[self.current_question_index]['id_item']
        self.user_answers[item_id] = answer

        if self.next_button.text() == "Finalizar Simulado":
            self.handle_finish_simulado()
        else:
            self.current_question_index += 1
            self.display_current_question()

    def handle_finish_simulado(self):
        """ Calcula o resultado do simulado e o exibe. """
        respostas_vetor = []
        parametros_itens = []
        acertos = 0
        
        for index, row in self.current_simulado_items.iterrows():
            item_id = row['id_item']
            gabarito = row['gabarito']
            user_answer = self.user_answers.get(item_id, '')
            
            if user_answer == gabarito:
                respostas_vetor.append(1)
                acertos += 1
            else:
                respostas_vetor.append(0)
            
            parametros_itens.append((row['param_a'], row['param_b'], row['param_c']))
        
        theta = tri_engine.estimar_proficiencia(respostas_vetor, parametros_itens)
        nota = tri_engine.calcular_nota_tri(theta)

        if nota is None:
            QMessageBox.critical(self, "Erro de Cálculo", "Não foi possível calcular a nota TRI. O padrão de respostas pode ser extremo (todos acertos ou todos erros).")
            self.simulado_stack.setCurrentIndex(0)
            return
        
        # Salva no banco de dados
        area_texto = self.area_combo.currentText().split('(')[1][:-1]
        total_itens = len(self.current_simulado_items)
        database_manager.save_simulation_result(self.db_path, area_texto, nota, acertos, total_itens)
        
        # Exibe o resultado
        QMessageBox.information(self, "Simulado Finalizado", 
                                f"Resultado:\n\n"
                                f"Acertos: {acertos} de {total_itens}\n"
                                f"Nota TRI Estimada: {nota:.2f}")
        
        # Emite o sinal para o dashboard atualizar
        self.simulation_finished.emit()

        # Volta para a tela de setup
        self.simulado_stack.setCurrentIndex(0)

    def create_analise_experimental_tab(self):
        analise_widget = QWidget()
        layout = QVBoxLayout(analise_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title_label = QLabel("Análise Experimental Manual")
        font = title_label.font()
        font.setPointSize(16)
        title_label.setFont(font)
        layout.addWidget(title_label)
        
        layout.addWidget(QLabel("Parâmetro 'a' (Discriminação):"))
        self.param_a_input = QLineEdit()
        layout.addWidget(self.param_a_input)

        layout.addWidget(QLabel("Parâmetro 'b' (Dificuldade):"))
        self.param_b_input = QLineEdit()
        layout.addWidget(self.param_b_input)
        
        layout.addWidget(QLabel("Parâmetro 'c' (Acerto Casual):"))
        self.param_c_input = QLineEdit()
        layout.addWidget(self.param_c_input)

        layout.addWidget(QLabel("Justificativa da Análise:"))
        self.justificativa_input = QTextEdit()
        layout.addWidget(self.justificativa_input)
        
        self.salvar_analise_button = QPushButton("Salvar Análise")
        self.salvar_analise_button.clicked.connect(self.handle_salvar_analise)
        layout.addWidget(self.salvar_analise_button)
        
        self.tabs.addTab(analise_widget, "Análise Experimental")

    def handle_salvar_analise(self):
        """ Valida os dados da análise manual e os salva no banco. """
        try:
            a = float(self.param_a_input.text().replace(',', '.'))
            b = float(self.param_b_input.text().replace(',', '.'))
            c = float(self.param_c_input.text().replace(',', '.'))
            justificativa = self.justificativa_input.toPlainText()
        except ValueError:
            QMessageBox.warning(self, "Erro de Entrada", "Os parâmetros 'a', 'b' e 'c' devem ser números válidos.")
            return

        if not justificativa.strip():
            QMessageBox.warning(self, "Erro de Entrada", "O campo de justificativa não pode estar vazio.")
            return

        success = database_manager.add_analise_manual(self.db_path, a, b, c, justificativa)

        if success:
            QMessageBox.information(self, "Sucesso", "Análise salva com sucesso no banco de dados.")
            # Limpa os campos
            self.param_a_input.clear()
            self.param_b_input.clear()
            self.param_c_input.clear()
            self.justificativa_input.clear()
        else:
            QMessageBox.critical(self, "Erro de Banco de Dados", "Ocorreu um erro ao tentar salvar a análise.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


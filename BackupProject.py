import os
import pyodbc
import sys
import schedule
import time
import json
import subprocess
import configparser
import qdarktheme
import mysql.connector
import logging
import traceback
import pymysql
from mysql.connector import Error
from cryptography.fernet import Fernet
from datetime import datetime
from PyQt5.QtWidgets import QGraphicsOpacityEffect, QShortcut, QDialog, QGridLayout, QTabWidget, QApplication, QMainWindow, QSystemTrayIcon, QAction, QMenu, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox, QCheckBox, QHBoxLayout
from PyQt5.QtCore import QThread, QSize, Qt
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap

global app

# Função para buscar a chave fernet do arquivo .key
def get_key_from_file():
        try:
            with open("content\\fernet.key", "rb") as key_file:
                key = key_file.read()
            return key
        
        except pyodbc.Error as e:
            error_message = f"Erro ao recuperar a chave do arquivo: {e}"
            logging.error(error_message)  # Grava o erro no arquivo de log
            print(error_message)
            return None

# Descriptografa o valor usando a chave Fernet
def decrypt_value(encrypted_value, key):
    f = Fernet(key)
    decrypted_value = f.decrypt(encrypted_value.encode()).decode()
    return decrypted_value

# Verificação de login
def check_login(username, password):
    key = get_key_from_file()
    if not key:
        return False
    
    with open("content\\credentials.json", "r") as file:
        data = json.load(file)
    
    for user in data['users']:
        decrypted_password = decrypt_value(user['password'], key)
        if user['username'] == username and decrypted_password == password:
            return True
    
    return False

# Configuração do logger de erros
error_log = logging.getLogger('error_log')
error_log.setLevel(logging.ERROR)
error_handler = logging.FileHandler('logs\\error.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_log.addHandler(error_handler)

# Configuração do main logger
main_log = logging.getLogger('main_log')
main_log.setLevel(logging.INFO)
main_handler = logging.FileHandler('logs\\main.log')
main_handler.setLevel(logging.INFO)
main_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
main_log.addHandler(main_handler)

# Configuração do logger de exceções não tratadas
exception_log = logging.getLogger('exception_log')
exception_log.setLevel(logging.ERROR)
exception_handler = logging.FileHandler('logs\\exception.log')
exception_handler.setLevel(logging.ERROR)
exception_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
exception_log.addHandler(exception_handler)

# Função para tratar os erros internos do python
def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, Exception):
            formatted_exception = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            exception_log.error(formatted_exception)
            print(formatted_exception)

# Configuração do excepthook para capturar exceções não tratadas
sys.excepthook = handle_exception

class LoginScreen(QMainWindow):
    def __init__(self, main_screen):
        super(LoginScreen, self).__init__()
        self.main_screen = main_screen

        # Define o titulo da tela e o tamanho fixo
        self.setWindowTitle("Tela de Login")
        self.setFixedSize(400, 220)

        # Configura o ícone da janela
        self.setWindowIcon(QIcon('images\\system_icon.png'))

        # ícone do usuário
        self.username_label = QLabel()
        self.username_label_icon = QIcon("images\\user_icon.png")
        self.username_label.setPixmap(self.username_label_icon.pixmap(56, 56))
        
        # Label e lineedit para entrada do usuário
        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("Usuário")
        self.username_entry.setStyleSheet("QLineEdit { border: 2px solid gray; border-radius: 10px; padding: 0 8px; width: 200px; height: 30px; }")
        self.username_entry.returnPressed.connect(lambda: self.password_entry.setFocus())

        # Ícone da senha
        self.password_label = QLabel()
        self.password_label_icon = QIcon("images\\password_icon.png")
        self.password_label.setPixmap(self.password_label_icon.pixmap(56, 56))
        
        # Label e linedit para entrada da senha
        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Senha")
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setStyleSheet("QLineEdit { border: 2px solid gray; border-radius: 10px; padding: 0 8px; width: 200px; height: 30px; }")
        self.password_entry.returnPressed.connect(lambda: self.login())

        # Botão para login
        self.login_button = QPushButton(" ")
        self.login_button_icon = QIcon("images\\login_icon.png")  # Definindo o ícone do botão
        self.login_button.setIcon(self.login_button_icon)  # Configurando o ícone para o botão
        icon_size = QSize(32, 32)
        self.login_button.setIconSize(icon_size)  # Definindo o tamanho do ícone

        self.login_button.clicked.connect(self.login)

        # Botão para abrir a tela de registro
        self.register_button = QPushButton("Registrar")
        self.register_button.clicked.connect(self.open_registration_screen)
        self.register_button.hide()  # Esconder o botão de registro inicialmente

        layout = QVBoxLayout()
        layout.addStretch(1)

        # Layout horizontal para o campo de entrada do usuário
        user_layout = QHBoxLayout()
        user_layout.addWidget(self.username_label)
        user_layout.addWidget(self.username_entry)
        layout.addLayout(user_layout)

        # Layout horizontal para o campo de entrada da senha
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(self.password_label)
        pass_layout.addWidget(self.password_entry)
        layout.addLayout(pass_layout)

        # Botões de login e registro
        layout.addWidget(self.login_button, alignment=Qt.AlignHCenter)
        layout.addWidget(self.register_button, alignment=Qt.AlignHCenter)
        layout.addStretch(1)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Definir uma combinação de teclas para revelar/ocultar o botão de registro
        self.show_register_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.show_register_shortcut.activated.connect(self.toggle_register_button_visibility)
    
    # Função de login da tela inicial
    def login(self):
        username = self.username_entry.text()
        password = self.password_entry.text()
        if check_login(username, password):
            success_message = f"Login bem sucedido do usuario {username}!"
            main_log.info(success_message)
            self.username_entry.clear() # Limpa o campo de usuário
            self.password_entry.clear()  # Limpa o campo de senha
            self.username_entry.setFocus() 
            self.hide()
            self.main_screen.show()
        else:
            QMessageBox.critical(self, "Erro", "Usuario ou senha incorretos")
            self.username_entry.clear()
            self.password_entry.clear()
            self.username_entry.setFocus()  # Define o foco de volta para o campo de senha

    # Função para mudar a visibilidade do botão de registro
    def toggle_register_button_visibility(self):
        if self.register_button.isHidden():
            self.register_button.show()
        else:
            self.register_button.hide()
    
    # Função para abrir a tela de registro
    def open_registration_screen(self):
        registration_screen = RegistrationScreen()
        registration_screen.exec_()  # Exibir a tela de registro como um diálogo
    
    # Função para esconder a tela de login em vez de fechar
    def closeEvent(self, event):
        event.ignore()
        self.hide()

class RegistrationScreen(QDialog):
    def __init__(self):
        super(RegistrationScreen, self).__init__()
        self.setWindowTitle("Tela de Registro")
        self.setFixedSize(400, 220)

        # Configura o ícone da janela
        self.setWindowIcon(QIcon('images\\system_icon.png'))

        # Campo de entrada para o novo usuário
        self.new_username_entry = QLineEdit()
        self.new_username_entry.setPlaceholderText("Novo Username")

        # Campo de entrada para a senha
        self.new_password_entry = QLineEdit()
        self.new_password_entry.setPlaceholderText("Nova Password")
        self.new_password_entry.setEchoMode(QLineEdit.Password)

        # Botão de registro
        self.register_button = QPushButton("Registrar")
        self.register_button.clicked.connect(self.register_user)

        layout = QVBoxLayout()
        
        layout.addWidget(self.new_username_entry)
        layout.addWidget(self.new_password_entry)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

    # Função para registrar o usuário
    def register_user(self):
        new_username = self.new_username_entry.text()
        new_password = self.new_password_entry.text()
        
        # Criptografa a senha antes de salvar
        key = get_key_from_file()  # Obtém a chave de criptografia
        cipher_suite = Fernet(key)
        encrypted_password = cipher_suite.encrypt(new_password.encode()).decode()

        # Carrega os usuários existentes do arquivo JSON
        with open("content/credentials.json", "r") as file:
            data = json.load(file)
        
        # Adiciona novo usuário à lista de usuários
        new_user = {
            "username": new_username,
            "password": encrypted_password
        }

        data["users"].append(new_user)

        # Salva os usuários atualizados de volta ao arquivo JSON com a formatação preservada
        with open("content/credentials.json", "w") as file:
            json.dump(data, file, indent=4)
        
        self.accept()  # Fecha a tela de registro após o registro bem-sucedido

class MainWindow(QMainWindow):
    def __init__(self, login_screen):
        super(MainWindow, self).__init__()

        self.login_screen = login_screen  # Armazena a referência para a tela de login

        # Define o caminho do ícone
        icon_path = os.path.join("images", "system_icon.png")
        self.setFixedSize(720, 480)

        # Configura o ícone da janela
        self.setWindowIcon(QIcon('images\\system_icon.png'))

        # Carrega o ícone a partir do arquivo
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(icon_path))

        # Crie uma ação para a funcao de backup
        backup_action = QAction("Backup", self)
        backup_action.triggered.connect(self.backup_handler)

        # Crie uma ação para a funcao de sair
        close_action = QAction("Sair", self)
        close_action.triggered.connect(app.quit)  # Alterado para fechar o aplicativo

        # Cria as acoes dos tray menu
        tray_menu = QMenu()
        tray_menu.addAction(backup_action)
        tray_menu.addAction(close_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Cria abas para Agendamento e Configurações
        self.tabs = QTabWidget(self)
        self.schedule_tab = QWidget()
        self.settings_tab = QWidget()

        # Define o icone das abas
        self.tabs.addTab(self.settings_tab, QIcon("images\\config.png"), None)
        self.tabs.addTab(self.schedule_tab, QIcon("images\\schedule.png"), None)

        # Muda a localização das abas
        self.tabs.setTabPosition(QTabWidget.West)

        # Configurar os ícones para as abas
        self.tabs.setTabIcon(0, QIcon("images\\config.png"))
        self.tabs.setTabIcon(1, QIcon("images\\schedule.png"))
        
        # Ajustar o tamanho dos ícones para centralizá-los
        icon_size = QSize(32, 32)
        self.tabs.setIconSize(icon_size)
        
        # Configurações das abas
        self.setup_schedule_tab()
        self.setup_settings_tab()
        self.setCentralWidget(self.tabs)

        # Carregue as configurações salvas
        self.load_settings()

        # Conecte o sinal activated do QSystemTrayIcon à função tray_icon_activated
        self.tray_icon.activated.connect(self.tray_icon_activated)

    # Função para abrir o programa com dois cliques
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:  # Verifica se o clique foi duplo
            self.login_screen.show()
            
    # Função para criar a aba de agendamento
    def setup_schedule_tab(self):
        self.background_label = QLabel(self.schedule_tab)
        
        pixmap = QPixmap("images/schedule2.png")
        pixmap_scaled = pixmap.scaled(350, 350, Qt.KeepAspectRatio)
        
        self.background_label.setPixmap(pixmap_scaled)
        self.background_label.setAlignment(Qt.AlignRight | Qt.AlignTop)  # Alinha a imagem à direita
        self.background_label.setGeometry(0, 25, self.schedule_tab.width(), self.schedule_tab.height()-50)
        
        opacity_effect = QGraphicsOpacityEffect(self)
        opacity_effect.setOpacity(0.7)  # Ajusta o nível de transparência conforme necessário
        self.background_label.setGraphicsEffect(opacity_effect) 

        # Adiciona checkboxes para cada dia da semana
        self.day_checkboxes = {day: QCheckBox(day, self.schedule_tab) for day in ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]}

        # Adiciona um QLineEdit para cada dia da semana para inserir a hora
        self.time_edits = {day: QLineEdit(self.schedule_tab) for day in ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]}
        
        # Define o tamanho máximo dos QLineEdit
        for edit in self.time_edits.values():
            edit.setMaximumWidth(100)

        # Botão para salvar as configurações
        self.save_button_schedule = QPushButton("Salvar Configurações", self.schedule_tab)
        self.save_button_schedule.clicked.connect(self.save_settings)
        self.save_button_schedule.clicked.connect(self.schedule_backups)

        layout_schedule = QVBoxLayout()
        for day in ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]:
            day_layout = QHBoxLayout()
            day_layout.addWidget(self.day_checkboxes[day])
            day_layout.addWidget(self.time_edits[day])
            clock_icon = QLabel()
            clock_icon.setPixmap(QIcon("images/clock.png").pixmap(20, 20))  # Ajusta o tamanho do ícone conforme necessário
            day_layout.addWidget(clock_icon)
            day_layout.addStretch()  # Adiciona um espaço flexível para alinhar à esquerda
            layout_schedule.addLayout(day_layout)
            
        # Adiciona as checkboxes de backup MySQL e SQL Server
        self.checkbox_mysql = QCheckBox("Backup MySQL", self.schedule_tab)
        self.checkbox_sql_server = QCheckBox("Backup SQL Server", self.schedule_tab)
        
        # Adiciona um layout horizontal para as checkboxes
        layout_checkboxes = QHBoxLayout()
        layout_checkboxes.addWidget(self.checkbox_sql_server)
        layout_checkboxes.addWidget(self.checkbox_mysql)
        
        # Adiciona os layouts ao layout principal
        layout_schedule.addLayout(layout_checkboxes)
        layout_schedule.addWidget(self.save_button_schedule)

        self.schedule_tab.setLayout(layout_schedule)

        # Carrega as configurações salvas e agenda os backups
        self.load_settings()
        self.schedule_backups()

    # Função para criar a aba de configurações
    def setup_settings_tab(self):
        self.layout = QGridLayout(self.settings_tab) # Define o tipo de layout

        # Configurações referentes ao layout do MySQL
        self.icon_mysql_username = QIcon("images\\db_user.png")
        self.label_mysql_username = QLabel(self.settings_tab)
        self.label_mysql_username.setPixmap(self.icon_mysql_username.pixmap(56, 56))
        self.mysql_username = QLineEdit(self.settings_tab)
        self.mysql_username.setPlaceholderText("MySQL Username")
        self.layout.addWidget(self.label_mysql_username, 0, 0)
        self.layout.addWidget(self.mysql_username, 0, 1)

        self.icon_mysql_password = QIcon("images\\database_password2.png")
        self.label_mysql_password = QLabel(self.settings_tab)
        self.label_mysql_password.setPixmap(self.icon_mysql_password.pixmap(56, 56))
        self.mysql_password = QLineEdit(self.settings_tab)
        self.mysql_password.setPlaceholderText("MySQL Password")
        self.mysql_password.setEchoMode(QLineEdit.Password) # Esconde a senha na digitação
        self.layout.addWidget(self.label_mysql_password, 1, 0)
        self.layout.addWidget(self.mysql_password, 1, 1)

        self.icon_mysql_port = QIcon("images\\port_icon.png")
        self.label_mysql_port = QLabel(self.settings_tab)
        self.label_mysql_port.setPixmap(self.icon_mysql_port.pixmap(56, 56))
        self.mysql_port = QLineEdit(self.settings_tab)
        self.mysql_port.setPlaceholderText("MySQL Port")
        self.layout.addWidget(self.label_mysql_port, 2, 0)
        self.layout.addWidget(self.mysql_port, 2, 1)

        # Configurações referentes ao layout do SQL Server
        self.icon_sql_server = QIcon("images\\server_icon.png")
        self.label_sql_server = QLabel(self.settings_tab)
        self.label_sql_server.setPixmap(self.icon_sql_server.pixmap(56, 56))
        self.sql_server = QLineEdit(self.settings_tab)
        self.sql_server.setPlaceholderText("SQL Server")
        self.layout.addWidget(self.label_sql_server, 0, 2)
        self.layout.addWidget(self.sql_server, 0, 3)

        self.icon_sql_username = QIcon("images\\db_user.png")
        self.label_sql_username = QLabel(self.settings_tab)
        self.label_sql_username.setPixmap(self.icon_sql_username.pixmap(56, 56))
        self.sql_username = QLineEdit(self.settings_tab)
        self.sql_username.setPlaceholderText("SQL Username")
        self.layout.addWidget(self.label_sql_username, 1, 2)
        self.layout.addWidget(self.sql_username, 1, 3)

        self.icon_sql_password = QIcon("images\\database_password2.png")
        self.label_sql_password = QLabel(self.settings_tab)
        self.label_sql_password.setPixmap(self.icon_sql_password.pixmap(56, 56))
        self.sql_password = QLineEdit(self.settings_tab)
        self.sql_password.setPlaceholderText("SQL Password")
        self.sql_password.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.label_sql_password, 2, 2)
        self.layout.addWidget(self.sql_password, 2, 3)

        self.icon_sql_database = QIcon("images\\database_icon.png")
        self.label_sql_database = QLabel(self.settings_tab)
        self.label_sql_database.setPixmap(self.icon_sql_database.pixmap(56, 56))
        self.sql_database = QLineEdit(self.settings_tab)
        self.sql_database.setPlaceholderText("SQL Database")
        self.layout.addWidget(self.label_sql_database, 3, 2)
        self.layout.addWidget(self.sql_database, 3, 3)

        self.icon_sql_port = QIcon("images\\port_icon.png")
        self.label_sql_port = QLabel(self.settings_tab)
        self.label_sql_port.setPixmap(self.icon_sql_port.pixmap(56, 56))
        self.sql_port = QLineEdit(self.settings_tab)
        self.sql_port.setPlaceholderText("SQL Port")
        self.layout.addWidget(self.label_sql_port, 4, 2)
        self.layout.addWidget(self.sql_port, 4, 3)

        # Adicionando botões para testar a conexão com MySQL e SQL Server
        self.test_mysql_button = QPushButton("Testar Conexão MySQL", self.settings_tab)
        self.layout.addWidget(self.test_mysql_button, 6, 0, 1, 2)  # Coluna 0, linha 6, colspan 2
        self.test_mysql_button.clicked.connect(self.test_mysql_connection)
        self.test_sql_server_button = QPushButton("Testar Conexão SQL Server", self.settings_tab)
        self.layout.addWidget(self.test_sql_server_button, 6, 2, 1, 2)  # Coluna 2, linha 6, colspan 2
        self.test_sql_server_button.clicked.connect(self.test_sql_server_connection)

        # Adicionando o botão na última linha
        self.save_button = QPushButton("Salvar Configurações", self.settings_tab)
        self.layout.addWidget(self.save_button, 5, 0, 1, 4)  # Coluna 0, linha 5, colspan 4
        self.save_button.clicked.connect(self.save_credentials)
    
    # Função fernet para criar uma chave e criptografar o texto    
    def encrypt_text(self, text):
        cipher_suite = Fernet(self.fernet_key)
        cipher_text = cipher_suite.encrypt(text.encode())
        return cipher_text.decode()
    
    # Função fernet para descriptografar o texto
    def decrypt_text(self, encrypted_text):
        cipher_suite = Fernet(self.fernet_key)
        decrypted_text = cipher_suite.decrypt(encrypted_text.encode())
        return decrypted_text.decode()
    
    # Função para testar a conexão com MySQL
    def test_mysql_connection(self):
        mysql_host = "localhost"
        mysql_username = self.mysql_username.text()
        mysql_password = self.mysql_password.text()
        mysql_port = self.mysql_port.text()

        # Tentativa de conexão com pymysql para versões >= 5.7
        if not (mysql_password and mysql_username and mysql_port):
            QMessageBox.information(self, "Testar conexão MySQL", "Preencha todos os campos do MySQL!")
            return 
        
        try:    
                connection = pymysql.connect(
                    host=mysql_host,
                    user=mysql_username,
                    password=mysql_password,
                    port=int(mysql_port),
                )
 
                QMessageBox.information(self, "Testar conexão MySQL", "Conexão com o MySQL bem-sucedida!") # Mensagem de sucesso

                connection.close() # Fechando a conexão
                return

        except pymysql.Error as e:
            pass

            # Tentativa de conexão com mysql-connector-python para versões < 5.7
            try:
                connection = mysql.connector.connect(
                    host=mysql_host,
                    user=mysql_username,
                    password=mysql_password,
                    port=int(mysql_port),
                )
               
                QMessageBox.information(self, "Testar conexão MySQL", "Conexão com o MySQL bem-sucedida!") # Mensagem de sucesso

                connection.close() # Fechando a conexão
                return

            except mysql.connector.Error as e:
                QMessageBox.critical(self, "Erro", f"Erro ao conectar ao MySQL: {str(e)}") # Mensagem de erro

    # Função para testar a conexão com SQL Server
    def test_sql_server_connection(self):
        sql_server = self.sql_server.text()
        sql_username = self.sql_username.text()
        sql_password = self.sql_password.text()
        sql_database = self.sql_database.text()
        sql_port = self.sql_port.text()

        if not(sql_server and sql_username and sql_password and sql_port):
            QMessageBox.information(self, "Testar conexão SQL Server", "Preencha o servidor, usuário, senha e porta!")
            return
        
        # Tentativa de conexão
        try:
            connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={sql_server},{sql_port};DATABASE={sql_database};UID={sql_username};PWD={sql_password};"

            connection = pyodbc.connect(connection_string)

            QMessageBox.information(self, "Testar conexão SQL Server", "Conexão com o SQL Server bem-sucedida!")

            connection.close()

        except pyodbc.Error as e:
            QMessageBox.critical(self, "Erro", f"Erro ao conectar ao SQL Server: {str(e)}")

    # Função para salvar as credenciais das conexões aos bancos de dados
    def save_credentials(self):
        self.fernet_key = get_key_from_file()
        
        config = configparser.ConfigParser()

        # Carrega o arquivo de configuração
        if os.path.exists('config/dbcredentials.ini'):
            config.read('config/dbcredentials.ini')

        if self.mysql_username.text() != "":
            if 'MySQL' not in config:
                config['MySQL'] = {}
            config['MySQL']['user'] = self.encrypt_text(self.mysql_username.text())

        if self.mysql_password.text() != "":
            if 'MySQL' not in config:
                config['MySQL'] = {}
            config['MySQL']['password'] = self.encrypt_text(self.mysql_password.text())

        if self.mysql_port.text() != "":
            if 'MySQL' not in config:
                config['MySQL'] = {}
            config['MySQL']['port'] = self.mysql_port.text()

        if self.sql_server.text() != "":
            if 'SQLServer' not in config:
                config['SQLServer'] = {}
            config['SQLServer']['server'] = self.encrypt_text(self.sql_server.text())

        if self.sql_username.text() != "":
            if 'SQLServer' not in config:
                config['SQLServer'] = {}
            config['SQLServer']['user'] = self.encrypt_text(self.sql_username.text())

        if self.sql_password.text() != "":
            if 'SQLServer' not in config:
                config['SQLServer'] = {}
            config['SQLServer']['password'] = self.encrypt_text(self.sql_password.text())

        if self.sql_database.text() != "":
            if 'SQLServer' not in config:
                config['SQLServer'] = {}
            config['SQLServer']['database'] = self.sql_database.text()

        if self.sql_port.text() != "":
            if 'SQLServer' not in config:
                config['SQLServer'] = {}
            config['SQLServer']['port'] = self.sql_port.text()

        # Escreva as configurações no arquivo credentials.ini
        with open('config/dbcredentials.ini', 'w') as configfile:
            config.write(configfile)

        # Exiba uma mensagem ou atualize a interface de usuário conforme necessário
        print("Configurações salvas com sucesso!")
    
    # Função para realizar o backup
    def backup(self, backup_mysql=True, backup_sql_server=True):
        configsettings = configparser.ConfigParser() # Carrega as informações do arquivo .ini nas seções MySQL e SQLServer
        configsettings.read("config\\settings.ini")
        
        configcredentials = configparser.ConfigParser()
        configcredentials.read("config\\dbcredentials.ini")

        # Verifica as opções de backup no arquivo settings.ini
        backup_mysql = configsettings.getboolean("Backup", "use_mysql", fallback=False)
        backup_sql_server = configsettings.getboolean("Backup", "use_sql_server", fallback=False)

        day_mapping = {
            'Monday': 'Segunda',
            'Tuesday': 'Terca',
            'Wednesday': 'Quarta',
            'Thursday': 'Quinta',
            'Friday': 'Sexta',
            'Saturday': 'Sabado',
            'Sunday': 'Domingo',
        }

        root_directory = os.getcwd()
        current_day = datetime.now().strftime("%A")
        translated_day = day_mapping.get(current_day, current_day)

        mysqldump_path = "C:\\Program Files (x86)\\MySQL\\MySQL Server 5.1\\bin\\mysqldump.exe"
        mysql_backup_folder = "mysql"
        sql_backup_folder = "sql"

        databases_mysql = []

        if configcredentials.has_section("MySQL") and backup_mysql:
            os.makedirs(os.path.join(root_directory, mysql_backup_folder), exist_ok=True)
            
            # Obtém as informações de conexão do arquivo .ini para MySQL
            encrypted_user_mysql = configcredentials.get("MySQL", "user")
            encrypted_password_mysql = configcredentials.get("MySQL", "password")
            port_mysql = configcredentials.get("MySQL", "port", fallback=3306)

            # Descriptografa as informações para MySQL
            user_mysql = self.decrypt_text(encrypted_user_mysql)
            password_mysql = self.decrypt_text(encrypted_password_mysql)

            databases_mysql = self.get_all_databases(user_mysql, password_mysql, port_mysql)
            
        # Lista de exceções para bancos de dados MySQL
        database_exceptions = ['test', 'information_schema', 'mysql']   

        for database in databases_mysql:
            if database not in database_exceptions:  # Verifica se o banco de dados não está na lista de exceções
                file_name_mysql = f"{mysql_backup_folder}\\{translated_day}_{database}.sql"
                destination_file_mysql = os.path.join(root_directory, file_name_mysql)
                command_mysql = f'"{mysqldump_path}" -u {user_mysql} -p{password_mysql} -P{port_mysql} {database} > "{destination_file_mysql}"'

                try:
                    result_mysql = subprocess.run(command_mysql, shell=True, capture_output=True, text=True, check=True)
                    success_message = f"MySQL: backup de {database} realizado em '{destination_file_mysql}'!"
                    print(success_message)
                    main_log.info(success_message)
                except subprocess.CalledProcessError as e:
                    error_message = f"Falha no backup da base de dados '{database}' do MySQL. Erro: {e.stderr}"
                    print(error_message)
                    error_log.error(error_message)

        if configcredentials.has_section("SQLServer") and backup_sql_server:
            os.makedirs(os.path.join(root_directory, sql_backup_folder), exist_ok=True)
            
            # Obtém as informações de conexão do arquivo .ini para SQL Server
            encrypted_user_sql_server = configcredentials.get("SQLServer", "user")
            encrypted_password_sql_server = configcredentials.get("SQLServer", "password")
            server_sql_server = configcredentials.get("SQLServer", "server")
            database_sql_server = configcredentials.get("SQLServer", "database")

            # Descriptografa as informações para SQL Server
            user_sql_server = self.decrypt_text(encrypted_user_sql_server)
            password_sql_server = self.decrypt_text(encrypted_password_sql_server)

            # Backup para o SQL Server
            file_name_sql_server = f"{sql_backup_folder}\\{translated_day}_{database_sql_server}.bak"
            destination_file_sql_server = os.path.join(root_directory, file_name_sql_server)
            command_sql_server = f'sqlcmd -s {server_sql_server} -d {database_sql_server} -U {user_sql_server} -P {password_sql_server} -Q "BACKUP DATABASE {database_sql_server} TO DISK=\'{destination_file_sql_server}\'"'
    
            try:
                result_sql_server = subprocess.run(command_sql_server, shell=True, capture_output=True, text=True, check=True)
                success_message = f"SQL: backup de {database_sql_server} realizado em '{destination_file_sql_server}'!"
                print(success_message)
                main_log.info(success_message)
            except subprocess.CalledProcessError as e:
                error_message = f"Falha no backup da base de dados {database_sql_server} do SQL. Erro: {e.stderr}"
                print(error_message)
                error_log.error(error_message)

    # Função para buscar todos os bancos de dados do MySQL e realizar o backup de todos
    def get_all_databases(self, user_mysql, password_mysql, port_mysql):
        try:
            connection = mysql.connector.connect( # Conecta ao servidor MySQL
                host='localhost',
                user=user_mysql,
                password=password_mysql,
                port=port_mysql
            )

            if connection.is_connected():
                success_message = f"Conexão com MySQL bem sucedida!"
                print(success_message)
                main_log.info(success_message)
                
                cursor = connection.cursor()

                # Executa o comando SQL para obter a lista de bancos de dados
                cursor.execute("SHOW DATABASES;")
                databases = [database[0] for database in cursor.fetchall()]

                cursor.close()
                connection.close()

                return databases
        except Error as e:
            error_message = f"Erro ao conectar ao MySQL:", e
            print(error_message)
            error_log.error(error_message)

        return []

    # Função para realizar backup de acordo com a opção marcada na aba configurações
    def backup_handler(self):
        backup_mysql = self.checkbox_mysql.isChecked()
        backup_sql_server = self.checkbox_sql_server.isChecked()
        self.backup(backup_mysql, backup_sql_server)  

    # Função para salvar as configurações
    def save_settings(self):
        config = configparser.ConfigParser()

        # Configuração para os dias
        config.add_section("Days")
        for day, checkbox in self.day_checkboxes.items():
            config.set("Days", day, str(checkbox.isChecked()))

        # Configuração para os horários
        config.add_section("Time")
        for day, time_edit in self.time_edits.items():
            config.set("Time", day, time_edit.text())
            
        # Adicione informações da seção Backup com base nas checkboxes
        config.add_section("Backup")
        config.set("Backup", "use_mysql", str(self.checkbox_mysql.isChecked()))
        config.set("Backup", "use_sql_server", str(self.checkbox_sql_server.isChecked()))    

        # Salva as configurações no arquivo .ini
        with open("config\\settings.ini", "w") as configfile:
            config.write(configfile)

        self.schedule_backups()

     # Função para carregar as configurações do arquivo settings.ini
    def load_settings(self):
        try:
            config = configparser.ConfigParser()
            config.read("config\\settings.ini")

            # Carrega as configurações para os dias
            if config.has_section("Days"):
                for day, checkbox in self.day_checkboxes.items():
                    if config.has_option("Days", day):
                        checked = config.getboolean("Days", day)
                        checkbox.setChecked(checked)

            # Carrega as configurações para os horários
            if config.has_section("Time"):
                for day, time_edit in self.time_edits.items():
                    if config.has_option("Time", day):
                        time = config.get("Time", day)
                        time_edit.setText(time)

            # Carrega as configurações para o backup MySQL e SQL Server
            if config.has_section("Backup"):
                if config.has_option("Backup", "use_mysql"):
                    mysql_checked = config.getboolean("Backup", "use_mysql")
                    self.checkbox_mysql.setChecked(mysql_checked)

                if config.has_option("Backup", "use_sql_server"):
                    sql_server_checked = config.getboolean("Backup", "use_sql_server")
                    self.checkbox_sql_server.setChecked(sql_server_checked)
            
        except configparser.Error as e:
            error_message = f"O arquivo de configurações 'settings.ini' pode estar ausente ou incorreto: {e}"
            print(error_message, e)
            error_log.error(error_message)
            pass
        
        self.schedule_backups()
    
    # Função para agendar os backups
    def schedule_backups(self):
        schedule.clear() # Limpa todos os trabalhos agendados

        try:
            config = configparser.ConfigParser()
            config.read("config/settings.ini")

            # Agende backups com base nas configurações
            if config.has_section("Days") and config.has_section("Time"):
                for day, checkbox in self.day_checkboxes.items():
                    if config.has_option("Days", day) and config.has_option("Time", day):
                        checked = config.getboolean("Days", day)
                        if checked:
                            time = config.get("Time", day)
                            if time:
                                schedule.every().day.at(time).do(self.backup_handler)  # Agende o backup para esse dia e horário
                                
        except configparser.Error as e:
            error_message = f"O arquivo de configurações 'settings.ini' pode estar ausente ou incorreto: {e}"
            print(error_message, e)
            error_log.error(error_message)
            pass

    # Função para minimizar o programa quando fechar a tela principal
    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()

    def new_option(self):
        self.hide()  # Esconde a janela principal
        self.login_screen.show()  # Chama a tela de login

class ScheduleThread(QThread):
    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

# Cria a aplicação e as janelas
def main():
    global app
    app = QApplication(sys.argv) # Define o tipo de aplicação
    qdarktheme.setup_theme() # Aplica o tema escuro
    main_screen = MainWindow(None)  # Cria a janela principal sem referência para a tela de login
    login_screen = LoginScreen(main_screen)  # Cria a tela de login com referência para a janela principal
    main_screen.login_screen = login_screen  # Atualiza a referência para a tela de login na janela principal
    main_screen.hide()  # Esconde a janela principal

    # Carrega as configurações e agenda os backups ao iniciar o programa
    main_screen.load_settings()
    main_screen.schedule_backups()

    schedule_thread = ScheduleThread()  # Cria e inicia a thread de agendamento
    schedule_thread.start()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
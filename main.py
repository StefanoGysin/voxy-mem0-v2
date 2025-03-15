#!/usr/bin/env python3
"""
Aplicativo Voxy-Mem0-v2 - Assistente com Memória Vetorial
Interface gráfica para o assistente Voxy-Mem0 com autenticação e memória persistente.
"""

import os
import sys
import logging
import traceback
from dotenv import load_dotenv
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont

# Configuração de logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"voxy-mem0-v2_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("voxy-app")

# Importa módulos do projeto
from ui.login_window import LoginWindow
from ui.chat_window import ChatWindow
from utils.db_setup import setup_database

# Informações da versão
__version__ = "2.0.0"
__author__ = "Voxy Team"

class VoxyApp:
    """
    Classe principal do aplicativo Voxy-Mem0-v2
    Gerencia as janelas e o fluxo de autenticação/chat
    """
    def __init__(self):
        """
        Inicializa o aplicativo
        """
        # Carrega as variáveis de ambiente
        load_dotenv()
        
        # Inicializa a aplicação Qt
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Voxy-Mem0")
        self.app.setApplicationVersion(__version__)
        
        # Estilo global
        self.set_global_style()
        
        # Inicializa as janelas
        self.login_window = None
        self.chat_window = None
        
        # Configurar tratamento de exceções não tratadas
        sys.excepthook = self.handle_exception
    
    def set_global_style(self):
        """
        Define o estilo global da aplicação
        """
        self.app.setStyle("Fusion")
        
        # Estilo global para todos os widgets
        self.app.setStyleSheet("""
            QMainWindow, QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            QLabel {
                color: #212529;
            }
        """)
    
    def show_splash_screen(self):
        """
        Mostra a tela de splash durante a inicialização
        """
        # Se houver um arquivo de splash, use-o
        splash_path = os.path.join("assets", "splash.png")
        
        if os.path.exists(splash_path):
            pixmap = QPixmap(splash_path)
        else:
            # Cria um pixmap vazio
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.white)
        
        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        
        # Adiciona texto ao splash
        splash.showMessage(
            f"Voxy-Mem0 v{__version__}\nInicializando...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            Qt.GlobalColor.black
        )
        
        splash.show()
        self.app.processEvents()
        
        # Configuração do banco de dados
        logger.info("Verificando configuração do banco de dados...")
        database_ready = setup_database()
        
        if not database_ready:
            splash.close()
            QMessageBox.critical(
                None,
                "Erro de Configuração",
                "Não foi possível configurar o banco de dados.\n"
                "Verifique os logs e as configurações no arquivo .env."
            )
            return False
        
        # Dá tempo para mostrar o splash
        QTimer.singleShot(1500, splash.close)
        
        return True
    
    def start(self):
        """
        Inicia a aplicação
        """
        try:
            logger.info(f"Iniciando Voxy-Mem0-v2 v{__version__}")
            
            # Mostra a tela de splash
            if not self.show_splash_screen():
                return 1
            
            # Inicializa a janela de login
            self.login_window = LoginWindow()
            self.login_window.login_successful.connect(self.on_login_successful)
            self.login_window.show()
            
            # Executa o loop principal
            return self.app.exec()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar aplicação: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                None,
                "Erro Fatal",
                f"Ocorreu um erro ao iniciar a aplicação:\n{str(e)}\n\n"
                "Verifique os logs para mais detalhes."
            )
            return 1
    
    def on_login_successful(self, user_id):
        """
        Callback chamado quando o login é bem-sucedido
        
        Args:
            user_id: ID do usuário que fez login
        """
        logger.info(f"Login bem-sucedido para o usuário: {user_id}")
        
        # Esconde a janela de login
        if self.login_window:
            self.login_window.hide()
        
        # Cria e mostra a janela de chat
        self.chat_window = ChatWindow(user_id)
        self.chat_window.logout_requested.connect(self.on_logout_requested)
        self.chat_window.show()
    
    def on_logout_requested(self):
        """
        Callback chamado quando o logout é solicitado
        """
        logger.info("Logout solicitado")
        
        # Fecha a janela de chat
        if self.chat_window:
            self.chat_window.close()
            self.chat_window = None
        
        # Mostra a janela de login novamente
        if self.login_window:
            self.login_window.show()
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Manipula exceções não tratadas
        
        Args:
            exc_type: Tipo da exceção
            exc_value: Valor da exceção
            exc_traceback: Traceback da exceção
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # Ctrl+C, não mostra mensagem
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Registra o erro
        logger.error("Exceção não tratada:", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Mostra mensagem ao usuário
        error_msg = f"{exc_type.__name__}: {exc_value}"
        QMessageBox.critical(
            None,
            "Erro Inesperado",
            f"Ocorreu um erro inesperado:\n{error_msg}\n\n"
            "A aplicação pode estar em um estado instável.\n"
            "Recomenda-se reiniciar o aplicativo."
        )

def main():
    """
    Função principal do aplicativo
    """
    app = VoxyApp()
    return app.start()

if __name__ == "__main__":
    sys.exit(main()) 
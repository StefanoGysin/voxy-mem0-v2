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
import colorama

# Inicializa colorama para suporte de cores em todos os terminais
colorama.init()

# Classe de formatação para melhorar a legibilidade do log no terminal
class ColoredFormatter(logging.Formatter):
    """
    Formatador personalizado que adiciona cores e símbolos para diferentes níveis de log.
    """
    # Cores ANSI para diferentes níveis de log
    COLORS = {
        'DEBUG': colorama.Fore.CYAN,
        'INFO': colorama.Fore.GREEN,
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'CRITICAL': colorama.Fore.RED + colorama.Style.BRIGHT
    }

    # Símbolos para diferentes níveis de log (ASCII para compatibilidade)
    SYMBOLS = {
        'DEBUG': '[D]',
        'INFO': '[I]',
        'WARNING': '[W]',
        'ERROR': '[E]',
        'CRITICAL': '[C]'
    }

    # Símbolos Unicode (usados apenas se o terminal suportar)
    UNICODE_SYMBOLS = {
        'DEBUG': '🔍',
        'INFO': '✓',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }

    # Cores para diferentes componentes
    COMPONENT_COLORS = {
        'voxy-app': colorama.Fore.MAGENTA + colorama.Style.BRIGHT,
        'voxy-memory': colorama.Fore.BLUE + colorama.Style.BRIGHT,
        'voxy-auth': colorama.Fore.YELLOW + colorama.Style.BRIGHT,
        'voxy-db-setup': colorama.Fore.CYAN + colorama.Style.BRIGHT,
        'voxy-ui': colorama.Fore.GREEN + colorama.Style.BRIGHT,
        'voxy-performance': colorama.Fore.RED + colorama.Style.BRIGHT
    }

    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, *, use_unicode=None):
        super().__init__(fmt, datefmt, style, validate)
        
        # Determina se devemos usar símbolos Unicode
        # Verificar se estamos no Windows (mais propenso a problemas de codificação)
        self.use_unicode = use_unicode
        if self.use_unicode is None:
            self.use_unicode = not (sys.platform == 'win32')
            
        # Em Windows, verificar se estamos no terminal moderno
        if self.use_unicode is None and sys.platform == 'win32':
            # Windows Terminal e outros terminais modernos têm TERM_PROGRAM ou WT_SESSION
            self.use_unicode = bool(os.environ.get('TERM_PROGRAM') or os.environ.get('WT_SESSION'))

    def format(self, record):
        # Formato padrão para arquivo de log (sem cores)
        if not hasattr(record, 'terminal_format') or not record.terminal_format:
            return super().format(record)
        
        try:
            # Adiciona cor ao nível de log
            levelname = record.levelname
            
            # Escolhe símbolos ASCII ou Unicode com base na configuração
            symbol_dict = self.UNICODE_SYMBOLS if self.use_unicode else self.SYMBOLS
            symbol = symbol_dict.get(levelname, '')
            
            color = self.COLORS.get(levelname, colorama.Fore.WHITE)
            
            # Adiciona cor ao nome do componente
            component_color = colorama.Fore.WHITE
            for component, comp_color in self.COMPONENT_COLORS.items():
                if component in record.name:
                    component_color = comp_color
                    break
            
            # Formata a mensagem com cores e símbolos
            colored_levelname = f"{color}{symbol} {levelname}{colorama.Style.RESET_ALL}"
            colored_name = f"{component_color}{record.name}{colorama.Style.RESET_ALL}"
            
            # Formata a data/hora com cor cinza
            asctime = self.formatTime(record, self.datefmt)
            colored_time = f"{colorama.Fore.WHITE}{asctime}{colorama.Style.RESET_ALL}"
            
            # Formata a mensagem
            message = record.getMessage()
            
            # Adiciona cor à mensagem para erros e críticos
            if record.levelno >= logging.ERROR:
                message = f"{color}{message}{colorama.Style.RESET_ALL}"
            
            # Monta o formato final
            return f"{colored_time} | {colored_name} | {colored_levelname} | {message}"
        except Exception as e:
            # Em caso de erro na formatação, use formato simples
            return f"{record.asctime} - {record.name} - {record.levelname} - {record.getMessage()}"

# Configuração de logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"voxy-mem0-v2_{datetime.now().strftime('%Y%m%d')}.log")

# Formatadores
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
terminal_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Handler para arquivo
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(file_formatter)

# Handler para terminal
terminal_handler = logging.StreamHandler()
terminal_handler.setFormatter(terminal_formatter)

# Configuração root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(terminal_handler)

# Função para adicionar contexto de formatação terminal
def add_terminal_format(record):
    record.terminal_format = True
    return True

# Adiciona filtro para identificar logs para terminal
terminal_handler.addFilter(add_terminal_format)

# Logger principal da aplicação
logger = logging.getLogger("voxy-app")
logger.info(f"Sistema de log inicializado - Voxy-Mem0-v2")

# Importa módulos do projeto
from ui.login_window import LoginWindow
from ui.chat_window import ChatWindow
from utils.db_setup import setup_database
from utils.performance import performance_monitor

# Informações da versão
__version__ = "2.3.0"
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
        
        # Configura monitoramento de desempenho
        self._setup_performance_monitoring()
        
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
    
    def _setup_performance_monitoring(self):
        """
        Configura o monitoramento de desempenho com base nas variáveis de ambiente
        """
        # Verifica se o monitoramento está ativado
        monitoring_enabled = os.getenv("PERFORMANCE_MONITORING", "true").lower() == "true"
        
        # Configura o limite para operações lentas (em ms)
        slow_threshold = int(os.getenv("PERFORMANCE_SLOW_OPERATION_THRESHOLD", "500"))
        
        # Configura o nível de log para alertas de desempenho
        log_level_name = os.getenv("PERFORMANCE_LOG_LEVEL", "WARNING")
        log_level = getattr(logging, log_level_name, logging.WARNING)
        
        # Configura o logger de desempenho
        perf_logger = logging.getLogger("voxy-performance")
        perf_logger.setLevel(log_level)
        
        # Ativa ou desativa o monitoramento
        if monitoring_enabled:
            performance_monitor.enable()
            logger.info(f"Monitoramento de desempenho ativado (limite: {slow_threshold}ms)")
            
            # Configura limites para operações críticas
            performance_monitor.set_threshold("retrieve_memories", slow_threshold)
            performance_monitor.set_threshold("process_message", slow_threshold * 2)
            performance_monitor.set_threshold("chat_completion", slow_threshold * 3)
        else:
            performance_monitor.disable()
            logger.info("Monitoramento de desempenho desativado")
    
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
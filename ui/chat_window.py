"""
Janela de chat para o aplicativo Voxy-Mem0-v2
"""

import os
import sys
import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QScrollArea,
    QSplitter, QFrame, QSizePolicy, QSpacerItem, QMenu,
    QTextBrowser, QProgressBar, QToolBar, QMessageBox, QDialog,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QThread, QObject, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction, QTextCursor, QColor, QPalette

# Importa módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import get_auth_instance, get_user_system_prompt, save_user_system_prompt
from utils.memory_manager import get_memory_manager

# Configuração de logging
logger = logging.getLogger("voxy-ui-chat")

# Definição de cores para tema escuro
THEME = {
    "bg_primary": "#1E1E2E",          # Fundo principal
    "bg_secondary": "#252536",         # Fundo secundário
    "bg_tertiary": "#313244",          # Elementos de fundo terciário
    "accent": "#89B4FA",               # Cor de destaque
    "accent_darker": "#74A0F0",        # Cor de destaque mais escura (hover)
    "text_primary": "#CDD6F4",         # Texto principal
    "text_secondary": "#A6ADC8",       # Texto secundário
    "text_muted": "#7F849C",           # Texto menos importante
    "user_message_bg": "#1E3A8A",      # Fundo da mensagem do usuário
    "user_message_border": "#2563EB",  # Borda da mensagem do usuário
    "assistant_message_bg": "#313244", # Fundo da mensagem do assistente
    "assistant_message_border": "#45475A", # Borda da mensagem do assistente
    "system_message_bg": "#2E1F42",    # Fundo da mensagem do sistema
    "system_message_border": "#7E3AF2", # Borda da mensagem do sistema
    "error_message_bg": "#4C1D24",     # Fundo da mensagem de erro
    "error_message_border": "#F87171", # Borda da mensagem de erro
    "error_text": "#F87171",           # Texto de erro
    "success_text": "#4ADE80",         # Texto de sucesso
    "button_primary": "#2563EB",       # Botão primário
    "button_primary_hover": "#1D4ED8", # Botão primário hover
    "button_primary_text": "#F8FAFC",  # Texto do botão primário
    "button_secondary": "#334155",     # Botão secundário
    "button_secondary_hover": "#475569", # Botão secundário hover
    "button_secondary_text": "#F1F5F9", # Texto do botão secundário
    "button_disabled": "#475569",      # Botão desabilitado
    "button_disabled_text": "#94A3B8", # Texto do botão desabilitado
    "input_bg": "#313244",             # Fundo do campo de entrada
    "input_border": "#45475A",         # Borda do campo de entrada
    "input_text": "#CDD6F4",           # Texto do campo de entrada
    "progress_bar": "#2563EB",         # Cor da barra de progresso
    "progress_bar_bg": "#1E293B",      # Fundo da barra de progresso
    "link": "#89B4FA",                 # Cor de links
    "link_hover": "#74A0F0",           # Cor de links (hover)
    "code_bg": "#252536",              # Fundo de código
    "toolbar_bg": "#1A1B26",           # Fundo da barra de ferramentas
}

class MessageWorker(QObject):
    """
    Worker para processar mensagens em uma thread separada
    """
    response_ready = pyqtSignal(dict)  # Alterado para enviar um dicionário com a resposta e memórias
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self, memory_manager, user_id):
        super().__init__()
        self.memory_manager = memory_manager
        self.user_id = user_id
        self.message = ""
    
    def set_message(self, message):
        """Define a mensagem a ser processada"""
        self.message = message
    
    def process_message(self):
        """Processa a mensagem e emite o sinal com a resposta"""
        try:
            # Simula progresso
            for i in range(1, 101):
                if i % 5 == 0:  # Atualiza a cada 5%
                    self.progress_update.emit(i)
            
            # A mensagem agora é o histórico completo de mensagens
            # Não precisamos criar uma nova lista
            response = self.memory_manager.process_message(self.message, self.user_id)
            
            # Emite a resposta completa com memórias
            self.response_ready.emit(response)
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            self.error_occurred.emit(f"Erro ao processar mensagem: {str(e)}")

class SystemPromptDialog(QDialog):
    """
    Diálogo para configuração do prompt do sistema
    """
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Configurar Prompt do Sistema")
        self.resize(600, 400)
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Instrução
        instruction_label = QLabel("Personalize o prompt do sistema utilizado pelo assistente:")
        instruction_label.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 14px;")
        layout.addWidget(instruction_label)
        
        # Explicação
        explanation_label = QLabel("Este prompt define a personalidade e comportamento do assistente. "
                                 "Modificá-lo afetará como o assistente responde às suas perguntas.")
        explanation_label.setWordWrap(True)
        explanation_label.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 12px;")
        layout.addWidget(explanation_label)
        
        # Campo de texto para o prompt
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Digite o prompt do sistema aqui...")
        self.prompt_text.setText(get_user_system_prompt(self.user_id))
        self.prompt_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {THEME['input_bg']};
                color: {THEME['input_text']};
                border: 1px solid {THEME['input_border']};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        layout.addWidget(self.prompt_text)
        
        # Indicador de status
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False) # Inicialmente oculto
        self.status_label.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Botões
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_prompt)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        button_box.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['button_secondary']};
                color: {THEME['button_secondary_text']};
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {THEME['button_secondary_hover']};
            }}
            QPushButton[text="Salvar"] {{
                background-color: {THEME['button_primary']};
                color: {THEME['button_primary_text']};
            }}
            QPushButton[text="Salvar"]:hover {{
                background-color: {THEME['button_primary_hover']};
            }}
        """)
        layout.addWidget(button_box)
        
        # Configura o layout
        self.setLayout(layout)
    
    def show_status(self, message, is_error=False):
        """
        Exibe uma mensagem de status no diálogo
        
        Args:
            message (str): Mensagem a ser exibida
            is_error (bool): Se True, a mensagem é um erro
        """
        color = THEME['error_text'] if is_error else THEME['success_text']
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        self.status_label.setVisible(True)
    
    def save_prompt(self):
        """
        Salva o prompt do sistema e exibe feedback imediato
        """
        prompt = self.get_prompt()
        if not prompt.strip():
            self.show_status("O prompt não pode estar vazio. Por favor, digite um prompt válido.", True)
            return
        
        success = save_user_system_prompt(self.user_id, prompt)
        
        if success:
            self.show_status("Prompt salvo com sucesso!", False)
            # Espera 1.5 segundos e então aceita o diálogo
            QTimer.singleShot(1500, self.accept)
        else:
            self.show_status("Erro ao salvar prompt. Por favor, tente novamente.", True)
    
    def get_prompt(self):
        """
        Retorna o texto do prompt personalizado
        
        Returns:
            str: Texto do prompt personalizado
        """
        return self.prompt_text.toPlainText()

class ChatWindow(QMainWindow):
    """
    Janela principal de chat do aplicativo
    """
    logout_requested = pyqtSignal()
    
    def __init__(self, user_id):
        super().__init__()
        
        # Armazena o ID do usuário
        self.user_id = user_id
        
        # Configuração da janela
        self.setWindowTitle("Voxy-Mem0 v2 - Chat")
        self.setMinimumSize(900, 700)
        
        # Inicialização dos serviços
        try:
            self.auth = get_auth_instance()
            self.memory_manager = get_memory_manager()
            logger.info("Serviços inicializados com sucesso")
            
            # Verifica se o usuário ainda está logado
            if not self.auth.is_logged_in():
                logger.warning("Usuário não está logado")
                self.logout_requested.emit()
                return
            
            # Thread de processamento de mensagens
            self.message_thread = QThread()
            self.message_worker = MessageWorker(self.memory_manager, self.user_id)
            self.message_worker.moveToThread(self.message_thread)
            
            # Conecta sinais da thread
            self.message_worker.response_ready.connect(self._add_assistant_message)
            self.message_worker.error_occurred.connect(self._show_error)
            self.message_worker.progress_update.connect(self._update_progress)
            self.message_thread.started.connect(self.message_worker.process_message)
            
            # Inicializa a UI
            self._init_ui()
            
            # Aplicar estilo global para tema escuro (MOVIDO PARA DEPOIS DA INICIALIZAÇÃO DA UI)
            self._apply_dark_theme()
            
            # Inicializa histórico de chat
            self._message_history = []
            
            # Adiciona mensagem de boas-vindas
            self._add_system_message("Bem-vindo ao Voxy-Mem0! Como posso ajudar você hoje?")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar serviços: {str(e)}")
            QMessageBox.critical(
                self, 
                "Erro de Inicialização", 
                f"Não foi possível inicializar os serviços necessários.\nErro: {str(e)}"
            )
            # Emite sinal para voltar à tela de login
            self.logout_requested.emit()
    
    def _apply_dark_theme(self):
        """Aplica o tema escuro para todos os componentes da janela"""
        # Define as cores do tema
        THEME = {
            "bg_primary": "#1E1E2E",          # Fundo principal
            "bg_secondary": "#252536",         # Fundo secundário
            "bg_tertiary": "#313244",          # Elementos de fundo terciário
            "accent": "#89B4FA",               # Cor de destaque
            "accent_darker": "#74A0F0",        # Cor de destaque mais escura (hover)
            "text_primary": "#CDD6F4",         # Texto principal
            "text_secondary": "#A6ADC8",       # Texto secundário
            "text_muted": "#7F849C",           # Texto menos importante
            "button_primary": "#2563EB",       # Botão primário
            "button_primary_hover": "#1D4ED8", # Botão primário hover
            "button_primary_text": "#F8FAFC",  # Texto do botão primário
            "button_secondary": "#334155",     # Botão secundário
            "button_secondary_hover": "#475569", # Botão secundário hover
            "button_secondary_text": "#F1F5F9", # Texto do botão secundário
            "button_disabled": "#475569",      # Botão desabilitado
            "button_disabled_text": "#94A3B8", # Texto do botão desabilitado
            "input_bg": "#313244",             # Fundo do campo de entrada
            "input_border": "#45475A",         # Borda do campo de entrada
            "input_text": "#CDD6F4",           # Texto do campo de entrada
            "user_msg_bg": "#313244",          # Fundo da mensagem do usuário
            "user_msg_border": "#45475A",      # Borda da mensagem do usuário
            "bot_msg_bg": "#252536",           # Fundo da mensagem do assistente
            "bot_msg_border": "#45475A",       # Borda da mensagem do assistente
            "code_bg": "#1E1E2E",              # Fundo de blocos de código
            "code_text": "#A6E3A1",            # Texto de blocos de código
            "accent_green": "#94E2D5",         # Cor de destaque verde
            "accent_blue": "#89B4FA",          # Cor de destaque azul
            "accent_red": "#F38BA8",           # Cor de destaque vermelha para errors
            "positive": "#A6E3A1",             # Cor positiva (sucesso)
            "negative": "#F38BA8",             # Cor negativa (erro)
            "warning": "#F9E2AF",              # Cor de alerta
            "hover_overlay": "rgba(30, 30, 46, 0.7)" # Overlay para efeitos de hover
        }
        
        # Configura a paleta de cores global da aplicação
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(THEME["bg_primary"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(THEME["text_primary"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(THEME["bg_secondary"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(THEME["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(THEME["bg_secondary"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(THEME["text_primary"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(THEME["text_primary"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(THEME["button_secondary"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(THEME["button_secondary_text"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(THEME["accent"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(THEME["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(THEME["text_primary"]))
        self.setPalette(palette)
        
        # Define os estilos globais
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {THEME["bg_primary"]};
                color: {THEME["text_primary"]};
            }}
            
            QLabel {{
                color: {THEME["text_primary"]};
            }}
            
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {THEME["input_bg"]};
                color: {THEME["input_text"]};
                border: 1px solid {THEME["input_border"]};
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {THEME["accent"]};
                selection-color: white;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {THEME["accent"]};
            }}
            
            QPushButton {{
                background-color: {THEME["button_secondary"]};
                color: {THEME["button_secondary_text"]};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {THEME["button_secondary_hover"]};
            }}
            
            QPushButton:disabled {{
                background-color: {THEME["button_disabled"]};
                color: {THEME["button_disabled_text"]};
            }}
            
            QPushButton#sendButton {{
                background-color: {THEME["button_primary"]};
                color: {THEME['button_primary_text']};
            }}
            
            QPushButton#sendButton:hover {{
                background-color: {THEME["button_primary_hover"]};
            }}
            
            QScrollArea {{
                border: none;
                background-color: {THEME["bg_primary"]};
            }}
            
            QScrollBar:vertical {{
                border: none;
                background-color: {THEME["bg_primary"]};
                width: 14px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {THEME["button_secondary"]};
                min-height: 30px;
                border-radius: 7px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {THEME["button_secondary_hover"]};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QToolBar {{
                background-color: {THEME["bg_secondary"]};
                border-bottom: 1px solid {THEME["input_border"]};
                spacing: 5px;
                padding: 5px;
            }}
            
            QToolButton {{
                background-color: {THEME["button_secondary"]};
                color: {THEME["button_secondary_text"]};
                border: none;
                border-radius: 4px;
                padding: 6px;
            }}
            
            QToolButton:hover {{
                background-color: {THEME["button_secondary_hover"]};
            }}
            
            QProgressBar {{
                border: 1px solid {THEME["input_border"]};
                border-radius: 4px;
                background-color: {THEME["bg_tertiary"]};
                color: {THEME["text_primary"]};
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {THEME["accent"]};
                border-radius: 2px;
            }}
            
            QStatusBar {{
                background-color: {THEME["bg_secondary"]};
                color: {THEME["text_secondary"]};
                border-top: 1px solid {THEME["input_border"]};
                padding: 2px;
                font-size: 12px;
            }}
            
            #chatWidget, #scrollAreaWidgetContents {{
                background-color: {THEME["bg_primary"]};
            }}
            
            .user-message {{
                background-color: {THEME["user_msg_bg"]};
                border: 1px solid {THEME["user_msg_border"]};
                border-radius: 8px;
                padding: 10px;
                margin: 5px 10px 5px 50px;
            }}
            
            .bot-message {{
                background-color: {THEME["bot_msg_bg"]};
                border: 1px solid {THEME["bot_msg_border"]};
                border-radius: 8px;
                padding: 10px;
                margin: 5px 50px 5px 10px;
            }}
            
            QFrame#messageFrame {{
                border: none;
                background-color: transparent;
            }}
            
            QLabel#userName {{
                color: {THEME["accent"]};
                font-weight: bold;
            }}
            
            QLabel#botName {{
                color: {THEME["accent_green"]};
                font-weight: bold;
            }}
            
            QLabel#messageTime {{
                color: {THEME["text_muted"]};
                font-size: 11px;
            }}
            
            QLabel#messageContent {{
                color: {THEME["text_primary"]};
                background-color: transparent;
            }}
            
            QMenu {{
                background-color: {THEME["bg_secondary"]};
                color: {THEME["text_primary"]};
                border: 1px solid {THEME["input_border"]};
                padding: 5px 0px;
            }}
            
            QMenu::item {{
                padding: 6px 25px 6px 25px;
                border: 1px solid transparent;
            }}
            
            QMenu::item:selected {{
                background-color: {THEME["button_secondary_hover"]};
            }}
        """)
        
        # Configura estilo específico para widgets individuais, verificando se já existem
        if hasattr(self, 'message_input') and self.message_input is not None:
            self.message_input.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {THEME["input_bg"]};
                    color: {THEME['input_text']};
                    border: 1px solid {THEME['input_border']};
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                }}
                
                QTextEdit:focus {{
                    border: 1px solid {THEME["accent"]};
                }}
            """)
        
        if hasattr(self, 'send_button') and self.send_button is not None:
            self.send_button.setObjectName("sendButton")
            self.send_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME["button_primary"]};
                    color: {THEME['button_primary_text']};
                    border-radius: 8px;
                    padding: 10px 15px;
                    font-weight: bold;
                    font-size: 14px;
                    margin: 0px 5px;
                }}
                
                QPushButton:hover {{
                    background-color: {THEME["button_primary_hover"]};
                }}
                
                QPushButton:disabled {{
                    background-color: {THEME['button_disabled']};
                    color: {THEME['button_disabled_text']};
                }}
            """)
        
        if hasattr(self, 'scroll_area') and self.scroll_area is not None:
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    border: none;
                    background-color: {THEME["bg_primary"]};
                }}
                
                QWidget#scrollAreaWidgetContents {{
                    background-color: {THEME["bg_primary"]};
                    border: none;
                }}
            """)
        
        if hasattr(self, 'statusbar') and self.statusbar is not None:
            self.statusbar.setStyleSheet(f"""
                QStatusBar {{
                    background-color: {THEME["bg_secondary"]};
                    color: {THEME["text_secondary"]};
                    padding: 5px;
                }}
                
                QStatusBar::item {{
                    border: none;
                }}
            """)
        
        if hasattr(self, 'toolbar') and self.toolbar is not None:
            self.toolbar.setStyleSheet(f"""
                QToolBar {{
                    background-color: {THEME["bg_secondary"]};
                    border: none;
                    border-bottom: 1px solid {THEME["input_border"]};
                    padding: 5px;
                    spacing: 5px;
                }}
            """)
    
    def _init_ui(self):
        """Inicializa a interface gráfica"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra de ferramentas
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet(f"background-color: {THEME['toolbar_bg']}; border: none;")
        
        # Ações da barra de ferramentas
        logout_action = QAction("Sair", self)
        logout_action.setStatusTip("Sair da conta")
        logout_action.triggered.connect(self._handle_logout)
        
        clear_action = QAction("Limpar Chat", self)
        clear_action.setStatusTip("Limpar o histórico de chat atual")
        clear_action.triggered.connect(self._clear_chat)
        
        # Nova ação para limpar memórias
        clear_memories_action = QAction("Limpar Memórias", self)
        clear_memories_action.setStatusTip("Limpar todas as memórias armazenadas do usuário atual")
        clear_memories_action.triggered.connect(self._clear_memories)
        
        # Nova ação para configurações
        settings_action = QAction("Configurações", self)
        settings_action.setStatusTip("Configurar o comportamento do assistente")
        settings_action.triggered.connect(self._show_settings)
        
        # Adiciona ações à barra de ferramentas
        toolbar.addAction(logout_action)
        toolbar.addAction(clear_action)
        toolbar.addAction(clear_memories_action)
        toolbar.addAction(settings_action)
        
        # Adiciona a barra de ferramentas ao layout
        main_layout.addWidget(toolbar)
        
        # Área de chat
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(20, 20, 20, 20)
        chat_layout.setSpacing(10)
        
        # Área de rolagem para as mensagens
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Widget de conteúdo da área de rolagem
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {THEME['bg_primary']};")
        self.chat_layout = QVBoxLayout(scroll_content)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(15)
        
        # Adiciona espaçador no final para empurrar as mensagens para o topo
        self.chat_layout.addStretch()
        
        # Configura a área de rolagem
        scroll_area.setWidget(scroll_content)
        
        # Adiciona a área de rolagem ao layout principal
        chat_layout.addWidget(scroll_area)
        
        # Barra de progresso para indicar processamento
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {THEME['progress_bar_bg']};
                border-radius: 3px;
                height: 6px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {THEME['progress_bar']};
                border-radius: 3px;
            }}
        """)
        
        chat_layout.addWidget(self.progress_bar)
        
        # Área de entrada de mensagem
        input_layout = QHBoxLayout()
        
        # Campo de texto
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Digite sua mensagem aqui...")
        self.message_input.setMaximumHeight(80)
        self.message_input.textChanged.connect(self._on_text_changed)
        self.message_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {THEME['input_bg']};
                color: {THEME['input_text']};
                border: 1px solid {THEME['input_border']};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        
        # Botão de envio
        self.send_button = QPushButton("Enviar")
        self.send_button.setMinimumHeight(40)
        self.send_button.setMaximumWidth(100)
        self.send_button.clicked.connect(self._send_message)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['button_primary']};
                color: {THEME['button_primary_text']};
                border-radius: 4px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {THEME['button_primary_hover']};
            }}
            QPushButton:disabled {{
                background-color: {THEME['button_disabled']};
                color: {THEME['button_disabled_text']};
            }}
        """)
        self.send_button.setEnabled(False)
        
        # Adiciona widgets ao layout de entrada
        input_layout.addWidget(self.message_input, 7)
        input_layout.addWidget(self.send_button, 1)
        
        # Adiciona o layout de entrada ao layout principal
        chat_layout.addLayout(input_layout)
        
        # Adiciona o layout de chat ao layout principal
        main_layout.addLayout(chat_layout, 1)
        
        # Conecta eventos de teclas
        self.message_input.installEventFilter(self)
    
    def eventFilter(self, source, event):
        """Filtra eventos para tratar teclas especiais no chat"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        
        if source is self.message_input and event.type() == QEvent.Type.KeyPress:
            key_event = event
            
            # Ctrl+Enter envia mensagem
            if key_event.key() == Qt.Key.Key_Return and key_event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self._send_message()
                return True
                
        return super().eventFilter(source, event)
    
    def _on_text_changed(self):
        """Atualiza o estado do botão de envio quando o texto muda"""
        self.send_button.setEnabled(len(self.message_input.toPlainText().strip()) > 0)
    
    def _send_message(self):
        """Processa e envia a mensagem do usuário"""
        message = self.message_input.toPlainText().strip()
        
        if not message:
            return
            
        # Adiciona a mensagem do usuário ao chat
        self._add_user_message(message)
        
        # Limpa o campo de entrada
        self.message_input.clear()
        
        # Mostra a barra de progresso
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Define a mensagem para o worker e inicia a thread
        # Passamos o histórico completo de mensagens, incluindo a nova mensagem do usuário
        self.message_worker.set_message(self._message_history)
        if not self.message_thread.isRunning():
            self.message_thread.start()
        else:
            # Se a thread já está rodando, apenas emite o sinal para iniciar o processamento
            self.message_thread.started.emit()
    
    def _add_user_message(self, message):
        """Adiciona uma mensagem do usuário ao chat"""
        # Cria o widget de mensagem
        message_widget = QFrame()
        message_widget.setFrameShape(QFrame.Shape.StyledPanel)
        message_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['user_message_bg']};
                border-radius: 10px;
                border: 1px solid {THEME['user_message_border']};
            }}
        """)
        
        # Layout da mensagem
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(10, 5, 10, 5)
        
        # Conteúdo da mensagem
        message_content = QLabel(message)
        message_content.setWordWrap(True)
        message_content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        message_content.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 14px;")
        
        # Informações da mensagem
        message_info = QLabel(f"Você • {datetime.now().strftime('%H:%M')}")
        message_info.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 10px;")
        
        # Adiciona os widgets ao layout da mensagem
        message_layout.addWidget(message_content)
        message_layout.addWidget(message_info)
        
        # Configura o layout do chat para mostrar a mensagem à direita
        message_container = QHBoxLayout()
        message_container.addStretch()
        message_container.addWidget(message_widget)
        
        # Adiciona a mensagem ao layout de chat
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, message_container)
        
        # Adiciona ao histórico
        self._message_history.append({"role": "user", "content": message})
    
    def _add_assistant_message(self, response):
        """Adiciona uma mensagem do assistente ao chat"""
        # Esconde a barra de progresso
        self.progress_bar.setVisible(False)
        
        # Extrai resposta e memórias do dicionário recebido
        if isinstance(response, dict):
            message = response.get("response", "")
            memories_used = response.get("memories_used", [])
            # Log para debug
            logger.debug(f"Memórias recebidas: {memories_used}")
        else:
            # Para compatibilidade com versões anteriores
            message = str(response)
            memories_used = []
        
        # Cria o widget de mensagem
        message_widget = QFrame()
        message_widget.setFrameShape(QFrame.Shape.StyledPanel)
        message_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['assistant_message_bg']};
                border-radius: 10px;
                border: 1px solid {THEME['assistant_message_border']};
            }}
        """)
        
        # Layout da mensagem
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(10, 5, 10, 5)
        
        # Conteúdo da mensagem
        message_content = QTextBrowser()
        message_content.setOpenExternalLinks(True)
        message_content.setHtml(message.replace("\n", "<br>"))
        message_content.setStyleSheet(f"""
            QTextBrowser {{
                background-color: transparent;
                color: {THEME['text_primary']};
                border: none;
                font-size: 14px;
            }}
        """)
        message_content.document().setDefaultStyleSheet(f"""
            a {{ color: {THEME['link']}; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            code {{ background-color: {THEME['code_bg']}; padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
            pre {{ background-color: {THEME['code_bg']}; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        """)
        
        # Ajusta a altura do texto para se adaptar ao conteúdo
        document_height = message_content.document().size().height()
        message_content.setMinimumHeight(min(200, int(document_height) + 10))
        message_content.setMaximumHeight(400)
        
        # Adiciona o conteúdo da mensagem ao layout
        message_layout.addWidget(message_content)
        
        # Se houver memórias usadas, mostra-as em um elemento expansível
        if memories_used and len(memories_used) > 0:
            # Container para memórias
            memories_container = QFrame()
            memories_container.setFrameShape(QFrame.Shape.StyledPanel)
            memories_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {THEME['bg_tertiary']};
                    border-radius: 5px;
                    border: 1px solid {THEME['input_border']};
                    margin-top: 5px;
                }}
            """)
            
            # Layout para as memórias
            memories_layout = QVBoxLayout(memories_container)
            memories_layout.setContentsMargins(8, 8, 8, 8)
            memories_layout.setSpacing(5)
            
            # Título para a seção de memórias
            memories_title = QLabel(f"Memórias Utilizadas ({len(memories_used)})")
            memories_title.setStyleSheet(f"color: {THEME['accent']}; font-weight: bold; font-size: 12px;")
            memories_layout.addWidget(memories_title)
            
            # Adiciona cada memória como um item
            for i, memory in enumerate(memories_used[:3]):  # Mostra apenas as 3 primeiras memórias
                # Verifica a estrutura da memória e extrai os dados conforme disponíveis
                memory_text = memory.get('memory', memory.get('text', 'Sem texto'))
                similarity = memory.get('score', memory.get('similarity', 0))
                relevance_percentage = int(similarity * 100)
                
                # Estiliza a relevância da memória (de 0 a 100%)
                relevance_color = f"#{min(255, int(255 - similarity * 255 * 0.7)):02x}{min(255, int(similarity * 255)):02x}4f"
                
                # Conteúdo da memória
                memory_item = QLabel(f"{memory_text[:150]}..." if len(memory_text) > 150 else memory_text)
                memory_item.setWordWrap(True)
                memory_item.setStyleSheet(f"""
                    color: {THEME['text_secondary']};
                    background-color: {THEME['bg_secondary']};
                    padding: 5px;
                    border-radius: 3px;
                    font-size: 11px;
                """)
                
                # Barra de relevância
                memory_relevance = QLabel(f"Relevância: {relevance_percentage}%")
                memory_relevance.setStyleSheet(f"""
                    color: {relevance_color};
                    font-size: 10px;
                    font-weight: bold;
                    margin-bottom: 5px;
                """)
                
                # Adiciona os widgets ao layout
                memories_layout.addWidget(memory_relevance)
                memories_layout.addWidget(memory_item)
                
                # Adiciona separador, exceto para o último item
                if i < min(2, len(memories_used) - 1):
                    separator = QFrame()
                    separator.setFrameShape(QFrame.Shape.HLine)
                    separator.setStyleSheet(f"border: none; background-color: {THEME['input_border']}; max-height: 1px;")
                    memories_layout.addWidget(separator)
            
            # Adiciona link para ver mais memórias se houver mais do que 3
            if len(memories_used) > 3:
                more_memories_link = QLabel(f"<a href='#'>Ver mais {len(memories_used) - 3} memórias...</a>")
                more_memories_link.setStyleSheet(f"""
                    color: {THEME['accent']};
                    font-size: 10px;
                    text-decoration: none;
                """)
                more_memories_link.setTextFormat(Qt.TextFormat.RichText)
                more_memories_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
                more_memories_link.linkActivated.connect(lambda: self._show_all_memories(memories_used))
                memories_layout.addWidget(more_memories_link)
            
            # Adiciona o container de memórias ao layout da mensagem
            message_layout.addWidget(memories_container)
        
        # Informações da mensagem
        message_info = QLabel(f"Assistente • {datetime.now().strftime('%H:%M')}")
        message_info.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 10px;")
        message_layout.addWidget(message_info)
        
        # Configura o layout do chat para mostrar a mensagem à esquerda
        message_container = QHBoxLayout()
        message_container.addWidget(message_widget)
        message_container.addStretch()
        
        # Adiciona a mensagem ao layout de chat
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, message_container)
        
        # Adiciona ao histórico
        self._message_history.append({"role": "assistant", "content": message})
    
    def _add_system_message(self, message):
        """Adiciona uma mensagem do sistema ao chat"""
        # Cria o widget de mensagem
        message_widget = QFrame()
        message_widget.setFrameShape(QFrame.Shape.StyledPanel)
        message_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['system_message_bg']};
                border-radius: 10px;
                border: 1px solid {THEME['system_message_border']};
            }}
        """)
        
        # Layout da mensagem
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(10, 5, 10, 5)
        
        # Conteúdo da mensagem
        message_content = QLabel(message)
        message_content.setWordWrap(True)
        message_content.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 14px;")
        
        # Informações da mensagem
        message_info = QLabel(f"Sistema • {datetime.now().strftime('%H:%M')}")
        message_info.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 10px;")
        
        # Adiciona os widgets ao layout da mensagem
        message_layout.addWidget(message_content)
        message_layout.addWidget(message_info)
        
        # Configura o layout do chat para mostrar a mensagem centralizada
        message_container = QHBoxLayout()
        message_container.addStretch()
        message_container.addWidget(message_widget)
        message_container.addStretch()
        
        # Adiciona a mensagem ao layout de chat
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, message_container)
    
    def _show_error(self, error_message):
        """Mostra uma mensagem de erro no chat"""
        # Esconde a barra de progresso
        self.progress_bar.setVisible(False)
        
        # Cria o widget de mensagem
        message_widget = QFrame()
        message_widget.setFrameShape(QFrame.Shape.StyledPanel)
        message_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['error_message_bg']};
                border-radius: 10px;
                border: 1px solid {THEME['error_message_border']};
            }}
        """)
        
        # Layout da mensagem
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(10, 5, 10, 5)
        
        # Conteúdo da mensagem
        message_content = QLabel(f"Erro: {error_message}")
        message_content.setWordWrap(True)
        message_content.setStyleSheet(f"color: {THEME['text_primary']}; font-size: 14px;")
        
        # Informações da mensagem
        message_info = QLabel(f"Sistema • {datetime.now().strftime('%H:%M')}")
        message_info.setStyleSheet(f"color: {THEME['text_muted']}; font-size: 10px;")
        
        # Adiciona os widgets ao layout da mensagem
        message_layout.addWidget(message_content)
        message_layout.addWidget(message_info)
        
        # Configura o layout do chat para mostrar a mensagem centralizada
        message_container = QHBoxLayout()
        message_container.addStretch()
        message_container.addWidget(message_widget)
        message_container.addStretch()
        
        # Adiciona a mensagem ao layout de chat
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, message_container)
    
    def _update_progress(self, value):
        """Atualiza o valor da barra de progresso"""
        self.progress_bar.setValue(value)
    
    def _clear_chat(self):
        """Limpa o histórico de chat atual"""
        # Remove mensagens do layout
        while self.chat_layout.count() > 1:  # Mantém apenas o stretch no final
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Limpa o layout interno
                while item.layout().count():
                    inner_item = item.layout().takeAt(0)
                    if inner_item.widget():
                        inner_item.widget().deleteLater()
        
        # Limpa o histórico
        self._message_history = []
        
        # Adiciona mensagem de sistema
        self._add_system_message("O histórico de chat foi limpo.")
    
    def _clear_memories(self):
        """Limpa todas as memórias do usuário atual"""
        # Pergunta ao usuário se realmente deseja limpar todas as memórias
        response = QMessageBox.question(
            self,
            "Limpar Memórias",
            f"Tem certeza que deseja apagar todas as memórias do usuário? Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        # Se o usuário confirmar, limpa as memórias
        if response == QMessageBox.StandardButton.Yes:
            try:
                # Tenta limpar as memórias
                result = self.memory_manager.clear_memories(self.user_id)
                
                if result:
                    # Mensagem de sucesso
                    QMessageBox.information(
                        self,
                        "Memórias Limpas",
                        "Todas as memórias foram apagadas com sucesso."
                    )
                    # Adiciona mensagem ao chat
                    self._add_system_message("Todas as memórias foram apagadas com sucesso.")
                else:
                    # Mensagem de erro
                    QMessageBox.warning(
                        self,
                        "Erro ao Limpar Memórias",
                        "Não foi possível limpar as memórias. Consulte os logs para mais detalhes."
                    )
            except Exception as e:
                logger.error(f"Erro ao limpar memórias: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Ocorreu um erro ao tentar limpar as memórias:\n{str(e)}"
                )
        
    def _handle_logout(self):
        """Processa o logout do usuário"""
        try:
            # Finaliza a thread de mensagens
            if self.message_thread.isRunning():
                self.message_thread.quit()
                self.message_thread.wait()
            
            # Faz logout
            success, message = self.auth.logout()
            
            if success:
                logger.info("Logout realizado com sucesso")
                self.logout_requested.emit()
            else:
                logger.warning(f"Falha no logout: {message}")
                QMessageBox.warning(self, "Falha no Logout", message)
                
        except Exception as e:
            logger.error(f"Erro ao processar logout: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao processar o logout:\n{str(e)}")
    
    def closeEvent(self, event):
        """Manipula o evento de fechamento da janela"""
        # Finaliza a thread de mensagens se existir
        if hasattr(self, 'message_thread') and self.message_thread.isRunning():
            self.message_thread.quit()
            self.message_thread.wait()
        
        event.accept()

    def _show_all_memories(self, memories):
        """Mostra todas as memórias em um diálogo"""
        # Cria um diálogo para mostrar todas as memórias
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Todas as Memórias Utilizadas")
        
        # Formata as memórias como texto
        memories_text = "<html><body style='font-family: Arial; font-size: 12px;'>"
        memories_text += "<h3 style='color: #89B4FA;'>Memórias Utilizadas na Resposta</h3>"
        memories_text += "<p>As seguintes memórias foram utilizadas para gerar a resposta:</p>"
        
        for i, memory in enumerate(memories):
            # Verifica a estrutura da memória e extrai os dados conforme disponíveis
            memory_text = memory.get('memory', memory.get('text', 'Sem texto'))
            similarity = memory.get('score', memory.get('similarity', 0))
            relevance_percentage = int(similarity * 100)
            
            memories_text += f"<div style='margin: 10px 0; padding: 10px; background-color: #252536; border-radius: 5px;'>"
            memories_text += f"<div style='margin-bottom: 5px; color: #94E2D5; font-weight: bold;'>Memória {i+1} (Relevância: {relevance_percentage}%)</div>"
            memories_text += f"<div style='color: #CDD6F4; background-color: #1E1E2E; padding: 8px; border-radius: 4px;'>{memory_text}</div>"
            memories_text += "</div>"
        
        memories_text += "</body></html>"
        
        # Configura o diálogo
        dialog.setTextFormat(Qt.TextFormat.RichText)
        dialog.setText(memories_text)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.setIconPixmap(QPixmap())  # Remove o ícone padrão
        
        # Ajusta o tamanho do diálogo
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        # Exibe o diálogo
        dialog.exec()

    def _show_settings(self):
        """
        Exibe o diálogo de configurações
        """
        try:
            # Obtém o ID do usuário atual
            user_id = self.user_id
            
            # Cria e exibe o diálogo de configurações
            dialog = SystemPromptDialog(user_id, self)
            result = dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                # Obtém o novo prompt do sistema
                new_prompt = dialog.get_prompt()
                
                # Salva o prompt personalizado
                success = save_user_system_prompt(user_id, new_prompt)
                
                if success:
                    # Adiciona uma mensagem no chat para informar o usuário
                    self._add_system_message("Seu prompt personalizado foi atualizado. As próximas mensagens usarão sua configuração.")
                else:
                    # Exibe mensagem de erro e registra no log
                    logger.error("Falha ao salvar prompt personalizado")
                    QMessageBox.critical(
                        self, 
                        "Erro", 
                        "Não foi possível salvar as configurações. Por favor, tente novamente."
                    )
        except Exception as e:
            # Registra o erro e exibe uma mensagem para o usuário
            logger.error(f"Erro ao exibir configurações: {str(e)}")
            QMessageBox.critical(
                self,
                "Erro nas Configurações",
                f"Ocorreu um erro ao processar as configurações: {str(e)}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Aplicar tema escuro em toda a aplicação
    app.setStyle("Fusion")
    window = ChatWindow("test_user")
    window.show()
    sys.exit(app.exec()) 
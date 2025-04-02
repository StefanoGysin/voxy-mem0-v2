"""
Janela de login para o aplicativo Voxy
"""

import os
import sys
import logging
import base64
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFrame,
    QGridLayout, QCheckBox, QSpacerItem, QSizePolicy, QDialog,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QSettings
from PyQt6.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QFontDatabase, QLinearGradient, QPainter, QBrush, QPen
from typing import Optional
from dotenv import load_dotenv

# Importa módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import get_auth_instance

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logger = logging.getLogger("voxy-ui-login")

# Configurações
REQUIRE_EMAIL_CONFIRMATION = os.getenv('REQUIRE_EMAIL_CONFIRMATION', 'true').lower() == 'true'

# Esquema de cores moderno para tema escuro
THEME = {
    "bg_primary": "#151823",          # Fundo principal (mais escuro)
    "bg_secondary": "#1A1E2A",         # Fundo secundário
    "bg_tertiary": "#232738",          # Elementos de fundo terciário
    "accent": "#4E67F1",               # Cor de destaque (azul)
    "accent_gradient_start": "#4E67F1",  # Início do gradiente de destaque
    "accent_gradient_end": "#9C5AFF",    # Fim do gradiente de destaque (roxo)
    "accent_darker": "#3A53DD",        # Cor de destaque mais escura (hover)
    "text_primary": "#F2F3F8",         # Texto principal
    "text_secondary": "#ADB3BC",       # Texto secundário  
    "text_muted": "#6C727F",           # Texto menos importante
    "button_primary": "#4E67F1",       # Botão primário (gradiente)
    "button_primary_hover": "#3A53DD", # Botão primário hover
    "button_primary_text": "#FFFFFF",  # Texto do botão primário
    "button_secondary": "#232738",     # Botão secundário
    "button_secondary_hover": "#2A2F43", # Botão secundário hover
    "button_secondary_text": "#E2E4E9", # Texto do botão secundário
    "button_disabled": "#32333B",      # Botão desabilitado
    "button_disabled_text": "#797E89", # Texto do botão desabilitado
    "input_bg": "#232738",             # Fundo do campo de entrada
    "input_border": "#2C3243",         # Borda do campo de entrada
    "input_text": "#F2F3F8",           # Texto do campo de entrada
    "input_placeholder": "#6C727F",    # Texto de placeholder
    "input_focus_border": "#4E67F1",   # Borda do campo quando em foco
    "accent_green": "#4AD295",         # Cor de destaque verde
    "accent_red": "#F56565",           # Cor de destaque vermelho
    "link": "#7C95FF",                 # Cor de links
    "shadow": "rgba(0, 0, 0, 0.25)",   # Cor das sombras
}

class GradientLabel(QLabel):
    """
    Label personalizado com texto em gradiente usando método seguro
    """
    def __init__(self, text, gradient_start, gradient_end, font_size=36, font_weight=QFont.Weight.Bold, parent=None):
        super().__init__(text, parent)
        self.gradient_start = QColor(gradient_start)
        self.gradient_end = QColor(gradient_end)
        self.setFont(QFont("Segoe UI", font_size, font_weight))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(text)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Cria o gradiente linear para texto
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, self.gradient_start)
        gradient.setColorAt(1, self.gradient_end)
        
        # Configura a caneta com o gradiente
        pen = QPen(QBrush(gradient), 1)
        painter.setPen(pen)
        
        # Desenha o texto usando o método normal de desenho de texto
        text_rect = self.rect()
        painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignCenter), self.text())
        
        # Finaliza o painter
        painter.end()

class LoginWindow(QMainWindow):
    """
    Janela de login do aplicativo
    """
    # Sinal emitido quando o login é bem-sucedido
    login_successful = pyqtSignal(str)
    
    def __init__(self):
        """
        Inicializa a janela de login
        """
        super().__init__()
        
        # Configurações iniciais
        self.setWindowTitle("Voxy - Login")
        self.setMinimumSize(450, 620)
        self.setWindowIcon(QIcon("assets/icon.png"))
        
        # Inicializa o QSettings para salvar as credenciais
        self.settings = QSettings("VoxyMem0", "LoginCredentials")
        
        # Aplica o estilo global para tema escuro
        self._apply_dark_theme()
        
        # Obtém o serviço de autenticação
        self.auth = get_auth_instance()
        
        # Verifica se o usuário permite criação de contas
        self.allow_account_creation = os.getenv('ALLOW_ACCOUNT_CREATION', 'false').lower() == 'true'
        
        # Inicializa a interface
        self._init_ui()
        
        # Carrega as credenciais salvas, se existirem
        self._load_saved_credentials()
        
        # Centraliza a janela
        self.center_on_screen()
        
        logger.info("Janela de login inicializada")
    
    def _apply_dark_theme(self):
        """Aplica o tema escuro à janela inteira"""
        # Configura um estilo global mais moderno
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {THEME['bg_primary']};
                color: {THEME['text_primary']};
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }}
            
            QLabel {{
                color: {THEME['text_primary']};
            }}
            
            QLineEdit {{
                background-color: {THEME['input_bg']};
                color: {THEME['input_text']};
                border: 1px solid {THEME['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                selection-background-color: {THEME['accent']};
                selection-color: {THEME['text_primary']};
                font-size: 14px;
            }}
            
            QLineEdit:focus {{
                border: 2px solid {THEME['input_focus_border']};
                padding: 7px 11px;
            }}
            
            QLineEdit::placeholder {{
                color: {THEME['input_placeholder']};
            }}
            
            QPushButton {{
                background-color: {THEME['button_primary']};
                color: {THEME['button_primary_text']};
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 14px;
            }}
            
            QPushButton:hover {{
                background-color: {THEME['button_primary_hover']};
            }}
            
            QPushButton:disabled {{
                background-color: {THEME['button_disabled']};
                color: {THEME['button_disabled_text']};
            }}
            
            QCheckBox {{
                color: {THEME['text_secondary']};
                spacing: 5px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {THEME['input_border']};
                border-radius: 3px;
                background-color: {THEME['input_bg']};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {THEME['accent']};
                border: 1px solid {THEME['accent']};
                image: url(assets/icons/check.png);
            }}
            
            QMessageBox {{
                background-color: {THEME['bg_secondary']};
                color: {THEME['text_primary']};
            }}
            
            QDialog {{
                background-color: {THEME['bg_secondary']};
                color: {THEME['text_primary']};
                border-radius: 8px;
            }}
        """)
    
    def _init_ui(self):
        """Inicializa a interface gráfica com design moderno"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 60, 40, 40)
        main_layout.setSpacing(30)
        
        # Frame de login com sombra
        login_frame = QFrame()
        login_frame.setFrameShape(QFrame.Shape.StyledPanel)
        login_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['bg_secondary']};
                border-radius: 12px;
            }}
        """)
        
        # Adiciona sombra ao frame
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 6)
        login_frame.setGraphicsEffect(shadow)
        
        # Layout do frame de login
        login_layout = QVBoxLayout(login_frame)
        login_layout.setContentsMargins(30, 60, 30, 30)
        login_layout.setSpacing(20)
        
        # Email Input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("seu.email@exemplo.com")
        self.email_input.setMinimumHeight(50)
        self.email_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                color: {THEME['input_text']};
                border: 1px solid {THEME['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {THEME['input_focus_border']};
                padding: 7px 11px;
            }}
        """)
        
        # Senha Input
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Sua senha")
        self.password_input.setMinimumHeight(50)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                color: {THEME['input_text']};
                border: 1px solid {THEME['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {THEME['input_focus_border']};
                padding: 7px 11px;
            }}
        """)
        
        # Layout para lembrar-me e esqueci senha
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(0)
        
        # Checkbox "Lembrar-me"
        self.remember_checkbox = QCheckBox("Lembrar-me")
        self.remember_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME['text_secondary']};
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {THEME['input_border']};
                border-radius: 3px;
                background-color: {THEME['input_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {THEME['accent']};
                border: 1px solid {THEME['accent']};
                image: url(assets/icons/check.png);
            }}
        """)
        
        # Link "Esqueci minha senha"
        self.forgot_button = QPushButton("Esqueci minha senha")
        self.forgot_button.setFlat(True)
        self.forgot_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.forgot_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {THEME['link']};
                border: none;
                text-decoration: none;
                font-weight: normal;
                font-size: 13px;
                text-align: right;
                padding: 0;
            }}
            QPushButton:hover {{
                text-decoration: underline;
                color: {THEME['accent']};
            }}
        """)
        
        options_layout.addWidget(self.remember_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(self.forgot_button)
        
        # Botão "Entrar"
        self.login_button = QPushButton("Entrar")
        self.login_button.setMinimumHeight(50)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                         stop:0 {THEME['accent_gradient_start']}, 
                                         stop:1 {THEME['accent_gradient_end']});
                color: {THEME['button_primary_text']};
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                         stop:0 {THEME['accent_gradient_start']}, 
                                         stop:1 {THEME['accent_gradient_end']});
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background: {THEME['accent_darker']};
            }}
        """)
        
        # Divisor com texto "ou"
        divider_layout = QHBoxLayout()
        divider_layout.setContentsMargins(0, 10, 0, 10)
        
        left_divider = QFrame()
        left_divider.setFrameShape(QFrame.Shape.HLine)
        left_divider.setStyleSheet(f"background-color: {THEME['input_border']}; max-height: 1px;")
        
        divider_text = QLabel("ou")
        divider_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        divider_text.setStyleSheet(f"color: {THEME['text_muted']}; margin: 0 15px; font-size: 13px;")
        
        right_divider = QFrame()
        right_divider.setFrameShape(QFrame.Shape.HLine)
        right_divider.setStyleSheet(f"background-color: {THEME['input_border']}; max-height: 1px;")
        
        divider_layout.addWidget(left_divider)
        divider_layout.addWidget(divider_text)
        divider_layout.addWidget(right_divider)
        
        # Botão "Criar Conta"
        self.register_button = QPushButton("Criar Conta")
        self.register_button.setMinimumHeight(50)
        self.register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['bg_tertiary']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['input_border']};
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {THEME['button_secondary_hover']};
                border: 1px solid {THEME['accent']};
            }}
            QPushButton:disabled {{
                background-color: {THEME['button_disabled']};
                color: {THEME['button_disabled_text']};
                border: 1px solid {THEME['input_border']};
            }}
        """)
        
        # Configura o estado do botão de registro
        self.register_button.setEnabled(self.allow_account_creation)
        if not self.allow_account_creation:
            self.register_button.setToolTip("Criação de contas desativada pelo administrador")
        
        # Adiciona os widgets ao layout de login
        # Titulo no topo do frame
        title_label = QLabel("Voxy")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {THEME['accent']}; margin-bottom: 15px;")
        
        # Login Frame Layout
        login_layout.addWidget(title_label)
        login_layout.addWidget(self.email_input)
        login_layout.addWidget(self.password_input)
        login_layout.addLayout(options_layout)
        login_layout.addSpacing(10)
        login_layout.addWidget(self.login_button)
        login_layout.addLayout(divider_layout)
        login_layout.addWidget(self.register_button)
        
        # Adiciona o frame ao layout principal com um peso maior
        main_layout.addStretch(1)  # Espaço flexível no topo
        main_layout.addWidget(login_frame, 6)  # Frame de login com peso maior
        main_layout.addStretch(1)  # Espaço flexível na base
        
        # Conecta sinais
        self.login_button.clicked.connect(self._handle_login)
        self.forgot_button.clicked.connect(self._handle_forgot_password)
        self.register_button.clicked.connect(self._show_register_form)
        
        # Conecta eventos de teclas
        self.password_input.returnPressed.connect(self._handle_login)
        self.email_input.returnPressed.connect(lambda: self.password_input.setFocus())
    
    def _handle_login(self):
        """
        Processa a tentativa de login
        """
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Campos Obrigatórios", "Por favor, preencha email e senha.")
            return
            
        try:
            # Tenta fazer login
            success, message, user = self.auth.login(email, password)
            
            if success:
                logger.info(f"Login bem-sucedido para {email}")
                
                # Salva as credenciais se o checkbox estiver marcado
                if self.remember_checkbox.isChecked():
                    self._save_credentials(email, password)
                    logger.info("Credenciais salvas para login automático")
                else:
                    # Se o checkbox não estiver marcado, remova as credenciais salvas
                    self._clear_saved_credentials()
                    logger.info("Credenciais salvas foram removidas")
                
                # Emite sinal de login bem-sucedido com o ID do usuário
                self.login_successful.emit(self.auth.get_user_id())
                # Limpa os campos por segurança
                self.email_input.clear()
                self.password_input.clear()
            else:
                logger.warning(f"Falha no login para {email}: {message}")
                QMessageBox.warning(self, "Falha no Login", message)
                
        except Exception as e:
            logger.error(f"Erro ao processar login: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao processar o login:\n{str(e)}")
    
    def _save_credentials(self, email, password):
        """
        Salva as credenciais do usuário de forma segura
        """
        try:
            # Usamos codificação em base64 para uma camada básica de ofuscação
            # Não é segurança real, apenas evita texto legível diretamente
            encoded_email = base64.b64encode(email.encode()).decode()
            encoded_password = base64.b64encode(password.encode()).decode()
            
            self.settings.setValue("remember_login", True)
            self.settings.setValue("email", encoded_email)
            self.settings.setValue("password", encoded_password)
            self.settings.sync()
            logger.info("Credenciais salvas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao salvar credenciais: {str(e)}")
    
    def _clear_saved_credentials(self):
        """
        Remove as credenciais salvas
        """
        self.settings.remove("remember_login")
        self.settings.remove("email")
        self.settings.remove("password")
        self.settings.sync()
        logger.info("Credenciais removidas")
    
    def _load_saved_credentials(self):
        """
        Carrega as credenciais salvas, se existirem
        """
        try:
            remember_login = self.settings.value("remember_login", False, type=bool)
            
            if remember_login:
                encoded_email = self.settings.value("email", "")
                encoded_password = self.settings.value("password", "")
                
                if encoded_email and encoded_password:
                    email = base64.b64decode(encoded_email.encode()).decode()
                    password = base64.b64decode(encoded_password.encode()).decode()
                    
                    self.email_input.setText(email)
                    self.password_input.setText(password)
                    self.remember_checkbox.setChecked(True)
                    
                    logger.info("Credenciais carregadas com sucesso")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais: {str(e)}")
            return False
    
    def _show_register_form(self):
        """
        Mostra o formulário de registro com design moderno
        """
        # Verifica se a criação de contas está habilitada
        if not self.allow_account_creation:
            QMessageBox.information(
                self, 
                "Registro", 
                "Para criar uma conta, entre em contato com o administrador do sistema."
            )
            return
        
        # Exibe o formulário de registro quando permitido
        dialog = QDialog(self)
        dialog.setWindowTitle("Criar Nova Conta")
        dialog.setMinimumSize(420, 380)
        
        # Adiciona sombra ao diálogo
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        dialog.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("Criar Nova Conta")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {THEME['text_primary']}; margin-bottom: 10px;")
        
        # Subtítulo
        subtitle_label = QLabel("Preencha os campos abaixo para se registrar")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {THEME['text_secondary']}; margin-bottom: 20px; font-size: 13px;")
        
        # Campos do formulário
        email_input = QLineEdit()
        email_input.setPlaceholderText("seu.email@exemplo.com")
        email_input.setMinimumHeight(46)
        email_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                color: {THEME['input_text']};
                border: 1px solid {THEME['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {THEME['input_focus_border']};
                padding: 7px 11px;
            }}
        """)
        
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setPlaceholderText("Crie uma senha forte")
        password_input.setMinimumHeight(46)
        password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                color: {THEME['input_text']};
                border: 1px solid {THEME['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {THEME['input_focus_border']};
                padding: 7px 11px;
            }}
        """)
        
        confirm_input = QLineEdit()
        confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_input.setPlaceholderText("Confirme sua senha")
        confirm_input.setMinimumHeight(46)
        confirm_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME['input_bg']};
                color: {THEME['input_text']};
                border: 1px solid {THEME['input_border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {THEME['input_focus_border']};
                padding: 7px 11px;
            }}
        """)
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.setMinimumHeight(46)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['bg_tertiary']};
                color: {THEME['text_primary']};
                border: 1px solid {THEME['input_border']};
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {THEME['button_secondary_hover']};
            }}
        """)
        
        register_button = QPushButton("Registrar")
        register_button.setMinimumHeight(46)
        register_button.setDefault(True)
        register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        register_button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                         stop:0 {THEME['accent_gradient_start']}, 
                                         stop:1 {THEME['accent_gradient_end']});
                color: {THEME['button_primary_text']};
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                         stop:0 {THEME['accent_gradient_start']}, 
                                         stop:1 {THEME['accent_gradient_end']});
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background: {THEME['accent_darker']};
            }}
        """)
        
        button_layout.addWidget(cancel_button, 1)
        button_layout.addWidget(register_button, 2)
        
        # Adiciona os widgets ao layout
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addWidget(email_input)
        layout.addSpacing(5)
        layout.addWidget(password_input)
        layout.addSpacing(5)
        layout.addWidget(confirm_input)
        layout.addSpacing(15)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Conecta os sinais
        cancel_button.clicked.connect(dialog.reject)
        
        def do_register():
            email = email_input.text()
            password = password_input.text()
            confirm_password = confirm_input.text()
            
            if not email or not password or not confirm_password:
                QMessageBox.warning(dialog, "Campos Vazios", "Por favor, preencha todos os campos.")
                return
            
            try:
                success, message = self.auth.register(email, password, confirm_password)
                
                if success:
                    if REQUIRE_EMAIL_CONFIRMATION:
                        # Mostrar mensagem solicitando confirmação por email
                        QMessageBox.information(
                            dialog, 
                            "Registro Concluído", 
                            "Sua conta foi criada com sucesso!\n\nPor favor, verifique seu email para confirmar a conta antes de fazer login."
                        )
                    else:
                        # Mostrar mensagem indicando que o login já pode ser feito
                        QMessageBox.information(
                            dialog, 
                            "Registro Concluído", 
                            "Sua conta foi criada com sucesso!\n\nVocê já pode fazer login."
                        )
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Falha no Registro", message)
            except Exception as e:
                logger.error(f"Erro ao processar registro: {str(e)}")
                QMessageBox.critical(dialog, "Erro", f"Ocorreu um erro ao processar o registro:\n{str(e)}")
        
        register_button.clicked.connect(do_register)
        
        # Exibe o diálogo
        dialog.exec()
    
    def _handle_forgot_password(self):
        """
        Processa a solicitação de recuperação de senha
        """
        QMessageBox.information(
            self, 
            "Recuperação de Senha", 
            "Para recuperar sua senha, entre em contato com o administrador do sistema."
        )
    
    def center_on_screen(self):
        """
        Centraliza a janela na tela
        """
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec()) 
"""
Testes para a janela de login usando pytest-qt.
"""

import pytest
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QMessageBox
from unittest.mock import patch, MagicMock
import os
import sys

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.login_window import LoginWindow
from utils.auth import SupabaseAuth

@pytest.fixture
def login_window(qapp, mock_env_vars):
    """Fixture que cria uma instância da janela de login para testes."""
    # Mock para o get_auth_instance
    with patch('ui.login_window.get_auth_instance') as mock_get_auth:
        # Configura a instância mock que será retornada
        mock_auth_manager = MagicMock()
        mock_get_auth.return_value = mock_auth_manager
        
        # Mock para QSettings para evitar carregar credenciais salvas
        with patch('ui.login_window.QSettings') as mock_settings_class:
            mock_settings = MagicMock()
            mock_settings_class.return_value = mock_settings
            
            # Configura o mock para não retornar credenciais salvas
            mock_settings.value.side_effect = lambda key, default=None, type=None: default
            
            # Cria a janela de login
            window = LoginWindow()
            
            # Limpa os campos de entrada para garantir que estejam vazios
            window.email_input.clear()
            window.password_input.clear()
            
            # Retorna a janela e o mock do SupabaseAuth
            yield window, mock_auth_manager
            
            # Cleanup
            window.close()

class TestLoginWindow:
    """Testes para a janela de login."""
    
    def test_init(self, login_window):
        """Testa a inicialização da janela de login."""
        # Descompacta
        window, _ = login_window
        
        # Verifica que a janela foi configurada corretamente
        assert window.windowTitle() == "Voxy-Mem0 - Login"
        assert hasattr(window, 'email_input')
        assert hasattr(window, 'password_input')
        assert hasattr(window, 'login_button')
        assert hasattr(window, 'register_button')
    
    def test_login_success(self, qtbot, login_window):
        """Testa o login bem-sucedido."""
        # Descompacta
        window, mock_auth_manager = login_window
        
        # Configura o SupabaseAuth mock para sucesso no login
        mock_auth_manager.login.return_value = (True, "Login bem-sucedido", {
            'id': 'user-123',
            'email': 'test@example.com'
        })
        mock_auth_manager.get_user_id.return_value = "user-123"
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Preenche os campos
        window.email_input.setText('test@example.com')
        window.password_input.setText('senha_segura')
        
        # Configura um sinal para verificar se o login_successful foi emitido
        login_successful_called = False
        
        def handle_login_successful(user_id):
            nonlocal login_successful_called
            login_successful_called = True
            assert user_id == 'user-123'
        
        window.login_successful.connect(handle_login_successful)
        
        # Clica no botão de login
        qtbot.mouseClick(window.login_button, Qt.MouseButton.LeftButton)
        
        # Verifica que o método de login foi chamado corretamente
        mock_auth_manager.login.assert_called_once_with('test@example.com', 'senha_segura')
        
        # Verifica que o sinal foi emitido
        assert login_successful_called
    
    def test_login_failure(self, qtbot, login_window, monkeypatch):
        """Testa o login com falha."""
        # Descompacta
        window, mock_auth_manager = login_window
        
        # Configura o SupabaseAuth mock para falha no login
        mock_auth_manager.login.return_value = (False, "Credenciais inválidas", None)
        
        # Substitui QMessageBox.warning para evitar diálogos durante o teste
        message_shown = False
        
        def mock_warning(parent, title, text):
            nonlocal message_shown
            message_shown = True
            return QMessageBox.StandardButton.Ok
        
        monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.warning', mock_warning)
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Preenche os campos
        window.email_input.setText('invalid@example.com')
        window.password_input.setText('senha_incorreta')
        
        # Clica no botão de login
        qtbot.mouseClick(window.login_button, Qt.MouseButton.LeftButton)
        
        # Verifica que o método de login foi chamado corretamente
        mock_auth_manager.login.assert_called_once_with('invalid@example.com', 'senha_incorreta')
        
        # Verifica que a mensagem de erro foi mostrada
        assert message_shown
    
    @pytest.mark.skip(reason="Teste complexo que requer mais mocks")
    def test_show_register_form(self, qtbot, login_window, monkeypatch):
        """Testa a exibição do formulário de registro."""
        # Descompacta
        window, _ = login_window
        
        # Mock para QDialog para evitar a exibição real
        dialog_created = False
        
        class MockDialog:
            def __init__(self, parent=None):
                nonlocal dialog_created
                dialog_created = True
                self.parent = parent
                self.title = ""
                self.layout = None
            
            def setWindowTitle(self, title):
                self.title = title
                
            def setMinimumSize(self, width, height):
                pass
                
            def exec(self):
                return QDialog.DialogCode.Accepted
        
        monkeypatch.setattr('PyQt6.QtWidgets.QDialog', MockDialog)
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Clica no botão de registro
        qtbot.mouseClick(window.register_button, Qt.MouseButton.LeftButton)
        
        # Verifica que o diálogo foi criado
        assert dialog_created
    
    @pytest.mark.skip(reason="Teste complexo que requer mais mocks")
    def test_register_success(self, qtbot, login_window, monkeypatch):
        """Testa o registro bem-sucedido."""
        # Descompacta
        window, mock_auth_manager = login_window
        
        # Configura o SupabaseAuth mock para sucesso no registro
        mock_auth_manager.register.return_value = (True, "Registro realizado com sucesso")
        
        # Mock para QDialog para simular o formulário de registro
        register_dialog = None
        register_callback = None
        
        class MockDialog:
            def __init__(self, parent=None):
                nonlocal register_dialog
                self.parent = parent
                self.title = ""
                self.layout = None
                self.email_input = MagicMock()
                self.email_input.text.return_value = "new@example.com"
                self.password_input = MagicMock()
                self.password_input.text.return_value = "nova_senha"
                self.confirm_password_input = MagicMock()
                self.confirm_password_input.text.return_value = "nova_senha"
                register_dialog = self
                
            def setWindowTitle(self, title):
                self.title = title
                
            def setMinimumSize(self, width, height):
                pass
                
            def exec(self):
                # Simula o clique no botão de registro
                if register_callback:
                    register_callback()
                return QDialog.DialogCode.Accepted
        
        # Substitui QMessageBox.information para evitar diálogos
        message_shown = False
        
        def mock_information(parent, title, text):
            nonlocal message_shown
            message_shown = True
            assert "sucesso" in title.lower() or "sucesso" in text.lower()
            return QMessageBox.StandardButton.Ok
        
        monkeypatch.setattr('PyQt6.QtWidgets.QMessageBox.information', mock_information)
        monkeypatch.setattr('PyQt6.QtWidgets.QDialog', MockDialog)
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Captura a função de registro quando o botão for configurado
        original_connect = QPushButton.clicked.connect
        
        def mock_connect(self, callback):
            nonlocal register_callback
            if self.__class__.__name__ == 'QPushButton' and not register_callback:
                register_callback = callback
            return original_connect(self, callback)
        
        monkeypatch.setattr('PyQt6.QtWidgets.QPushButton.clicked.connect', mock_connect)
        
        # Clica no botão de registro para abrir o formulário
        qtbot.mouseClick(window.register_button, Qt.MouseButton.LeftButton)
        
        # Verifica que o método de registro foi chamado corretamente
        mock_auth_manager.register.assert_called_once_with("new@example.com", "nova_senha", "nova_senha")
        
        # Verifica que a mensagem de sucesso foi mostrada
        assert message_shown 
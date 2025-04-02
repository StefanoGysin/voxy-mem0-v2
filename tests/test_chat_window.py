"""
Testes para a janela de chat usando pytest-qt.
"""

import pytest
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtWidgets import QApplication, QMessageBox, QLabel, QDialog
from unittest.mock import patch, MagicMock
import os
import sys

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.chat_window import ChatWindow, MessageWorker, SystemPromptDialog
from utils.memory_manager import MemoryManager

@pytest.fixture
def chat_window(qapp, mock_env_vars):
    """Fixture que cria uma instância da janela de chat para testes."""
    # Mock para o get_memory_manager e get_auth_instance
    with patch('ui.chat_window.get_memory_manager') as mock_get_memory_manager, \
         patch('ui.chat_window.get_auth_instance') as mock_get_auth_instance:
        
        # Configura o mock de autenticação
        mock_auth = MagicMock()
        mock_auth.is_logged_in.return_value = True
        mock_get_auth_instance.return_value = mock_auth
        
        # Configura a instância mock do memory manager
        mock_memory_manager = MagicMock()
        mock_get_memory_manager.return_value = mock_memory_manager
        
        # Configura o processamento de mensagens para retornar uma resposta válida
        mock_memory_manager.process_message.return_value = {
            "response": "Esta é uma resposta de teste",
            "memories_used": [
                {"text": "Memória recuperada 1", "similarity": 0.95},
                {"text": "Memória recuperada 2", "similarity": 0.85}
            ]
        }
        
        # Cria a janela de chat
        user_id = "user-123"
        window = ChatWindow(user_id)
        
        # Retorna a janela e o mock do MemoryManager
        yield window, mock_memory_manager
        
        # Cleanup - Finaliza a thread de mensagens se estiver rodando
        if hasattr(window, 'message_thread') and window.message_thread.isRunning():
            window.message_thread.quit()
            window.message_thread.wait()
        
        window.close()

class TestChatWindow:
    """Testes para a janela de chat."""
    
    def test_init(self, chat_window):
        """Testa a inicialização da janela de chat."""
        # Descompacta
        window, _ = chat_window
        
        # Verifica que a janela foi configurada corretamente
        assert window.windowTitle() == "Voxy - Chat"
        assert hasattr(window, 'message_input')
        assert hasattr(window, 'send_button')
        assert hasattr(window, 'chat_layout')
    
    def test_send_message(self, qtbot, chat_window, monkeypatch):
        """Testa o envio de mensagem."""
        # Descompacta
        window, mock_memory_manager = chat_window
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Substitui os métodos de adicionar mensagens do assistente/sistema para evitar problemas com a interface gráfica
        window._add_assistant_message = MagicMock()
        window._add_system_message = MagicMock()
        
        # Preenche o campo de mensagem
        window.message_input.setText("Olá, como vai?")
        
        # Clica no botão de enviar
        qtbot.mouseClick(window.send_button, Qt.MouseButton.LeftButton)
        
        # Verificamos se a mensagem foi definida no worker corretamente (última mensagem no histórico)
        assert len(window.message_worker.message) > 0
        assert window.message_worker.message[-1] == {"role": "user", "content": "Olá, como vai?"}
    
    def test_clear_chat(self, qtbot, chat_window):
        """Testa a limpeza do chat."""
        # Descompacta
        window, _ = chat_window
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Adiciona algumas mensagens ao chat para testar a limpeza
        original_add_system_message = window._add_system_message
        window._add_system_message = MagicMock()
        
        # Aciona a limpeza do chat
        window._clear_chat()
        
        # Verifica que a mensagem de sistema foi adicionada
        window._add_system_message.assert_called_once_with("O histórico de chat foi limpo.")
        
        # Restaura o método original
        window._add_system_message = original_add_system_message
    
    def test_logout_request(self, qtbot, chat_window, monkeypatch):
        """Testa a solicitação de logout."""
        # Descompacta
        window, _ = chat_window
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Configura um sinal para verificar se o logout_requested foi emitido
        logout_requested_called = False
        
        def handle_logout_requested():
            nonlocal logout_requested_called
            logout_requested_called = True
        
        window.logout_requested.connect(handle_logout_requested)
        
        # Mock para o método de logout para evitar erros
        window.auth.logout = MagicMock(return_value=(True, "Logout bem-sucedido"))
        
        # Aciona o logout
        window._handle_logout()
        
        # Verifica que o sinal foi emitido
        assert logout_requested_called
    
    @pytest.mark.skip(reason="Não existe método _clear_memories na classe ChatWindow")
    def test_clear_memories(self, qtbot, chat_window, monkeypatch):
        """Testa a limpeza das memórias."""
        # Este teste está sendo ignorado porque a funcionalidade não existe na implementação atual
        pass
        
    def test_clear_memories_button(self, qtbot, chat_window, monkeypatch):
        """Testa se o botão de limpar memórias funciona corretamente."""
        # Descompacta
        window, mock_memory_manager = chat_window
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Simula o usuário confirmando a limpeza
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        
        # Mock para o método de mensagem de informação
        monkeypatch.setattr(QMessageBox, 'information', lambda *args, **kwargs: None)
        
        # Mock para a adição de mensagem do sistema
        window._add_system_message = MagicMock()
        
        # Configura o mock do memory_manager para retornar sucesso
        mock_memory_manager.clear_memories.return_value = True
        
        # Aciona a limpeza das memórias
        window._clear_memories()
        
        # Verifica que o método do memory_manager foi chamado
        mock_memory_manager.clear_memories.assert_called_once_with(window.user_id)
        
        # Verifica que a mensagem de sucesso foi adicionada ao chat
        window._add_system_message.assert_called_once_with("Todas as memórias foram apagadas com sucesso.")
    
    def test_assistant_message_with_memories(self, qtbot, chat_window):
        """Testa se as memórias são exibidas corretamente com a resposta."""
        # Descompacta
        window, _ = chat_window
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Cria uma resposta de teste com memórias
        test_response = {
            "response": "Esta é uma resposta de teste",
            "memories_used": [
                {"memory": "Memória de teste 1", "score": 0.95},
                {"memory": "Memória de teste 2", "score": 0.85}
            ]
        }
        
        # Mock para os métodos que criam widgets
        original_add_layout = window.chat_layout.insertLayout
        layouts_added = []
        
        def mock_add_layout(index, layout):
            layouts_added.append(layout)
            return original_add_layout(index, layout)
        
        window.chat_layout.insertLayout = mock_add_layout
        
        # Adiciona a mensagem com memórias
        window._add_assistant_message(test_response)
        
        # Verifica que a mensagem e memórias foram adicionadas
        assert len(layouts_added) > 0
        
        # Restaura o método original
        window.chat_layout.insertLayout = original_add_layout
    
    def test_show_all_memories(self, qtbot, chat_window, monkeypatch):
        """Testa se o diálogo de todas as memórias é exibido corretamente."""
        # Descompacta
        window, _ = chat_window
        
        # Adiciona a janela ao qtbot
        qtbot.addWidget(window)
        
        # Prepara memórias de teste
        test_memories = [
            {"memory": "Memória de teste 1", "score": 0.95},
            {"memory": "Memória de teste 2", "score": 0.85}
        ]
        
        # Mock para o QMessageBox.exec
        dialog_shown = False
        
        def mock_exec(self):
            nonlocal dialog_shown
            dialog_shown = True
            return QMessageBox.StandardButton.Ok
        
        monkeypatch.setattr(QMessageBox, 'exec', mock_exec)
        
        # Chama o método para mostrar todas as memórias
        window._show_all_memories(test_memories)
        
        # Verifica que o diálogo foi exibido
        assert dialog_shown

def test_show_settings_dialog(qtbot, monkeypatch):
    """Testa a exibição do diálogo de configurações do prompt do sistema"""
    # Configura mocks
    mock_get_prompt = MagicMock(return_value="Prompt de teste")
    mock_save_prompt = MagicMock(return_value=True)
    mock_dialog_exec = MagicMock(return_value=QDialog.DialogCode.Accepted)
    mock_system_message = MagicMock()
    
    # Cria mocks para outras funções da janela de chat
    mock_auth_instance = MagicMock()
    mock_auth_instance.is_logged_in.return_value = True
    
    mock_memory_manager = MagicMock()
    
    # Aplica os mocks
    monkeypatch.setattr("ui.chat_window.get_user_system_prompt", mock_get_prompt)
    monkeypatch.setattr("ui.chat_window.save_user_system_prompt", mock_save_prompt)
    monkeypatch.setattr("ui.chat_window.get_auth_instance", lambda: mock_auth_instance)
    monkeypatch.setattr("ui.chat_window.get_memory_manager", lambda: mock_memory_manager)
    monkeypatch.setattr(SystemPromptDialog, "exec", mock_dialog_exec)
    monkeypatch.setattr(SystemPromptDialog, "get_prompt", lambda self: "Novo prompt de teste")
    
    # Cria a janela de chat
    user_id = "test_user"
    with patch.object(ChatWindow, '_add_system_message') as mock_add_system:
        window = ChatWindow(user_id)
        # Garantir que a thread de mensagens exista para evitar erro no teardown
        if not hasattr(window, 'message_thread'):
            window.message_thread = MagicMock()
            window.message_thread.isRunning = MagicMock(return_value=False)
        
        qtbot.addWidget(window)
        
        # Substitui o método de adicionar mensagem do sistema pelo mock
        window._add_system_message = mock_system_message
        
        # Ativa o método para mostrar as configurações
        window._show_settings()
        
        # Verifica se o diálogo foi executado
        assert mock_dialog_exec.called
        
        # Verifica se o prompt foi salvo
        mock_save_prompt.assert_called_once_with(user_id, "Novo prompt de teste")
        
        # Verifica se a mensagem de sistema foi adicionada
        mock_system_message.assert_called_once_with("Seu prompt personalizado foi atualizado. As próximas mensagens usarão sua configuração.")
        
        # Limpeza explícita
        window.close()
        
        # Não é necessário verificar mock_message_box.assert_called_once() 
        # pois substituímos o QMessageBox.information por uma mensagem no chat 
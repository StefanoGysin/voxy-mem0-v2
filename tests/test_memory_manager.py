"""
Testes unitários para o módulo de gerenciamento de memória vetorial.
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import uuid
from utils.memory_manager import MemoryManager

class TestMemoryManager:
    """Testes para a classe MemoryManager."""
    
    @patch('utils.memory_manager.Memory.from_config')
    def test_init(self, mock_memory_from_config, mock_env_vars):
        """Testa a inicialização do gerenciador de memória."""
        # Configura o mock
        memory_instance = MagicMock()
        mock_memory_from_config.return_value = memory_instance
        
        # Executa
        memory_manager = MemoryManager()
        
        # Verifica
        assert memory_manager.collection_prefix == "voxy"
        assert memory_manager.memory is not None
        # Verifica que o método from_config foi chamado
        mock_memory_from_config.assert_called_once()
    
    def test_init_missing_env_vars(self):
        """Testa a inicialização com variáveis de ambiente faltando."""
        # Configura - remove DATABASE_URL
        with patch.dict(os.environ, {}, clear=True):
            # Verifica que a exceção é lançada
            with pytest.raises(ValueError, match="OPENAI_API_KEY não definida"):
                MemoryManager()
    
    @patch('utils.memory_manager.Memory.from_config')
    def test_retrieve_memories(self, mock_memory_from_config, mock_env_vars):
        """Testa a recuperação de memórias."""
        # Configura o mock
        memory_instance = MagicMock()
        memory_instance.search.return_value = [
            {"id": "memory-1", "text": "Memória de teste 1", "similarity": 0.95},
            {"id": "memory-2", "text": "Memória de teste 2", "similarity": 0.85}
        ]
        mock_memory_from_config.return_value = memory_instance
        
        # Executa
        memory_manager = MemoryManager()
        query = "Qual o meu histórico de conversas?"
        user_id = "user-123"
        
        # Executa
        results = memory_manager.retrieve_memories(query, user_id)
        
        # Verifica
        assert isinstance(results, list)
        assert len(results) == 2
        assert "text" in results[0]
        assert "similarity" in results[0]
        # Verifica que o método de busca da memória foi chamado
        memory_manager.memory.search.assert_called_once()
    
    @patch('utils.memory_manager.Memory.from_config')
    def test_add_memory(self, mock_memory_from_config, mock_env_vars):
        """Testa a adição de memórias."""
        # Configura o mock
        memory_instance = MagicMock()
        memory_instance.add.return_value = "memory-id-123"
        mock_memory_from_config.return_value = memory_instance
        
        # Cria o gerenciador
        memory_manager = MemoryManager()
        
        # Configura os dados
        messages = [
            {"role": "user", "content": "Esta é uma mensagem de teste"},
            {"role": "assistant", "content": "Esta é uma resposta de teste"}
        ]
        user_id = "user-123"
        
        # Executa
        result = memory_manager.add_memory(messages, user_id)
        
        # Verifica
        assert result is True
        # Verifica que o método de adicionar memória foi chamado
        memory_manager.memory.add.assert_called()
    
    @patch('utils.memory_manager.Memory.from_config')
    @patch('utils.memory_manager.OpenAI')
    def test_process_message(self, mock_openai_class, mock_memory_from_config, mock_env_vars):
        """Testa o processamento de mensagens com recuperação de contexto."""
        # Configura os mocks
        memory_instance = MagicMock()
        memory_instance.search.return_value = [
            {"id": "memory-1", "text": "Memória de teste 1", "similarity": 0.95, "memory": "Teste 1"},
            {"id": "memory-2", "text": "Memória de teste 2", "similarity": 0.85, "memory": "Teste 2"}
        ]
        mock_memory_from_config.return_value = memory_instance
        
        openai_instance = MagicMock()
        mock_openai_class.return_value = openai_instance
        
        # Mock para completions
        chat_completion = MagicMock()
        chat_completion.choices = [MagicMock(message=MagicMock(content="Resposta de teste"))]
        openai_instance.chat.completions.create.return_value = chat_completion
        
        # Cria o gerenciador
        memory_manager = MemoryManager()
        
        # Mock para o método chat_completion
        memory_manager.chat_completion = MagicMock(return_value="Resposta de teste")
        
        # Configura os dados do teste
        query = "Qual o meu nome?"
        user_id = "user-123"
        message_list = [{"role": "user", "content": query}]
        
        # Executa
        response = memory_manager.process_message(message_list, user_id)
        
        # Verifica
        assert isinstance(response, dict)
        assert "response" in response
        assert "memories_used" in response
        assert response["response"] == "Resposta de teste"
        assert len(response["memories_used"]) == 2
        
        # Verifica se o método add_memory foi chamado com os parâmetros corretos
        memory_instance.add.assert_called_once()
    
    @patch('utils.memory_manager.Memory.from_config')
    def test_clear_memories(self, mock_memory_from_config, mock_env_vars):
        """Testa a limpeza de memórias de um usuário."""
        # Configura o mock
        memory_instance = MagicMock()
        memory_instance.delete_all = MagicMock(return_value={"deleted": 5})
        mock_memory_from_config.return_value = memory_instance
        
        # Cria o gerenciador
        memory_manager = MemoryManager()
        user_id = "user-123"
        
        # Executa
        result = memory_manager.clear_memories(user_id)
        
        # Verifica
        assert result is True
        # Verifica se o método clear foi chamado com user_id
        memory_manager.memory.clear.assert_called_once_with(user_id=user_id)
    
    @patch('utils.memory_manager.Memory.from_config')
    def test_chat_completion(self, mock_memory_from_config, mock_env_vars):
        """Testa a geração de resposta com o modelo de linguagem."""
        # Configura o mock
        memory_instance = MagicMock()
        mock_memory_from_config.return_value = memory_instance
        
        # Mock para o cliente OpenAI
        with patch('utils.memory_manager.OpenAI') as mock_openai_class:
            openai_instance = MagicMock()
            mock_openai_class.return_value = openai_instance
            
            # Mock para completions
            chat_completion = MagicMock()
            message_mock = MagicMock()
            message_mock.content = "Resposta de teste"
            choice_mock = MagicMock()
            choice_mock.message = message_mock
            chat_completion.choices = [choice_mock]
            openai_instance.chat.completions.create.return_value = chat_completion
            
            # Cria o gerenciador
            memory_manager = MemoryManager()
            
            # Executa o método
            messages = [
                {"role": "system", "content": "Você é um assistente útil"},
                {"role": "user", "content": "Olá, como está?"}
            ]
            
            response = memory_manager.chat_completion(messages)
            
            # Verifica
            assert "Resposta de teste" in response
            openai_instance.chat.completions.create.assert_called_once() 
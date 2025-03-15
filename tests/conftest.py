"""
Configurações e fixtures compartilhadas para os testes do Voxy-Mem0-v2.
"""

import os
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
import time

# Adiciona o diretório raiz ao path para importações
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock para variáveis de ambiente
@pytest.fixture
def mock_env_vars():
    """Mock das variáveis de ambiente necessárias para os testes."""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'sk-test-key-for-testing',
        'MODEL_CHOICE': 'gpt-4o-mini',
        'DATABASE_URL': 'postgres://postgres:password@localhost:5432/postgres?sslmode=require',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-supabase-key',
        'SUPABASE_SERVICE_KEY': 'test-supabase-service-key',
        'LOG_LEVEL': 'DEBUG',
        'GUI_THEME': 'dark',
        'GUI_LANG': 'pt-br',
        'ALLOW_ACCOUNT_CREATION': 'true',
        'REQUIRE_EMAIL_CONFIRMATION': 'false'
    }):
        yield

# Fixtures para mockups dos serviços externos
@pytest.fixture
def mock_openai():
    """Mock do cliente OpenAI."""
    with patch('openai.OpenAI') as mock:
        client_instance = MagicMock()
        mock.return_value = client_instance
        
        # Mock para o método de criar embeddings
        embedding_response = MagicMock()
        embedding_response.data = [{'embedding': [0.1] * 1536}]
        client_instance.embeddings.create.return_value = embedding_response
        
        # Mock para completions
        chat_completion = MagicMock()
        chat_completion.choices = [MagicMock(message=MagicMock(content="Resposta de teste"))]
        client_instance.chat.completions.create.return_value = chat_completion
        
        yield client_instance

@pytest.fixture
def mock_memory():
    """Mock da classe Memory da biblioteca mem0ai."""
    # Primeiro, vamos fazer patch do método from_config para evitar a validação
    with patch('mem0.Memory.from_config') as mock_from_config:
        # Criar a instância mock que será retornada
        memory_instance = MagicMock()
        mock_from_config.return_value = memory_instance
        
        # Mock para métodos comuns
        memory_instance.add.return_value = "memory-id-123"
        memory_instance.search.return_value = [
            {"id": "memory-1", "text": "Memória de teste 1", "similarity": 0.95},
            {"id": "memory-2", "text": "Memória de teste 2", "similarity": 0.85}
        ]
        memory_instance.delete.return_value = {"deleted": 5}
        memory_instance.query.return_value = {"count": 42}
        
        yield memory_instance

@pytest.fixture
def mock_supabase():
    """Mock do cliente Supabase."""
    # Patch direto da função create_client para evitar a validação de chave
    with patch('supabase.create_client') as mock_create_client:
        # Criamos uma instância mock do cliente Supabase
        supabase_instance = MagicMock()
        mock_create_client.return_value = supabase_instance
        
        # Mock para auth
        auth_mock = MagicMock()
        supabase_instance.auth = auth_mock
        
        # Mock para sign_in_with_password
        auth_response = MagicMock()
        auth_response.session = {"access_token": "fake-token", "expires_at": int(time.time()) + 3600}
        auth_response.user = {"id": "user-123", "email": "test@example.com"}
        auth_mock.sign_in_with_password.return_value = auth_response
        
        # Mock para sign_up
        signup_response = MagicMock()
        signup_response.user = {"id": "user-456", "email": "new@example.com"}
        auth_mock.sign_up.return_value = signup_response
        
        # Mock para sign_out
        auth_mock.sign_out.return_value = None
        
        # Mock para operações de banco de dados
        table_mock = MagicMock()
        supabase_instance.table.return_value = table_mock
        
        select_mock = MagicMock()
        table_mock.select.return_value = select_mock
        
        execute_mock = MagicMock()
        select_mock.execute.return_value = {"data": []}
        
        yield supabase_instance

@pytest.fixture
def qapp():
    """Fixture que fornece uma instância QApplication para testes de GUI."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app 
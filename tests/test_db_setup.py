"""
Testes unitários para o módulo de configuração do banco de dados.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import os
import psycopg2
from utils.db_setup import setup_database, DatabaseSetup

@pytest.fixture
def mock_psycopg2():
    """Mock para a biblioteca psycopg2."""
    with patch('psycopg2.connect') as mock_connect:
        # Configura o objeto de conexão e cursor
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        yield mock_connect, mock_conn, mock_cursor

@pytest.fixture
def mock_vecs():
    """Mock para a biblioteca vecs."""
    with patch('vecs.create_client') as mock_create_client:
        # Configura o objeto client
        vecs_client = MagicMock()
        mock_create_client.return_value = vecs_client
        
        # Mock para o método list_collections
        vecs_client.list_collections.return_value = ["voxy_memories"]
        
        yield vecs_client

class TestDatabaseSetup:
    """Testes para a classe DatabaseSetup."""
    
    def test_init(self, mock_env_vars):
        """Testa a inicialização da classe DatabaseSetup."""
        # Executa
        db_setup = DatabaseSetup()
        
        # Verifica
        assert db_setup.database_url is not None
        assert db_setup.conn is None
    
    def test_init_missing_env_vars(self):
        """Testa a inicialização com variáveis de ambiente faltando."""
        # Configura - remove DATABASE_URL
        with patch.dict(os.environ, {}, clear=True):
            # Verifica que a exceção é lançada
            with pytest.raises(ValueError, match="DATABASE_URL não definida"):
                DatabaseSetup()
    
    def test_check_connection(self, mock_env_vars, mock_psycopg2):
        """Testa a verificação de conexão com o banco de dados."""
        # Descompacta os mocks
        mock_connect, mock_conn, mock_cursor = mock_psycopg2
        
        # Configura o cursor para retornar um resultado válido
        mock_cursor.fetchone.return_value = (1,)
        
        # Executa
        db_setup = DatabaseSetup()
        result = db_setup.check_connection()
        
        # Verifica
        assert result is True
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_with("SELECT 1")
    
    def test_check_connection_failure(self, mock_env_vars, mock_psycopg2):
        """Testa a falha na verificação de conexão."""
        # Descompacta os mocks
        mock_connect, _, _ = mock_psycopg2
        
        # Configura o connect para lançar uma exceção
        mock_connect.side_effect = psycopg2.Error("Erro de conexão")
        
        # Executa
        db_setup = DatabaseSetup()
        result = db_setup.check_connection()
        
        # Verifica
        assert result is False
        mock_connect.assert_called_once()
    
    def test_check_pgvector_extension(self, mock_env_vars, mock_psycopg2):
        """Testa a verificação da extensão pgvector."""
        # Descompacta os mocks
        mock_connect, mock_conn, mock_cursor = mock_psycopg2
        
        # Configura o cursor para retornar um resultado positivo
        mock_cursor.fetchone.return_value = ('vector',)
        
        # Executa
        db_setup = DatabaseSetup()
        # Precisamos configurar a conexão primeiro
        db_setup.conn = mock_conn
        result = db_setup.check_pgvector_extension()
        
        # Verifica
        assert result is True
        mock_cursor.execute.assert_called_with("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    
    def test_setup_user_tables(self, mock_env_vars, mock_psycopg2):
        """Testa a criação das tabelas de usuários."""
        # Descompacta os mocks
        mock_connect, mock_conn, mock_cursor = mock_psycopg2
        
        # Configura o cursor para retornar que a tabela não existe
        mock_cursor.fetchone.return_value = (None,)
        
        # Executa
        db_setup = DatabaseSetup()
        # Precisamos configurar a conexão primeiro
        db_setup.conn = mock_conn
        result = db_setup.setup_user_tables()
        
        # Verifica
        assert result is True
        assert mock_cursor.execute.call_count > 0
        mock_conn.commit.assert_called_once()
    
    def test_get_vector_collections(self, mock_env_vars, mock_vecs):
        """Testa a obtenção das coleções de vetores."""
        # Configura
        mock_collection = MagicMock()
        mock_collection.name = "voxy_memories"
        mock_vecs.list_collections.return_value = [mock_collection]
        
        # Executa
        db_setup = DatabaseSetup()
        collections = db_setup.get_vector_collections()
        
        # Verifica
        assert isinstance(collections, list)
        assert "voxy_memories" in collections
    
    def test_setup_database_success(self, mock_env_vars):
        """Testa o sucesso da configuração completa do banco de dados."""
        # Mock do DatabaseSetup
        with patch('utils.db_setup.DatabaseSetup') as mock_db_setup_class:
            # Configura a instância mock
            mock_db_setup = MagicMock()
            mock_db_setup_class.return_value = mock_db_setup
            
            # Configura os retornos dos métodos
            mock_db_setup.check_connection.return_value = True
            mock_db_setup.check_pgvector_extension.return_value = True
            mock_db_setup.setup_user_tables.return_value = True
            mock_db_setup.get_vector_collections.return_value = ["voxy_memories"]
            mock_db_setup.setup_database.return_value = True
            
            # Executa a função
            result = setup_database()
            
            # Verifica
            assert result is True
            # Verifica que o método setup_database foi chamado
            mock_db_setup.setup_database.assert_called_once()
    
    def test_setup_database_connection_failure(self, mock_env_vars):
        """Testa a falha na configuração do banco de dados devido à conexão."""
        # Mock do DatabaseSetup
        with patch('utils.db_setup.DatabaseSetup') as mock_db_setup_class:
            # Configura a instância mock
            mock_db_setup = MagicMock()
            mock_db_setup_class.return_value = mock_db_setup
            
            # Configura os retornos dos métodos
            mock_db_setup.setup_database.side_effect = Exception("Erro ao configurar banco de dados")
            
            # Executa a função
            result = setup_database()
            
            # Verifica
            assert result is False
            # Verifica que o método setup_database foi chamado
            mock_db_setup.setup_database.assert_called_once() 
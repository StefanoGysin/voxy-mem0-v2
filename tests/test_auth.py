"""
Testes para o módulo de autenticação do Voxy-Mem0-v2
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa os módulos a serem testados
from utils.auth import (
    SupabaseAuth, get_auth_instance, 
    get_user_system_prompt, save_user_system_prompt,
    DEFAULT_SYSTEM_PROMPT
)

class TestSupabaseAuth:
    """Testes para a classe SupabaseAuth."""
    
    def test_init(self, mock_env_vars, mock_supabase):
        """Testa a inicialização do gerenciador de autenticação."""
        # Patch direto da função create_client para evitar falha de validação da chave API
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Executa
            auth_manager = SupabaseAuth()
            
            # Verifica que o cliente foi inicializado
            assert auth_manager.client is not None
            # Na implementação atual, estes são apenas valores locais, não atributos
            assert auth_manager.supabase_url is not None
            assert auth_manager.supabase_key is not None
    
    def test_init_missing_env_vars(self):
        """Testa a inicialização com variáveis de ambiente faltando."""
        # Configura - remove variáveis do Supabase
        with patch.dict(os.environ, {}, clear=True):
            # Verifica que a exceção é lançada
            with pytest.raises(ValueError):
                SupabaseAuth()
    
    def test_login_success(self, mock_env_vars, mock_supabase):
        """Testa o login bem-sucedido."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Executa
            auth_manager = SupabaseAuth()
            email = "test@example.com"
            password = "senha_segura"
            
            success, message, user = auth_manager.login(email, password)
            
            # Verifica
            assert success is True
            assert user is not None
            assert user["id"] == "user-123"
            assert user["email"] == email
            # Verifica que o método de login foi chamado com os parâmetros no formato correto
            auth_manager.client.auth.sign_in_with_password.assert_called_once_with({
                "email": email, 
                "password": password
            })
    
    def test_login_failure(self, mock_env_vars, mock_supabase):
        """Testa o login com falha."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Configura o mock para lançar uma exceção
            mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")
            
            # Executa
            auth_manager = SupabaseAuth()
            email = "invalid@example.com"
            password = "senha_incorreta"
            
            success, message, user = auth_manager.login(email, password)
            
            # Verifica
            assert success is False
            assert user is None
            assert "credenciais" in message.lower() or "falha" in message.lower()
    
    def test_register_success(self, mock_env_vars, mock_supabase):
        """Testa o registro bem-sucedido de um novo usuário."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Executa
            auth_manager = SupabaseAuth()
            email = "new_user@example.com"
            password = "senha_segura"
            confirm_password = "senha_segura"
            
            success, message = auth_manager.register(email, password, confirm_password)
            
            # Verifica
            assert success is True
            assert "sucesso" in message.lower()
            # Verifica que o método de registro foi chamado com os parâmetros no formato correto
            auth_manager.client.auth.sign_up.assert_called_once_with({
                "email": email, 
                "password": password
            })
    
    def test_register_disabled(self, mock_env_vars, mock_supabase):
        """Testa o registro quando está desabilitado."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Modifica a variável de ambiente ALLOW_ACCOUNT_CREATION
            with patch.dict(os.environ, {'ALLOW_ACCOUNT_CREATION': 'false'}):
                # Redefine a constante no módulo auth.py para simular a alteração da variável
                with patch('utils.auth.ALLOW_ACCOUNT_CREATION', False):
                    # Executa
                    auth_manager = SupabaseAuth()
                    email = "new_user@example.com"
                    password = "senha_segura"
                    confirm_password = "senha_segura"
                    
                    success, message = auth_manager.register(email, password, confirm_password)
                    
                    # Verifica
                    assert success is False
                    assert "desativada" in message.lower()
    
    def test_register_password_mismatch(self, mock_env_vars, mock_supabase):
        """Testa o registro com senhas que não coincidem."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Executa
            auth_manager = SupabaseAuth()
            email = "new_user@example.com"
            password = "senha_segura"
            confirm_password = "senha_diferente"
            
            success, message = auth_manager.register(email, password, confirm_password)
            
            # Verifica
            assert success is False
            assert "coincidem" in message.lower() or "diferentes" in message.lower()
    
    def test_register_failure(self, mock_env_vars, mock_supabase):
        """Testa o registro com falha."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Configura o mock para lançar uma exceção
            mock_supabase.auth.sign_up.side_effect = Exception("User already registered")
            
            # Executa
            auth_manager = SupabaseAuth()
            email = "existing@example.com"
            password = "senha_fraca"
            confirm_password = "senha_fraca"
            
            success, message = auth_manager.register(email, password, confirm_password)
            
            # Verifica
            assert success is False
            # Ajusta a verificação para a mensagem real
            assert "já está registrado" in message.lower()
    
    def test_logout(self, mock_env_vars, mock_supabase):
        """Testa o logout."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Configura uma sessão ativa simulada
            mock_supabase.auth.sign_out.return_value = None
            
            # Executa
            auth_manager = SupabaseAuth()
            
            # Simula um usuário logado
            auth_manager.current_user = {"id": "user-123"}
            auth_manager.session = {"access_token": "fake-token"}
            
            success, message = auth_manager.logout()
            
            # Verifica
            assert success is True
            # Verifica que o método de logout foi chamado
            auth_manager.client.auth.sign_out.assert_called_once()
    
    def test_is_logged_in(self, mock_env_vars, mock_supabase):
        """Testa a verificação de login ativo."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Executa
            auth_manager = SupabaseAuth()
            
            # Configura o estado de login
            auth_manager.current_user = {"id": "user-123"}
            
            # Executa
            result = auth_manager.is_logged_in()
            
            # Verifica
            assert result is True
    
    def test_is_logged_in_no_session(self, mock_env_vars, mock_supabase):
        """Testa a verificação de login sem sessão ativa."""
        # Configura - patch do create_client para evitar a validação de chave
        with patch('utils.auth.create_client') as mock_create_client:
            mock_create_client.return_value = mock_supabase
            
            # Executa
            auth_manager = SupabaseAuth()
            
            # Configura estado sem login
            auth_manager.current_user = None
            
            # Executa
            result = auth_manager.is_logged_in()
            
            # Verifica
            assert result is False

# Testes para as funções de gerenciamento de prompt do sistema
class TestSystemPrompt:
    """Testes para as funções de gerenciamento de prompt do sistema"""
    
    def test_get_user_system_prompt_no_user_id(self):
        """Testa a obtenção do prompt padrão quando não há ID de usuário"""
        result = get_user_system_prompt(None)
        assert result == DEFAULT_SYSTEM_PROMPT
    
    @patch("utils.auth.create_client")
    def test_get_user_system_prompt_error(self, mock_create_client):
        """Testa a obtenção do prompt padrão quando ocorre um erro"""
        # Configurando o mock para lançar uma exceção
        mock_client = MagicMock()
        mock_client.table.side_effect = Exception("Erro de teste")
        mock_create_client.return_value = mock_client
        
        # Testando a função
        result = get_user_system_prompt("test_user_id")
        
        # Verificações
        assert result == DEFAULT_SYSTEM_PROMPT
    
    def test_save_user_system_prompt_invalid_params(self):
        """Testa o salvamento com parâmetros inválidos"""
        # Sem user_id
        result1 = save_user_system_prompt(None, "Teste")
        # Sem prompt
        result2 = save_user_system_prompt("test_user_id", None)
        # Ambos vazios
        result3 = save_user_system_prompt(None, None)
        
        assert result1 is False
        assert result2 is False
        assert result3 is False
    
    @patch("utils.auth.create_client")
    def test_save_user_system_prompt_error(self, mock_create_client):
        """Testa o tratamento de erro ao salvar o prompt do sistema"""
        # Configurando o mock para lançar uma exceção
        mock_client = MagicMock()
        mock_client.table.side_effect = Exception("Erro de teste")
        mock_create_client.return_value = mock_client
        
        # Testando a função
        result = save_user_system_prompt("test_user_id", "Teste")
        
        # Verificações
        assert result is False 
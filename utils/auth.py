"""
Módulo de autenticação para o Voxy-Mem0-v2
Gerencia autenticação de usuários com o Supabase
"""

import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
import jwt
from typing import Dict, Optional, Tuple
import json
import time
from datetime import datetime

# Configuração de logging
logger = logging.getLogger("voxy-auth")

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Prompt padrão do sistema
DEFAULT_SYSTEM_PROMPT = """Você é um assistente AI útil, amigável e detalhista.
Responda às perguntas da maneira mais útil possível.
Se você não souber a resposta a uma pergunta, não invente informações - apenas diga que não sabe.
Baseie suas respostas em fatos e conhecimentos precisos."""

# Outras configurações
ALLOW_ACCOUNT_CREATION = os.getenv('ALLOW_ACCOUNT_CREATION', 'false').lower() == 'true'
REQUIRE_EMAIL_CONFIRMATION = os.getenv('REQUIRE_EMAIL_CONFIRMATION', 'true').lower() == 'true'

class SupabaseAuth:
    """
    Classe para gerenciar autenticação de usuários com Supabase
    """
    def __init__(self):
        """
        Inicializa o cliente Supabase para autenticação
        """
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias")
            raise ValueError("Configuração do Supabase incompleta. Verifique o arquivo .env")
        
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Cliente Supabase inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Supabase: {str(e)}")
            raise
        
        # Estado do usuário atual
        self.current_user = None
        self.session = None
        
        # Log de configurações
        logger.info(f"Configuração de confirmação de email: {'ATIVADA' if REQUIRE_EMAIL_CONFIRMATION else 'DESATIVADA'}")
        logger.info(f"Configuração de criação de contas: {'ATIVADA' if ALLOW_ACCOUNT_CREATION else 'DESATIVADA'}")
    
    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Realiza login de usuário com email e senha
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (sucesso, mensagem, dados do usuário)
        """
        try:
            logger.info(f"Tentativa de login para o usuário: {email}")
            
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            self.session = response.session
            self.current_user = response.user
            
            logger.info(f"Login bem-sucedido para o usuário: {email}")
            return True, "Login realizado com sucesso", self.current_user
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erro no login: {error_msg}")
            
            if "Invalid login credentials" in error_msg:
                return False, "Credenciais inválidas. Verifique seu email e senha.", None
            elif "Email not confirmed" in error_msg:
                # Verificamos a configuração de confirmação de email
                if not REQUIRE_EMAIL_CONFIRMATION:
                    # Devemos auto-confirmar o email
                    logger.info(f"Tentando auto-confirmar email para: {email}")
                    
                    if self.supabase_service_key:
                        try:
                            # Cria um cliente admin com a chave de serviço
                            admin_client = create_client(self.supabase_url, self.supabase_service_key)
                            
                            # Busca o usuário pelo email
                            user_data = admin_client.from_('auth.users').select('id').eq('email', email).execute()
                            
                            if user_data and user_data.data and len(user_data.data) > 0:
                                user_id = user_data.data[0]['id']
                                
                                # Confirma o email do usuário
                                try:
                                    admin_client.rpc('confirm_user', {'uid': user_id}).execute()
                                    logger.info(f"Email auto-confirmado via RPC para: {email}")
                                except Exception as rpc_err:
                                    logger.warning(f"Não foi possível confirmar via RPC: {rpc_err}")
                                    
                                    # Alternativa: atualizar diretamente a tabela
                                    try:
                                        admin_client.table('auth.users').update({'email_confirmed_at': 'now()'}).eq('id', user_id).execute()
                                        logger.info(f"Email confirmado via atualização direta para: {email}")
                                    except Exception as db_err:
                                        logger.warning(f"Falha ao atualizar tabela: {db_err}")
                                
                                logger.info(f"Email auto-confirmado para: {email}, tentando login novamente")
                                
                                # Tenta login novamente
                                try:
                                    response = self.client.auth.sign_in_with_password({
                                        "email": email,
                                        "password": password
                                    })
                                    
                                    self.session = response.session
                                    self.current_user = response.user
                                    
                                    return True, "Login realizado com sucesso", self.current_user
                                except Exception as retry_err:
                                    logger.error(f"Erro no segundo login: {str(retry_err)}")
                        except Exception as confirm_err:
                            logger.error(f"Erro ao confirmar email: {str(confirm_err)}")
                    
                    # Se chegarmos aqui, não conseguimos auto-confirmar
                    return False, "Não foi possível ativar sua conta automaticamente. Entre em contato com o suporte.", None
                else:
                    # Confirmação de email é necessária
                    return False, "Email não confirmado. Verifique sua caixa de entrada para confirmar sua conta.", None
            else:
                return False, f"Erro no login: {error_msg}", None
    
    def register(self, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Registra um novo usuário
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            confirm_password: Confirmação da senha
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        # Verifica se a criação de contas está habilitada
        if not ALLOW_ACCOUNT_CREATION:
            logger.warning(f"Tentativa de registro para {email} rejeitada: criação de contas desativada")
            return False, "A criação de contas está desativada. Entre em contato com o administrador."
        
        # Validações básicas
        if password != confirm_password:
            return False, "As senhas não coincidem"
        
        if len(password) < 6:
            return False, "A senha deve ter pelo menos 6 caracteres"
            
        try:
            logger.info(f"Tentativa de registro para o usuário: {email}")
            
            # Registra o usuário
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # Após o registro, verificamos se precisamos auto-confirmar o email
            if not REQUIRE_EMAIL_CONFIRMATION and self.supabase_service_key:
                logger.info(f"Auto-confirmação de email ativada para: {email}")
                try:
                    # Cria um cliente admin com a chave de serviço para confirmar o email
                    admin_client = create_client(self.supabase_url, self.supabase_service_key)
                    
                    # Obtém o ID do usuário da resposta de registro
                    user_id = response.user.id
                    
                    # Tenta confirmar o email
                    try:
                        admin_client.rpc('confirm_user', {'uid': user_id}).execute()
                        logger.info(f"Email auto-confirmado para o usuário: {email}")
                    except Exception as confirm_error:
                        logger.warning(f"Não foi possível confirmar via RPC: {confirm_error}")
                        
                        # Alternativa: atualizar diretamente a tabela de usuários
                        try:
                            admin_client.table('auth.users').update({'email_confirmed_at': 'now()'}).eq('id', user_id).execute()
                            logger.info(f"Email confirmado via atualização direta para o usuário: {email}")
                        except Exception as db_error:
                            logger.warning(f"Não foi possível atualizar a confirmação do email no banco: {db_error}")
                    
                except Exception as admin_error:
                    logger.warning(f"Não foi possível utilizar o cliente admin: {admin_error}")
            
            logger.info(f"Registro realizado para o usuário: {email}")
            
            if REQUIRE_EMAIL_CONFIRMATION:
                return True, "Registro realizado com sucesso. Verifique seu email para confirmar a conta."
            else:
                return True, "Registro realizado com sucesso! Você já pode fazer login."
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erro no registro: {error_msg}")
            
            if "User already registered" in error_msg:
                return False, "Este email já está registrado."
            else:
                return False, f"Erro no registro: {error_msg}"
    
    def logout(self) -> Tuple[bool, str]:
        """
        Realiza logout do usuário atual
        
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        if not self.current_user:
            return True, "Nenhum usuário logado"
            
        try:
            self.client.auth.sign_out()
            self.current_user = None
            self.session = None
            
            logger.info("Logout realizado com sucesso")
            return True, "Logout realizado com sucesso"
        except Exception as e:
            logger.error(f"Erro no logout: {str(e)}")
            return False, f"Erro no logout: {str(e)}"
    
    def get_current_user(self) -> Optional[Dict]:
        """
        Retorna os dados do usuário atual
        
        Returns:
            Optional[Dict]: Dados do usuário atual ou None se não estiver logado
        """
        return self.current_user
    
    def is_logged_in(self) -> bool:
        """
        Verifica se há um usuário logado
        
        Returns:
            bool: True se houver um usuário logado, False caso contrário
        """
        return self.current_user is not None
    
    def get_user_id(self) -> Optional[str]:
        """
        Retorna o ID do usuário atual
        
        Returns:
            Optional[str]: ID do usuário atual ou None se não estiver logado
        """
        if not self.current_user:
            return None
        return self.current_user.id
    
    def refresh_session(self) -> bool:
        """
        Atualiza a sessão do usuário
        
        Returns:
            bool: True se a sessão foi atualizada com sucesso, False caso contrário
        """
        if not self.session:
            return False
            
        try:
            response = self.client.auth.refresh_session()
            self.session = response.session
            self.current_user = response.user
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar sessão: {str(e)}")
            return False


# Singleton para uso em toda a aplicação
def get_auth_instance():
    """
    Retorna uma instância da classe SupabaseAuth
    
    Returns:
        SupabaseAuth: Instância única da classe SupabaseAuth
    """
    if not hasattr(get_auth_instance, "instance"):
        get_auth_instance.instance = SupabaseAuth()
    return get_auth_instance.instance 

def get_user_system_prompt(user_id):
    """
    Recupera o prompt do sistema personalizado do usuário
    
    Args:
        user_id: ID do usuário
        
    Returns:
        str: Prompt do sistema personalizado ou o prompt padrão se não existir
    """
    if not user_id:
        logger.warning("ID de usuário não fornecido para recuperar prompt do sistema")
        return DEFAULT_SYSTEM_PROMPT
        
    try:
        # Cria uma instância do cliente Supabase se necessário
        if not hasattr(get_user_system_prompt, "supabase"):
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.error("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias")
                return DEFAULT_SYSTEM_PROMPT
                
            get_user_system_prompt.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Busca o prompt personalizado do usuário
        response = get_user_system_prompt.supabase.table("user_prompts").select("system_prompt").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Prompt personalizado encontrado para o usuário {user_id}")
            return response.data[0]["system_prompt"]
        else:
            logger.info(f"Nenhum prompt personalizado encontrado para o usuário {user_id}, usando padrão")
            return DEFAULT_SYSTEM_PROMPT
            
    except Exception as e:
        logger.error(f"Erro ao recuperar prompt do sistema: {e}")
        return DEFAULT_SYSTEM_PROMPT

def save_user_system_prompt(user_id, system_prompt):
    """
    Salva o prompt do sistema personalizado do usuário
    
    Args:
        user_id: ID do usuário
        system_prompt: Prompt do sistema personalizado
        
    Returns:
        bool: True se o prompt foi salvo com sucesso, False caso contrário
    """
    if not user_id or not system_prompt:
        logger.warning("ID de usuário ou prompt não fornecidos")
        return False
        
    try:
        # Cria uma instância do cliente Supabase se necessário
        if not hasattr(save_user_system_prompt, "supabase"):
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.error("Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias")
                return False
                
            save_user_system_prompt.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Verifica se já existe um registro para este usuário
        response = save_user_system_prompt.supabase.table("user_prompts").select("id").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            # Atualiza o registro existente
            save_user_system_prompt.supabase.table("user_prompts").update({
                "system_prompt": system_prompt,
                "updated_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()
            
            logger.info(f"Prompt do sistema atualizado para o usuário {user_id}")
        else:
            # Cria um novo registro
            save_user_system_prompt.supabase.table("user_prompts").insert({
                "user_id": user_id,
                "system_prompt": system_prompt
            }).execute()
            
            logger.info(f"Novo prompt do sistema criado para o usuário {user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao salvar prompt do sistema: {e}")
        return False 
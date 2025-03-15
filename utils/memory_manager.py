"""
Módulo para gerenciamento de memória vetorial usando a biblioteca Mem0.
Responsável pela recuperação e armazenamento de memórias no Supabase.
"""

import os
import logging
from dotenv import load_dotenv
from mem0 import Memory
from openai import OpenAI
from typing import Dict, List, Optional, Any
import time
import uuid
from datetime import datetime
import sys

# Adiciona o diretório raiz ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Importa o utilitário de autenticação
from utils.auth import get_user_system_prompt

# Configuração de logging
logger = logging.getLogger("voxy-memory")

# Carrega variáveis de ambiente
load_dotenv()

class MemoryManager:
    """
    Gerencia a memória vetorial para o assistente Voxy-Mem0.
    Integra com a biblioteca Mem0 e OpenAI para armazenamento e recuperação de memórias.
    """
    def __init__(self, collection_prefix: str = "voxy"):
        """
        Inicializa o gerenciador de memória vetorial
        
        Args:
            collection_prefix: Prefixo para as coleções de memórias no banco de dados
        """
        self.collection_prefix = collection_prefix
        self.openai_client = None
        self.memory = None
        
        # Inicializa os clientes
        self._setup_memory()
    
    def _setup_memory(self):
        """
        Configura e inicializa a camada de memória usando Mem0 e OpenAI
        
        Raises:
            ValueError: Se as variáveis de ambiente necessárias não estiverem configuradas
            Exception: Para outros erros de configuração
        """
        logger.info("Inicializando configuração da memória")
        
        # Verifica configurações necessárias
        database_url = os.environ.get('DATABASE_URL')
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        if not database_url:
            logger.error("ERRO: DATABASE_URL não está configurado no arquivo .env!")
            raise ValueError("DATABASE_URL não configurado")
                
        if not openai_api_key:
            logger.error("ERRO: OPENAI_API_KEY não está configurado no arquivo .env!")
            raise ValueError("OPENAI_API_KEY não configurado")
        
        # Configuração do agente com memória
        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": os.getenv('MODEL_CHOICE', 'gpt-4o-mini')
                }
            },
            "vector_store": {
                "provider": "supabase",
                "config": {
                    "connection_string": database_url,
                    "collection_name": f"{self.collection_prefix}_memories"
                }
            }    
        }
        
        try:
            self.openai_client = OpenAI()
            self.memory = Memory.from_config(config)
            logger.info("Configuração da memória concluída com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar memória: {str(e)}")
            
            # Verificações específicas para erros comuns
            error_str = str(e)
            if "401" in error_str and "OpenAI" in error_str:
                logger.error("Erro de autenticação com a OpenAI. Verifique sua chave de API.")
                raise ValueError("Erro de autenticação com a OpenAI")
            elif "supabase" in error_str.lower() or "database" in error_str.lower() or "db" in error_str.lower():
                logger.error("Erro de conexão com o Supabase. Verifique a URL de conexão.")
                raise ValueError("Erro de conexão com o Supabase")
            
            raise
    
    def retrieve_memories(self, query: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recupera memórias relevantes para uma consulta
        
        Args:
            query: Consulta para buscar memórias relevantes
            user_id: ID do usuário para filtrar memórias
            limit: Número máximo de memórias a serem recuperadas
            
        Returns:
            List[Dict[str, Any]]: Lista de memórias relevantes
        """
        try:
            logger.info(f"Recuperando memórias para o usuário {user_id} com a consulta: {query}")
            
            # Usando o método search conforme documentação oficial
            search_results = self.memory.search(
                query=query, 
                user_id=user_id, 
                limit=limit
            )
            
            # Verifica se os resultados estão em formato de lista ou dicionário
            if isinstance(search_results, dict) and "results" in search_results:
                memories = search_results.get("results", [])
            else:
                # Versões mais recentes podem retornar diretamente uma lista
                memories = search_results if isinstance(search_results, list) else []
                
            # Exibe informações sobre memórias recuperadas para debugging
            if memories and len(memories) > 0:
                for mem in memories:
                    logger.info(str(mem))
            
            logger.info(f"Recuperadas {len(memories)} memórias relevantes")
            return memories
        except Exception as e:
            logger.error(f"Erro ao recuperar memórias: {str(e)}")
            return []
    
    def add_memory(self, messages: list, user_id: str) -> bool:
        """
        Adiciona uma nova memória para o usuário
        
        Args:
            messages: Lista de mensagens no formato {"role": "user"/"assistant", "content": "texto"}
            user_id: ID do usuário para armazenar a memória
            
        Returns:
            bool: True se a memória foi adicionada com sucesso, False caso contrário
        """
        try:
            # Validar os parâmetros
            if not isinstance(messages, list):
                logger.error(f"Parâmetro 'messages' inválido: {messages}. Deve ser uma lista.")
                return False
                
            if not messages:
                logger.error("Lista de mensagens vazia. Não há memória para adicionar.")
                return False
                
            for msg in messages:
                if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                    logger.error(f"Formato de mensagem inválido: {msg}")
                    return False
            
            if not user_id or not isinstance(user_id, str):
                logger.error(f"ID de usuário inválido: {user_id}")
                return False
            
            # Método 1: Adicionar diretamente usando a API do Mem0ai conforme documentação
            try:
                # Criação de metadata adicional
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "app": "voxy-mem0-v2"
                }
                
                # Usar o método add diretamente no objeto Memory
                # conforme documentação: m.add(messages, user_id="alice", metadata={"category": "movie_recommendations"})
                result = self.memory.add(
                    messages,  # Passa diretamente a lista de mensagens
                    user_id=user_id,
                    metadata=metadata
                )
                
                logger.info(f"Memória adicionada com sucesso: {result}")
                return True
                
            except Exception as e:
                # Se falhar, tenta alternativa mais simples
                logger.warning(f"Erro ao adicionar memória com método principal: {e}")
                
                try:
                    # Método 2: Se o primeiro método falhar, tenta combinar as mensagens em um texto único
                    processed_text = ""
                    for msg in messages:
                        processed_text += f"{msg['role'].upper()}: {msg['content']}\n"
                    
                    processed_text = processed_text.strip()
                    
                    if not processed_text:
                        logger.error("Texto processado vazio")
                        return False
                    
                    # Adiciona o texto como uma memória única
                    result = self.memory.add(
                        [processed_text],  # Formato da API: lista com texto
                        user_id=user_id,
                        metadata={"source": "combined_messages"}
                    )
                    
                    logger.info(f"Memória adicionada com sucesso (método alternativo 1): {result}")
                    return True
                    
                except Exception as alt_error:
                    logger.warning(f"Erro no método alternativo 1: {alt_error}")
                    
                    try:
                        # Método 3: Última alternativa - usar apenas o conteúdo das mensagens
                        combined_text = " ".join([msg.get("content", "") for msg in messages if msg.get("content")])
                        
                        if not combined_text.strip():
                            logger.error("Conteúdo combinado vazio")
                            return False
                        
                        # Tenta com abordagem mais simples possível
                        memory_data = {"text": combined_text}
                        result = self.memory.add(memory_data, user_id=user_id)
                        
                        logger.info(f"Memória adicionada com sucesso (método alternativo 2)")
                        return True
                        
                    except Exception as last_error:
                        logger.error(f"Todos os métodos de adição de memória falharam: {last_error}")
                        return False
                        
        except Exception as e:
            logger.error(f"Erro geral ao adicionar memória: {e}")
            return False
    
    def clear_memories(self, user_id: str) -> bool:
        """
        Limpa todas as memórias de um usuário
        
        Args:
            user_id: ID do usuário para limpar memórias
            
        Returns:
            bool: True se as memórias foram limpas com sucesso, False caso contrário
        """
        try:
            logger.info(f"Limpando memórias do usuário {user_id}")
            
            # Usando a API do Mem0ai para excluir memórias
            # Conforme documentação: m.delete_all(user_id="alice")
            try:
                self.memory.delete_all(user_id=user_id)
                logger.info(f"Todas as memórias do usuário {user_id} foram apagadas com sucesso")
                return True
            except AttributeError:
                # Se delete_all não existir, tenta abordagem alternativa
                logger.warning("Método delete_all não disponível, tentando alternativa")
                
                try:
                    # Em algumas versões, pode ser que o método tenha outro nome
                    if hasattr(self.memory, "reset"):
                        self.memory.reset(user_id=user_id)
                        logger.info(f"Memórias do usuário {user_id} foram resetadas com sucesso")
                        return True
                    else:
                        logger.warning("Nenhum método de limpeza de memórias disponível na API")
                        return False
                except Exception as alt_error:
                    logger.error(f"Erro no método alternativo de limpeza: {alt_error}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao limpar memórias: {str(e)}")
            return False
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """
        Gera uma resposta usando o modelo da OpenAI
        
        Args:
            messages: Lista de mensagens no formato da OpenAI
            model: Modelo da OpenAI a ser usado (opcional)
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        try:
            logger.info("Gerando resposta com o modelo da OpenAI")
            
            response = self.openai_client.chat.completions.create(
                model=model or os.getenv('MODEL_CHOICE', 'gpt-4o-mini'),
                messages=messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {str(e)}")
            return f"Erro na comunicação com a OpenAI: {str(e)}"
    
    def process_message(self, message: str, user_id: str) -> dict:
        """
        Processa uma mensagem do usuário, recupera memórias relevantes e gera uma resposta
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário
            
        Returns:
            dict: Dicionário contendo a resposta do assistente e as memórias utilizadas
        """
        try:
            # Recupera memórias relevantes
            memories = self.retrieve_memories(message, user_id)
            memories_str = "\n".join(f"- {entry.get('memory', '')}" for entry in memories)
            
            # Obtém o prompt personalizado do usuário
            custom_system_prompt = get_user_system_prompt(user_id)
            
            # Prepara o prompt com o contexto das memórias
            system_prompt = (
                f"{custom_system_prompt}\n\n"
                "Responda à pergunta do usuário com base nas memórias disponíveis e na consulta atual.\n"
                f"Memórias do Usuário:\n{memories_str}"
            )
            
            # Prepara os mensagens para a chamada da API
            api_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Gera a resposta
            assistant_response = self.chat_completion(api_messages)
            
            # Adiciona a nova conversa à memória
            api_messages.append({"role": "assistant", "content": assistant_response})
            self.add_memory(api_messages, user_id)
            
            # Retorna um dicionário com a resposta e as memórias utilizadas
            return {
                "response": assistant_response,
                "memories_used": memories
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return {
                "response": f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}",
                "memories_used": []
            }


# Singleton para uso em toda a aplicação
def get_memory_manager(collection_prefix: str = "voxy") -> MemoryManager:
    """
    Retorna uma instância da classe MemoryManager
    
    Args:
        collection_prefix: Prefixo para as coleções de memórias
        
    Returns:
        MemoryManager: Instância única da classe MemoryManager
    """
    if not hasattr(get_memory_manager, "instance"):
        get_memory_manager.instance = MemoryManager(collection_prefix)
    return get_memory_manager.instance 
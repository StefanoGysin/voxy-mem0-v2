"""
Módulo para gerenciamento de memória vetorial usando a biblioteca Mem0.
Responsável pela recuperação e armazenamento de memórias no Supabase.
"""

import os
import logging
from dotenv import load_dotenv
from mem0 import Memory
from openai import OpenAI
from typing import Dict, List, Optional, Any, Union, Tuple
import time
import uuid
from datetime import datetime
import sys
import hashlib
import tqdm
import builtins

# Adiciona o diretório raiz ao path do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Importa o utilitário de autenticação
from utils.auth import get_user_system_prompt
from utils.cache import MemoryCache, cached
from utils.performance import performance_monitor, measure

# Configuração de logging
logger = logging.getLogger("voxy-memory")

# Carrega variáveis de ambiente
load_dotenv()

# Carrega configurações de desempenho das variáveis de ambiente
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_SIZE = int(os.getenv("CACHE_SIZE", "200"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
PERFORMANCE_MONITORING = os.getenv("PERFORMANCE_MONITORING", "true").lower() == "true"
PERFORMANCE_SLOW_THRESHOLD = int(os.getenv("PERFORMANCE_SLOW_OPERATION_THRESHOLD", "500"))
MODEL_CHOICE = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
MEM0_COLLECTION_NAME = os.getenv("MEM0_COLLECTION_NAME", "voxy_memories")
MEM0_MAX_RESULTS = int(os.getenv("MEM0_MAX_RESULTS", "5"))

class ProgressManager:
    """
    Gerencia a exibição de barras de progresso e oculta saídas extensas.
    """
    def __init__(self):
        self.original_print = builtins.print
        self.is_capturing = False
        self.progress_bar = None
        
    def start_capture(self, desc="Processando", total=100):
        """Inicia a captura de saídas e exibe uma barra de progresso"""
        if self.is_capturing:
            return
            
        self.is_capturing = True
        builtins.print = self._custom_print
        self.progress_bar = tqdm.tqdm(total=total, desc=desc, bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}")
        
    def update_progress(self, amount=1):
        """Atualiza a barra de progresso"""
        if self.progress_bar:
            self.progress_bar.update(amount)
            
    def stop_capture(self):
        """Finaliza a captura e restaura a função print original"""
        if not self.is_capturing:
            return
            
        self.is_capturing = False
        builtins.print = self.original_print
        
        if self.progress_bar:
            self.progress_bar.close()
            self.progress_bar = None
    
    def _custom_print(self, *args, **kwargs):
        """Função print personalizada que captura saídas"""
        # Não faz nada, apenas suprime a saída
        pass

# Instância global do gerenciador de progresso
progress_manager = ProgressManager()

class MemoryManager:
    """
    Gerencia a memória vetorial para o assistente Voxy.
    Integra com a biblioteca Mem0 e OpenAI para armazenamento e recuperação de memórias.
    
    Esta classe é responsável por:
    - Recuperar memórias relevantes para consultas do usuário
    - Armazenar novas memórias após interações
    - Gerenciar o cache de memórias para otimizar desempenho
    - Processar mensagens e gerar respostas com contexto
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
        
        # Configura monitoramento de desempenho
        if PERFORMANCE_MONITORING:
            performance_monitor.enable()
            performance_monitor.set_threshold("retrieve_memories", PERFORMANCE_SLOW_THRESHOLD)
            performance_monitor.set_threshold("process_message", PERFORMANCE_SLOW_THRESHOLD * 2)
        else:
            performance_monitor.disable()
        
        # Inicializa o cache de memórias
        cache_size = 0 if not CACHE_ENABLED else CACHE_SIZE
        self.memories_cache = MemoryCache[str, List[Dict]](max_size=cache_size, ttl=CACHE_TTL)
        logger.info(f"Cache de memórias inicializado com tamanho {cache_size} e TTL {CACHE_TTL}s")
        
        # Inicializa os clientes
        self._setup_memory()
    
    def _generate_cache_key(self, user_id: str, query: str) -> str:
        """
        Gera uma chave de cache única baseada no usuário e na consulta
        
        Args:
            user_id: ID do usuário
            query: Consulta realizada
            
        Returns:
            str: Chave única para o cache
        """
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"{user_id}:{query_hash}"
    
    def _invalidate_user_cache(self, user_id: str) -> None:
        """
        Invalida todas as entradas de cache de um usuário específico
        
        Args:
            user_id: ID do usuário
        """
        with self.memories_cache._lock:
            keys_to_remove = [k for k in self.memories_cache._cache.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                self.memories_cache.invalidate(key)
            logger.debug(f"Invalidadas {len(keys_to_remove)} entradas de cache para o usuário {user_id}")
            
    def _setup_memory(self):
        """
        Configura e inicializa a camada de memória usando Mem0 e OpenAI
        """
        try:
            logger.info("Inicializando configuração da memória")
            
            # Inicializa cliente OpenAI
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                raise ValueError("OPENAI_API_KEY não definida")
            
            # Inicializa o cliente OpenAI
            self.openai_client = OpenAI(api_key=openai_key)
            
            # Configura conexão com banco de dados
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                database_url = os.getenv("SUPABASE_URL")
                if not database_url:
                    raise ValueError("DATABASE_URL ou SUPABASE_URL não definida")
            
            # Tentativa de inicializar a biblioteca Mem0 com diferentes versões da API
            collection_name = f"{self.collection_prefix}_memories"
            
            # Método 1: Configuração via dicionário para versões mais recentes
            try:
                config = {
                    "llm": {
                        "provider": "openai",
                        "config": {
                            "model": MODEL_CHOICE,
                            "api_key": openai_key
                        }
                    },
                    "vector_store": {
                        "provider": "supabase",
                        "config": {
                            "connection_string": database_url,
                            "collection_name": collection_name,
                            "embedding_model_dims": 1536  # Dimensão dos embeddings padrão
                        }
                    }
                }
                
                # Tenta inicializar usando o método from_config
                self.memory = Memory.from_config(config)
                logger.info("Memória inicializada com sucesso usando from_config")
            except (AttributeError, TypeError) as e:
                logger.warning(f"Não foi possível inicializar usando from_config: {str(e)}")
                
                # Método 2: Inicialização direta para versões anteriores
                try:
                    self.memory = Memory(
                        openai_api_key=openai_key,
                        model=MODEL_CHOICE,
                        supabase_url=database_url,
                        collection_name=collection_name
                    )
                    logger.info("Memória inicializada com sucesso usando construtor direto")
                except Exception as e2:
                    logger.error(f"Falha na inicialização direta: {str(e2)}")
                    raise ValueError(f"Não foi possível inicializar a memória: {str(e2)}")
            
            logger.info("Configuração da memória concluída com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao configurar memória: {str(e)}")
            
            # Se for erro de conexão com o Supabase, fornece mensagem específica
            if "connection" in str(e).lower():
                raise ValueError("Erro de conexão com o Supabase")
            
            raise

    @measure("retrieve_memories")
    def retrieve_memories(self, user_id: str, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Recupera memórias relevantes para uma consulta
        
        Args:
            user_id: ID do usuário para filtrar memórias
            query: Consulta para buscar memórias relevantes
            limit: Número máximo de memórias a serem recuperadas
            
        Returns:
            List[Dict[str, Any]]: Lista de memórias relevantes
        """
        try:
            # Define limite padrão se não especificado
            if limit is None:
                limit = MEM0_MAX_RESULTS
                
            logger.info(f"Recuperando memórias para o usuário {user_id} com a consulta: {query}")
            
            # Verifica no cache primeiro
            cache_key = self._generate_cache_key(user_id, query)
            cached_memories = self.memories_cache.get(cache_key)
            
            if cached_memories is not None:
                logger.info(f"Cache hit: Recuperadas {len(cached_memories)} memórias do cache")
                return cached_memories
            
            # Não encontrou no cache, busca no banco de dados
            logger.info("Cache miss: Buscando memórias no banco de dados")
            
            # Marca o tempo de início para timeout
            start_time = time.time()
            
            # Inicia captura de saída para evitar impressão de vetores extensos
            progress_manager.start_capture(desc="Buscando memórias", total=1)
            
            try:
                # Usando o método search conforme a API atual do mem0ai
                # A API mudou e não aceita mais o parâmetro 'filter'
                search_results = self.memory.search(
                    query=query, 
                    user_id=user_id,  # Passando user_id diretamente como antes
                    limit=limit
                )
            finally:
                # Finaliza captura de saída
                progress_manager.update_progress(1)
                progress_manager.stop_capture()
            
            # Verifica se os resultados estão em formato de lista ou dicionário
            if isinstance(search_results, dict) and "results" in search_results:
                memories = search_results.get("results", [])
            else:
                # Versões mais recentes podem retornar diretamente uma lista
                memories = search_results if isinstance(search_results, list) else []
                
            # Exibe informações sobre memórias recuperadas para debugging
            if memories and len(memories) > 0:
                for mem in memories:
                    # Adapta para acessar o conteúdo com a chave correta, pode ser 'content' ou 'memory'
                    content = mem.get('content', mem.get('memory', ''))
                    logger.debug(f"Memória recuperada: {content[:100]}...")
            
            # Armazena resultados no cache para futuras consultas
            self.memories_cache.set(cache_key, memories)
            
            # Registra métricas de tempo
            elapsed = time.time() - start_time
            logger.info(f"Recuperadas {len(memories)} memórias relevantes em {elapsed:.2f}s")
            
            return memories
        except Exception as e:
            logger.error(f"Erro ao recuperar memórias: {str(e)}")
            return []
    
    @measure("add_memory")
    def add_memory(self, messages: list, user_id: str) -> bool:
        """
        Adiciona uma nova memória para o usuário
        
        Args:
            messages: Lista de mensagens no formato {"role": "user"/"assistant", "content": "texto"}
            user_id: ID do usuário para armazenar a memória
            
        Returns:
            bool: True se a memória foi adicionada com sucesso
        """
        try:
            logger.info(f"Adicionando memória para o usuário {user_id}")
            
            # Verifica se a lista de mensagens não está vazia
            if not messages or len(messages) == 0:
                logger.warning("Lista de mensagens vazia. Nada para adicionar à memória.")
                return True
            
            # Estrutura a conversa para armazenamento
            conversation_text = ""
            
            # Extrai mensagens para texto
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "system":
                    continue  # Ignora mensagens do sistema
                    
                if role == "user":
                    conversation_text += f"Usuário: {content}\n"
                elif role == "assistant":
                    conversation_text += f"Assistente: {content}\n"
            
            # Se não houver texto de conversa, não armazena
            if not conversation_text.strip():
                logger.warning("Texto de conversa vazio após processamento. Nada para adicionar.")
                return True
            
            # Adiciona a conversa à memória
            try:
                # Inicia captura de saída para evitar impressão de vetores extensos
                progress_manager.start_capture(desc="Adicionando memória", total=1)
                
                try:
                    # Nova implementação que passa o texto como primeiro argumento posicional
                    # e mantém apenas o user_id como parâmetro nomeado
                    self.memory.add(conversation_text, user_id=user_id)
                finally:
                    # Finaliza captura de saída
                    progress_manager.update_progress(1)
                    progress_manager.stop_capture()
                
                logger.info(f"Memória adicionada com sucesso para o usuário {user_id}")
                
                # Invalidar cache do usuário após adicionar nova memória
                self._invalidate_user_cache(user_id)
                
                return True
            except Exception as e:
                logger.error(f"Erro ao adicionar memória: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao processar memória para armazenamento: {str(e)}")
            return False

    @measure("clear_memories")
    def clear_memories(self, user_id: str) -> bool:
        """
        Limpa todas as memórias de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            bool: True se as memórias foram limpas com sucesso
        """
        try:
            logger.info(f"Limpando memórias do usuário {user_id}")
            
            # Limpa memórias no banco de dados
            self.memory.clear(user_id=user_id)
            
            # Limpa também o cache relacionado a este usuário
            self._invalidate_user_cache(user_id)
            
            logger.info(f"Memórias do usuário {user_id} limpas com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar memórias: {str(e)}")
            return False

    @measure("chat_completion")
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """
        Solicita uma resposta do modelo de linguagem
        
        Args:
            messages: Lista de mensagens para enviar ao modelo
            model: Modelo a ser usado (opcional)
            
        Returns:
            str: Resposta do modelo
        """
        try:
            # Se não foi especificado um modelo, usa o padrão das variáveis de ambiente
            if not model:
                model = MODEL_CHOICE
                
            # Solicita resposta do modelo
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages
            )
            
            # Retorna o conteúdo da resposta
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao obter resposta do modelo: {str(e)}")
            return f"Desculpe, não foi possível gerar uma resposta no momento. Erro: {str(e)}"

    @measure("process_message")
    def process_message(self, message_list: list, user_id: str) -> Dict[str, Any]:
        """
        Processa uma mensagem do usuário e gera uma resposta com contexto de memórias
        
        Args:
            message_list: Lista de mensagens em formato OpenAI
            user_id: ID do usuário para recuperar memórias relevantes
            
        Returns:
            Dict: Resposta do sistema contendo o texto e memórias utilizadas
        """
        start_time = time.time()
        
        try:
            # Extrai a última mensagem do usuário
            user_message = ""
            for msg in reversed(message_list):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
                    
            if not user_message:
                return {"response": "Não foi possível processar a mensagem.", "memories_used": []}
                
            # Recupera memórias relevantes
            relevant_memories = []
            
            try:
                # Inicia captura de saída para evitar impressão de vetores extensos
                progress_manager.start_capture(desc="Processando mensagem", total=2)
                
                # Etapa 1: Recuperar memórias
                try:
                    relevant_memories = self.retrieve_memories(user_id, user_message)
                    progress_manager.update_progress(1)
                except Exception as e:
                    logger.error(f"Erro ao recuperar memórias: {str(e)}")
                    
                # Etapa 2: Gerar completions
                try:
                    # Obtém o prompt do sistema personalizado do usuário
                    system_prompt = get_user_system_prompt(user_id)
                    
                    # Cria o contexto para o assistente
                    messages = []
                    
                    # Adiciona o prompt do sistema
                    messages.append({"role": "system", "content": system_prompt})
                    
                    # Adiciona contexto de memórias, se houver
                    if relevant_memories and len(relevant_memories) > 0:
                        memory_text = "Estas são informações relevantes sobre o usuário que você deve utilizar em sua resposta:\n\n"
                        
                        for i, memory in enumerate(relevant_memories):
                            # Extrai o conteúdo da memória (pode estar em diferentes campos)
                            if isinstance(memory, tuple) and len(memory) >= 3:
                                # Formato (id, score, data)
                                memory_data = memory[2]
                                if isinstance(memory_data, dict) and "data" in memory_data:
                                    memory_content = memory_data["data"]
                                else:
                                    memory_content = str(memory[2])
                            elif isinstance(memory, dict):
                                # Formato de dicionário
                                memory_content = memory.get("data", memory.get("content", memory.get("memory", str(memory))))
                            else:
                                # Outro formato
                                memory_content = str(memory)
                                
                            memory_text += f"{i+1}. {memory_content}\n"
                            
                        messages.append({"role": "system", "content": memory_text})
                    
                    # Adiciona o histórico de mensagens
                    for msg in message_list:
                        messages.append(msg)
                    
                    # Gera a resposta
                    response = self.chat_completion(messages)
                    progress_manager.update_progress(1)
                except Exception as e:
                    logger.error(f"Erro ao processar chat completion: {str(e)}")
                    response = "Desculpe, não foi possível gerar uma resposta."
                    
            finally:
                # Garante que a captura seja finalizada
                progress_manager.stop_capture()
            
            # Adiciona a mensagem e resposta à memória
            api_messages = message_list.copy()
            api_messages.append({"role": "assistant", "content": response})
            self.add_memory(api_messages, user_id)
            
            elapsed = time.time() - start_time
            logger.info(f"Mensagem processada em {elapsed:.2f}s")
            
            return {
                "response": response,
                "memories_used": relevant_memories
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            return {"response": "Ocorreu um erro ao processar sua mensagem.", "memories_used": []}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache de memórias
        
        Returns:
            Dict: Estatísticas do cache
        """
        return self.memories_cache.get_stats()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de desempenho das operações
        
        Returns:
            Dict: Estatísticas de desempenho
        """
        return performance_monitor.get_stats()

def get_memory_manager(collection_prefix: str = "voxy") -> MemoryManager:
    """
    Função de fábrica para criar e retornar uma instância do MemoryManager
    
    Args:
        collection_prefix: Prefixo para as coleções de memórias
        
    Returns:
        MemoryManager: Instância do gerenciador de memórias
    """
    return MemoryManager(collection_prefix) 
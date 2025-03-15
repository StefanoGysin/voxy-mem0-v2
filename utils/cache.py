"""
Módulo de cache para otimização de desempenho.

Este módulo implementa um sistema de cache LRU (Least Recently Used) 
para melhorar o desempenho de operações repetitivas ou custosas.
"""

import time
import logging
import threading
from collections import OrderedDict
from typing import Any, Dict, Optional, TypeVar, Generic, Callable, Tuple

K = TypeVar('K')  # Tipo para chaves
V = TypeVar('V')  # Tipo para valores

logger = logging.getLogger('voxy-cache')

class MemoryCache(Generic[K, V]):
    """
    Implementação de cache LRU (Least Recently Used) com expiração por tempo.
    
    Esta classe fornece um mecanismo de cache que:
    - Limita o número de itens armazenados (expira os menos usados recentemente)
    - Expira itens baseado em tempo (TTL - Time To Live)
    - Thread-safe para uso em ambientes multithreaded
    
    Atributos:
        max_size (int): Tamanho máximo do cache
        ttl (int): Tempo de vida dos itens em segundos
        _cache (OrderedDict): Estrutura para armazenar os dados do cache
        _expirations (Dict): Dicionário de timestamps de expiração
        _lock (threading.RLock): Lock para sincronização de threads
        _hits (int): Contador de acertos do cache
        _misses (int): Contador de erros do cache
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        """
        Inicializa o cache com tamanho máximo e TTL especificados.
        
        Args:
            max_size: Tamanho máximo do cache (padrão: 100)
            ttl: Tempo de vida em segundos (padrão: 300s = 5min)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[K, V] = OrderedDict()
        self._expirations: Dict[K, float] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        
        logger.info(f"Cache inicializado com tamanho máximo {max_size} e TTL {ttl}s")
    
    def get(self, key: K) -> Optional[V]:
        """
        Recupera um item do cache se existir e não estiver expirado.
        
        Args:
            key: A chave do item a ser recuperado
            
        Returns:
            O valor associado à chave ou None se não existir ou estiver expirado
        """
        with self._lock:
            self._cleanup_expired()
            
            if key not in self._cache:
                self._misses += 1
                return None
            
            # Move o item para o final (mais recentemente usado)
            value = self._cache.pop(key)
            self._cache[key] = value
            self._hits += 1
            return value
    
    def set(self, key: K, value: V) -> None:
        """
        Adiciona ou atualiza um item no cache.
        
        Args:
            key: A chave para o item
            value: O valor a ser armazenado
        """
        with self._lock:
            # Se já existe, remova primeiro
            if key in self._cache:
                self._cache.pop(key)
            
            # Adiciona o novo item e atualiza expiração
            self._cache[key] = value
            self._expirations[key] = time.time() + self.ttl
            
            # Remove itens mais antigos se exceder o tamanho máximo
            if self.max_size > 0 and len(self._cache) > self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                self._expirations.pop(oldest_key, None)
    
    def invalidate(self, key: K) -> None:
        """
        Remove um item específico do cache.
        
        Args:
            key: A chave do item a ser removido
        """
        with self._lock:
            if key in self._cache:
                self._cache.pop(key)
                self._expirations.pop(key, None)
    
    def clear(self) -> None:
        """Limpa todo o conteúdo do cache."""
        with self._lock:
            self._cache.clear()
            self._expirations.clear()
    
    def _cleanup_expired(self) -> None:
        """Remove itens expirados do cache."""
        now = time.time()
        expired_keys = [
            k for k, exp_time in self._expirations.items() 
            if exp_time <= now
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._expirations.pop(key, None)
    
    @property
    def size(self) -> int:
        """Retorna o número de itens no cache."""
        with self._lock:
            return len(self._cache)
    
    @property
    def hit_rate(self) -> float:
        """
        Calcula a taxa de acerto do cache.
        
        Returns:
            Taxa de acerto entre 0.0 e 1.0, ou 0.0 se não houver acessos
        """
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return self._hits / total
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de uso do cache.
        
        Returns:
            Dicionário com estatísticas: tamanho, acertos, erros e taxa de acerto
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self.hit_rate
            }

def cached(cache: MemoryCache, key_fn: Callable[..., K] = None) -> Callable:
    """
    Decorador para armazenar em cache os resultados de funções.
    
    Args:
        cache: Instância de MemoryCache para armazenar os resultados
        key_fn: Função opcional para gerar chaves de cache personalizadas
        
    Returns:
        Decorador que aplica o cache à função decorada
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            # Gera uma chave baseada nos argumentos e na função
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                # Chave padrão: nome da função + representação de string dos argumentos
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = ':'.join(key_parts)
            
            # Tenta obter do cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Executa a função e armazena o resultado no cache
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        return wrapper
    
    return decorator 
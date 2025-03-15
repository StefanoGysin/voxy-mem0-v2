"""
Módulo para monitoramento de desempenho e rastreamento de operações lentas.

Este módulo fornece ferramentas para medir, monitorar e registrar o desempenho
de operações críticas no aplicativo, facilitando a identificação de gargalos.
"""

import time
import logging
import functools
import statistics
from typing import Dict, List, Callable, Any, Optional, Union, TypeVar, cast
from collections import defaultdict

# Configuração de logging
logger = logging.getLogger("voxy-performance")

F = TypeVar('F', bound=Callable[..., Any])

class PerformanceMonitor:
    """
    Monitor de performance para rastreamento de tempos de execução de funções.
    
    Esta classe mantém estatísticas sobre o tempo de execução de várias 
    operações no sistema, permitindo identificar gargalos e tendências.
    
    Atributos:
        _metrics (Dict): Dicionário com métricas de desempenho por função
        _thresholds (Dict): Limites de tempo para alertas por operação
        _enabled (bool): Indica se o monitoramento está ativo
    """
    
    def __init__(self, enabled: bool = True, default_threshold_ms: int = 500):
        """
        Inicializa o monitor de performance.
        
        Args:
            enabled: Se o monitoramento está ativo (padrão: True)
            default_threshold_ms: Limite padrão para alertas em ms (padrão: 500ms)
        """
        self._metrics: Dict[str, Dict[str, Union[int, List[float]]]] = defaultdict(
            lambda: {"count": 0, "total_time": 0.0, "times": []}
        )
        self._thresholds: Dict[str, float] = defaultdict(lambda: default_threshold_ms / 1000.0)
        self._enabled = enabled
        
    def enable(self) -> None:
        """Ativa o monitoramento de desempenho"""
        self._enabled = True
        
    def disable(self) -> None:
        """Desativa o monitoramento de desempenho"""
        self._enabled = False
        
    def is_enabled(self) -> bool:
        """Retorna se o monitoramento está ativo"""
        return self._enabled
    
    def set_threshold(self, operation: str, threshold_ms: int) -> None:
        """
        Define um limite personalizado para uma operação específica.
        
        Args:
            operation: Nome da operação
            threshold_ms: Limite em milissegundos
        """
        self._thresholds[operation] = threshold_ms / 1000.0
        
    def get_threshold(self, operation: str) -> float:
        """
        Obtém o limite definido para uma operação.
        
        Args:
            operation: Nome da operação
            
        Returns:
            Limite em segundos
        """
        return self._thresholds[operation]
    
    def record_time(self, operation: str, time_taken: float) -> None:
        """
        Registra o tempo de execução de uma operação.
        
        Args:
            operation: Nome da operação
            time_taken: Tempo de execução em segundos
        """
        if not self._enabled:
            return
            
        metrics = self._metrics[operation]
        metrics["count"] = cast(int, metrics["count"]) + 1
        metrics["total_time"] = cast(float, metrics["total_time"]) + time_taken
        
        # Armazena os últimos 100 tempos para análise estatística
        times = cast(List[float], metrics["times"])
        times.append(time_taken)
        if len(times) > 100:
            times.pop(0)
            
        # Verifica se a operação excedeu o limite de tempo
        threshold = self._thresholds[operation]
        if time_taken > threshold:
            # Formatação melhorada para operações lentas
            time_ms = time_taken * 1000
            threshold_ms = threshold * 1000
            
            # Calcula a porcentagem acima do limite
            percentage = (time_ms / threshold_ms - 1) * 100
            
            # Escolhe o nível de log com base na gravidade
            log_level = logging.WARNING
            if percentage > 200:  # Mais de 3x o limite
                log_level = logging.ERROR
            
            # Informações estatísticas para contexto
            avg_time = self.get_average_time(operation)
            if avg_time:
                avg_ms = avg_time * 1000
                comparison = f" (média: {avg_ms:.2f}ms, {(time_ms/avg_ms):.1f}x a média)"
            else:
                comparison = ""
            
            try:
                # Log formatado para facilitar análise (corrigido "llevou" para "levou")
                logger.log(
                    log_level, 
                    f"Operação lenta: {operation} levou {time_ms:.2f}ms "
                    f"(limite: {threshold_ms:.2f}ms, +{percentage:.1f}%){comparison}"
                )
            except Exception as e:
                # Fallback para mensagem simples sem formatação especial em caso de erro
                logger.log(
                    log_level,
                    f"Operacao lenta: {operation} ({time_ms:.2f}ms, limite: {threshold_ms:.2f}ms)"
                )
    
    def get_metrics(self, operation: str) -> Dict[str, Union[int, float]]:
        """
        Obtém métricas de uma operação específica.
        
        Args:
            operation: Nome da operação
            
        Returns:
            Dicionário com métricas: contagem, tempo total e médio
        """
        if operation not in self._metrics:
            return {"count": 0, "total_time": 0.0, "avg_time": 0.0}
            
        metrics = self._metrics[operation]
        count = cast(int, metrics["count"])
        total_time = cast(float, metrics["total_time"])
        avg_time = total_time / count if count > 0 else 0.0
        
        return {
            "count": count,
            "total_time": total_time,
            "avg_time": avg_time
        }
    
    def get_average_time(self, operation: str) -> Optional[float]:
        """
        Obtém o tempo médio de execução para uma operação.
        
        Args:
            operation: Nome da operação
            
        Returns:
            Tempo médio em segundos ou None se não houver registros
        """
        if operation not in self._metrics:
            return None
            
        metrics = self._metrics[operation]
        count = cast(int, metrics["count"])
        
        if count == 0:
            return None
            
        return cast(float, metrics["total_time"]) / count
    
    def get_statistics(self, operation: str) -> Dict[str, Union[int, float]]:
        """
        Obtém estatísticas detalhadas de uma operação.
        
        Args:
            operation: Nome da operação
            
        Returns:
            Dicionário com estatísticas: contagem, média, mediana, mínimo, máximo, p90, p95, p99
        """
        if operation not in self._metrics:
            return {
                "count": 0,
                "avg": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
            
        metrics = self._metrics[operation]
        times = cast(List[float], metrics["times"])
        
        if not times:
            return {
                "count": 0,
                "avg": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
            
        count = len(times)
        avg = statistics.mean(times)
        median = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        
        # Calcular percentis
        sorted_times = sorted(times)
        p90_idx = int(count * 0.9)
        p95_idx = int(count * 0.95)
        p99_idx = int(count * 0.99)
        
        p90 = sorted_times[p90_idx - 1] if p90_idx > 0 else sorted_times[0]
        p95 = sorted_times[p95_idx - 1] if p95_idx > 0 else sorted_times[0]
        p99 = sorted_times[p99_idx - 1] if p99_idx > 0 else sorted_times[0]
        
        return {
            "count": count,
            "avg": avg,
            "median": median,
            "min": min_time,
            "max": max_time,
            "p90": p90,
            "p95": p95,
            "p99": p99
        }
    
    def log_statistics(self, operation: str) -> None:
        """
        Registra estatísticas de uma operação no log.
        
        Args:
            operation: Nome da operação
        """
        if not self._enabled or operation not in self._metrics:
            return
            
        stats = self.get_statistics(operation)
        if stats["count"] == 0:
            return
            
        # Converter para milissegundos para facilitar leitura
        avg_ms = stats["avg"] * 1000
        median_ms = stats["median"] * 1000
        min_ms = stats["min"] * 1000
        max_ms = stats["max"] * 1000
        p90_ms = stats["p90"] * 1000
        p95_ms = stats["p95"] * 1000
        p99_ms = stats["p99"] * 1000
        
        logger.info(
            f"📊 Estatísticas para '{operation}' ({stats['count']} execuções):\n"
            f"   • Média: {avg_ms:.2f}ms | Mediana: {median_ms:.2f}ms\n"
            f"   • Min: {min_ms:.2f}ms | Max: {max_ms:.2f}ms\n"
            f"   • p90: {p90_ms:.2f}ms | p95: {p95_ms:.2f}ms | p99: {p99_ms:.2f}ms"
        )
        
        # Verifica se a operação está consistentemente acima do limite
        threshold = self._thresholds[operation] * 1000  # em ms
        if median_ms > threshold:
            logger.warning(
                f"⚠️ A operação '{operation}' está consistentemente acima do limite "
                f"({median_ms:.2f}ms > {threshold:.2f}ms). Considere otimizá-la."
            )

# Instância única para uso no aplicativo
performance_monitor = PerformanceMonitor()

def measure(operation_name: str) -> Callable[[F], F]:
    """
    Decorador para medir o tempo de execução de uma função.
    
    Args:
        operation_name: Nome da operação para registro
        
    Returns:
        Função decorada que registra tempo de execução
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not performance_monitor.is_enabled():
                return func(*args, **kwargs)
                
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                end_time = time.time()
                performance_monitor.record_time(operation_name, end_time - start_time)
        return cast(F, wrapper)
    return decorator 
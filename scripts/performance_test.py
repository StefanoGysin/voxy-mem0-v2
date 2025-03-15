#!/usr/bin/env python3
"""
Script para testar o desempenho do sistema de memórias.

Este script executa testes comparativos de desempenho para avaliar a eficácia
das otimizações implementadas, especialmente o sistema de cache.
"""

import os
import time
import random
import logging
import argparse
import statistics
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("performance-test")

# Carrega variáveis de ambiente
load_dotenv()

# Configura usuário de teste
os.environ["TEST_MODE"] = "true"
TEST_USER_ID = "ba60795d-244a-4e0d-b0da-591dc0dd7a0b"

# Configura variáveis de ambiente para os testes
os.environ["CACHE_ENABLED"] = "true"
os.environ["CACHE_SIZE"] = "200"
os.environ["CACHE_TTL"] = "300"
os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

# Importa depois de configurar variáveis de ambiente
try:
    from utils.memory_manager import MemoryManager
    from utils.performance import performance_monitor
    from utils.cache import MemoryCache
except ImportError as e:
    logger.error(f"Erro ao importar módulos: {e}")
    print(f"Erro ao importar módulos necessários: {e}")
    print("Verifique se você está executando o script do diretório raiz do projeto.")
    import sys
    sys.exit(1)

def generate_test_queries(num_queries: int = 10, repeat_factor: int = 3) -> List[str]:
    """
    Gera consultas de teste, algumas repetidas para simular padrões reais.
    
    Args:
        num_queries: Número base de consultas únicas
        repeat_factor: Fator de repetição para simular queries comuns
        
    Returns:
        Lista de consultas para teste
    """
    base_queries = [
        "Quais são os benefícios da inteligência artificial?",
        "Como implementar um sistema de cache eficiente?",
        "Explique o que é embeddings em NLP.",
        "Como posso melhorar a performance de um banco de dados?",
        "Como funciona o algoritmo de PageRank?",
        "Qual a diferença entre machine learning e deep learning?",
        "Como otimizar consultas SQL?",
        "O que são transformers na IA?",
        "Quais os desafios da computação quântica?",
        "Quais são as melhores práticas em segurança de APIs?"
    ]
    
    # Seleciona um subconjunto das consultas base se necessário
    if num_queries < len(base_queries):
        base_queries = base_queries[:num_queries]
    elif num_queries > len(base_queries):
        # Adiciona mais consultas geradas aleatoriamente
        for i in range(len(base_queries), num_queries):
            base_queries.append(f"Consulta de teste {i}: Como melhorar {random.choice(['desempenho', 'segurança', 'usabilidade'])}?")
    
    # Cria lista de consultas com repetições
    queries = base_queries.copy()
    
    # Adiciona repetições de algumas consultas para simular uso real
    for _ in range(repeat_factor - 1):
        # Seleciona aleatoriamente algumas consultas para repetir
        repeat_count = max(1, len(base_queries) // 2)
        repeat_queries = random.sample(base_queries, repeat_count)
        queries.extend(repeat_queries)
    
    # Embaralha a lista para distribuir as repetições
    random.shuffle(queries)
    
    return queries

def run_test_with_cache(memory_manager: MemoryManager, queries: List[str], cache_size: int) -> Dict[str, Dict[str, float]]:
    """
    Executa testes de desempenho usando o cache.
    
    Args:
        memory_manager: Instância do gerenciador de memórias
        queries: Lista de consultas para teste
        cache_size: Tamanho do cache a ser utilizado
        
    Returns:
        Dicionário com tempos de execução para cada consulta
    """
    # Configura cache com tamanho especificado
    memory_manager.memories_cache = MemoryCache(max_size=cache_size, ttl=300)
    
    # Resultados por consulta
    results = {}
    
    # Executa cada consulta e mede o tempo
    for i, query in enumerate(queries):
        logger.info(f"Executando consulta {i+1}/{len(queries)}: {query[:30]}...")
        
        start_time = time.time()
        memory_manager.retrieve_memories(TEST_USER_ID, query)
        elapsed = time.time() - start_time
        
        # Armazena resultado
        short_query = query[:40] + "..." if len(query) > 40 else query
        results[short_query] = {"time": elapsed}
    
    # Recupera estatísticas do monitor de desempenho
    stats = performance_monitor.get_stats("retrieve_memories")
    
    return results

def compare_performance(
    memory_manager: MemoryManager, 
    queries: List[str], 
    cache_size: int = 200
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Compara o desempenho com e sem cache.
    
    Args:
        memory_manager: Instância do gerenciador de memórias
        queries: Lista de consultas para teste
        cache_size: Tamanho do cache a ser usado no teste com cache
        
    Returns:
        Tupla com resultados com cache e sem cache
    """
    # Limpa estatísticas anteriores
    performance_monitor.reset_stats()
    
    # Teste COM cache
    print("\nExecutando teste COM cache...")
    with_cache_results = run_test_with_cache(memory_manager, queries, cache_size)
    with_cache_stats = performance_monitor.get_stats()
    
    # Limpa estatísticas para o próximo teste
    performance_monitor.reset_stats()
    
    # Teste SEM cache
    print("\nExecutando teste SEM cache...")
    memory_manager.memories_cache = MemoryCache(max_size=0, ttl=300)  # Desativa cache
    without_cache_results = run_test_with_cache(memory_manager, queries, 0)
    without_cache_stats = performance_monitor.get_stats()
    
    return with_cache_results, without_cache_results

def generate_report(
    with_cache: Dict[str, Dict[str, float]], 
    without_cache: Dict[str, Dict[str, float]], 
    queries: List[str]
) -> None:
    """
    Gera um relatório comparativo de desempenho.
    
    Args:
        with_cache: Resultados com cache ativado
        without_cache: Resultados sem cache
        queries: Lista de consultas usadas no teste
    """
    # Calcula estatísticas gerais
    with_cache_times = [result["time"] for result in with_cache.values()]
    without_cache_times = [result["time"] for result in without_cache.values()]
    
    # Conta cache hits/misses
    cache_hits = sum(1 for q in queries if queries.count(q) > 1)
    cache_misses = len(queries) - cache_hits
    
    # Calcula métricas
    total_with_cache = sum(with_cache_times)
    total_without_cache = sum(without_cache_times)
    avg_with_cache = statistics.mean(with_cache_times) if with_cache_times else 0
    avg_without_cache = statistics.mean(without_cache_times) if without_cache_times else 0
    speedup = total_without_cache / total_with_cache if total_with_cache > 0 else 0
    time_saved_pct = (1 - total_with_cache / total_without_cache) * 100 if total_without_cache > 0 else 0
    
    # Imprime relatório
    print("\n" + "=" * 60)
    print(" " * 18 + "RELATÓRIO DE PERFORMANCE")
    print("=" * 60 + "\n")
    
    print("CONFIGURAÇÃO")
    print(f"Número de consultas            {len(queries)}")
    print(f"Cache hits                     {cache_hits}")
    print(f"Cache misses                   {cache_misses}")
    print(f"Taxa de acerto do cache        {cache_hits/len(queries)*100:.1f}%")
    print()
    
    print("MÉTRICAS DE TEMPO")
    print(f"Tempo total com cache          {total_with_cache:.2f}s")
    print(f"Tempo total sem cache          {total_without_cache:.2f}s")
    print(f"Tempo médio com cache          {avg_with_cache*1000:.2f}ms por consulta")
    print(f"Tempo médio sem cache          {avg_without_cache*1000:.2f}ms por consulta")
    print(f"Speedup                        {speedup:.2f}x mais rápido com cache")
    print(f"Tempo economizado              {time_saved_pct:.1f}%")
    print()
    
    # Mostra alguns exemplos de consultas específicas
    print("DETALHES DE ALGUMAS CONSULTAS:")
    for i, query in enumerate(list(with_cache.keys())[:5]):
        with_time = with_cache[query]["time"] * 1000  # Converte para ms
        without_time = without_cache.get(query, {"time": 0})["time"] * 1000
        print(f"{i+1}. {query}")
        print(f"   Com cache: {with_time:.2f}ms | Sem cache: {without_time:.2f}ms")
    
    print("\n" + "=" * 60)

def main():
    """Função principal que executa o teste de desempenho."""
    parser = argparse.ArgumentParser(description="Teste de desempenho do sistema de memórias")
    parser.add_argument("--num-queries", type=int, default=10, help="Número de consultas de base")
    parser.add_argument("--repeat-factor", type=int, default=2, help="Fator de repetição para simulação de cache hits")
    parser.add_argument("--cache-size", type=int, default=200, help="Tamanho do cache para teste")
    args = parser.parse_args()
    
    # Gera consultas de teste
    queries = generate_test_queries(args.num_queries, args.repeat_factor)
    print(f"Executando teste de desempenho com {len(queries)} consultas...")
    
    # Configura gerenciador de memórias
    memory_manager = MemoryManager()
    
    # Executa os testes
    with_cache_results, without_cache_results = compare_performance(
        memory_manager, 
        queries,
        args.cache_size
    )
    
    # Gera relatório
    generate_report(with_cache_results, without_cache_results, queries)
    
    # Mostra estatísticas detalhadas
    print("\nEstatísticas detalhadas de funções monitoradas:\n")
    stats = performance_monitor.get_stats()
    
    # Formata e imprime as estatísticas
    for func_name, metrics in stats.items():
        print(f"=== ESTATÍSTICAS DE DESEMPENHO ===\n")
        print(f"{func_name}:")
        print(f"  Execuções: {metrics.get('count', 0)}")
        print(f"  Tempo médio: {metrics.get('avg_time', 0)*1000:.2f}ms")
        print(f"  P95: {metrics.get('p95', 0)*1000:.2f}ms")
        print(f"  Min/Max: {metrics.get('min_time', 0)*1000:.2f}ms / {metrics.get('max_time', 0)*1000:.2f}ms")
        print()

if __name__ == "__main__":
    main() 
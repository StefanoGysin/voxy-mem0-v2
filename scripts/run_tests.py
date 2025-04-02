#!/usr/bin/env python3
"""
Script para execução de testes do Voxy
Este script facilita a execução dos testes com diferentes configurações.
"""

import sys
import argparse
import subprocess
import os
from pathlib import Path

# Adiciona o diretório raiz ao path para importações
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def parse_args():
    """Analisa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description='Executa testes do Voxy')
    
    parser.add_argument('--type', choices=['all', 'unit', 'gui', 'integration'],
                        default='all', help='Tipo de testes a executar')
    
    parser.add_argument('--coverage', action='store_true',
                        help='Gerar relatório de cobertura')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Saída detalhada')
    
    parser.add_argument('--file', type=str,
                        help='Arquivo específico de teste a executar')
    
    parser.add_argument('--test', type=str,
                        help='Teste específico a executar (ex: TestMemoryManager::test_init)')
    
    return parser.parse_args()

def run_tests(args):
    """Executa os testes com base nos argumentos fornecidos."""
    # Constrói o comando base
    cmd = ['pytest']
    
    # Adiciona verbosidade
    if args.verbose:
        cmd.append('-v')
    
    # Adiciona relatório de cobertura
    if args.coverage:
        cmd.extend(['--cov=utils', '--cov=ui', '--cov-report=term', '--cov-report=html'])
    
    # Adiciona filtros por tipo de teste
    if args.type == 'unit':
        cmd.extend(['-m', 'not gui and not integration'])
    elif args.type == 'gui':
        cmd.extend(['-m', 'gui'])
    elif args.type == 'integration':
        cmd.extend(['-m', 'integration'])
    
    # Adiciona arquivo específico se fornecido
    if args.file:
        if not args.file.startswith('tests/'):
            args.file = f'tests/{args.file}'
        cmd.append(args.file)
    
    # Adiciona teste específico se fornecido
    if args.test:
        if args.file:
            cmd[-1] = f'{cmd[-1]}::{args.test}'
        else:
            print("Erro: Para especificar um teste, você também deve especificar o arquivo.")
            return 1
    
    # Exibe o comando a ser executado
    print(f"Executando: {' '.join(cmd)}")
    
    # Executa o comando
    result = subprocess.run(cmd, cwd=project_root)
    
    return result.returncode

def main():
    """Função principal."""
    # Verifica se o diretório de testes existe
    if not os.path.isdir(os.path.join(project_root, 'tests')):
        print("Erro: Diretório de testes não encontrado.")
        return 1
    
    # Analisa argumentos
    args = parse_args()
    
    # Executa os testes
    return run_tests(args)

if __name__ == '__main__':
    sys.exit(main()) 
# PLANNING.md: Diretrizes e Arquitetura do Projeto Voxy

Este documento descreve a arquitetura, convenções e diretrizes de desenvolvimento para o projeto Voxy.

## 1. Visão Geral e Objetivos

- **Projeto**: Voxy - Assistente conversacional com memória vetorial e interface gráfica.
- **Objetivo Principal**: Criar um assistente inteligente e personalizável que utilize memória vetorial para conversas contextuais, com uma interface gráfica intuitiva e autenticação segura via Supabase.
- **Tecnologias Chave**: Python 3.12+, PyQt6, Mem0ai, OpenAI API, Supabase (Auth + Postgres/pgvector).

## 2. Arquitetura Geral

A aplicação segue uma arquitetura modular:

- **`main.py`**: Ponto de entrada da aplicação, inicialização da UI e lógica principal.
- **`ui/`**: Módulos relacionados à interface gráfica (PyQt6).
    - `login_window.py`: Janela de login/registro.
    - `main_window.py`: Janela principal do chat.
    - `widgets/`: Componentes reutilizáveis da UI.
- **`core/`** (Sugestão: Mover lógica principal para cá): Lógica central do assistente.
    - `assistant.py`: Interação com Mem0ai e OpenAI.
    - `memory_manager.py`: Gerenciamento da memória vetorial.
- **`auth/`**: Módulos relacionados à autenticação (Supabase).
    - `auth_client.py`: Cliente para interagir com Supabase Auth.
- **`db/`**: Módulos relacionados ao banco de dados (Supabase/pgvector).
    - `db_client.py`: Cliente Vecs para interagir com a memória vetorial.
    - `db_setup.py`: Script para configuração inicial do banco.
- **`utils/`**: Utilitários gerais.
    - `config.py`: Carregamento de configurações (.env).
    - `logger.py`: Configuração do logger.
    - `helpers.py`: Funções auxiliares diversas.
- **`tests/`**: Testes unitários (Pytest). A estrutura deve espelhar a estrutura principal.
- **`assets/`**: Arquivos estáticos (ícones, etc.).
- **`scripts/`**: Scripts auxiliares (build, deploy, etc.).
- **`docs/`**: Documentação adicional (diagramas, etc.).

## 3. Convenções de Código e Estilo

- **Linguagem**: Python 3.12+.
- **Estilo**: PEP8 rigoroso.
- **Formatação**: `black`.
- **Tipagem**: Uso obrigatório de Type Hints.
- **Docstrings**: Estilo Google para todas as funções e classes.
    ```python
    def example(param1: str) -> int:
        """
        Breve resumo da função.

        Args:
            param1 (str): Descrição do parâmetro.

        Returns:
            int: Descrição do valor de retorno.
        """
        # Lógica da função
    ```
- **Comentários**: Comentar código não óbvio, especialmente lógica complexa, explicando o "porquê" (`# Razão: ...`).
- **Nomenclatura**: `snake_case` para variáveis e funções, `PascalCase` para classes.
- **Importações**: Preferir importações relativas dentro dos pacotes (`from . import module`). Evitar `import *`.

## 4. Gerenciamento de Dependências

- **Arquivo**: `requirements.txt`.
- **Ambiente Virtual**: Uso obrigatório (`.venv`).

## 5. Validação de Dados

- **Biblioteca**: `pydantic` para validação de dados de entrada/saída onde aplicável (ex: configurações, respostas de API).

## 6. Testes

- **Framework**: `pytest`.
- **Localização**: Pasta `/tests`, espelhando a estrutura do projeto.
- **Cobertura Mínima**:
    - 1 teste de caso feliz.
    - 1 teste de caso de borda.
    - 1 teste de caso de falha para cada nova funcionalidade/módulo.
- **Manutenção**: Atualizar testes sempre que a lógica for modificada.

## 7. Limites e Restrições

- **Tamanho de Arquivo**: Nenhum arquivo deve exceder 500 linhas. Refatorar se necessário.
- **Bibliotecas**: Usar apenas pacotes Python conhecidos e verificados. Confirmar existência antes de usar.

## 8. Gerenciamento de Tarefas

- **Arquivo**: `TASK.md`. Usar para rastrear tarefas pendentes, concluídas e descobertas.

## 9. Documentação

- **`README.md`**: Documentação principal para usuários e configuração. Manter atualizado.
- **`PLANNING.md`**: Este arquivo. Guia de arquitetura e desenvolvimento.
- **`TASK.md`**: Rastreamento de tarefas.

## 10. Commits e Versionamento

- **Mensagens de Commit**: Seguir o padrão Conventional Commits (ex: `feat: adiciona login`, `fix: corrige bug na UI`, `docs: atualiza README`).
- **Branches**: Usar branches para novas funcionalidades (`feature/`) e correções (`fix/`). 
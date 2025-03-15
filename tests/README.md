# Testes Automatizados para o Voxy-Mem0-v2

Este diretório contém os testes automatizados para o assistente Voxy-Mem0-v2. Os testes foram criados usando pytest e pytest-qt para testar tanto os componentes de back-end quanto a interface gráfica.

## Estrutura dos Testes

- `conftest.py` - Configurações e fixtures compartilhadas para todos os testes
- `test_memory_manager.py` - Testes para o gerenciador de memória vetorial
- `test_auth.py` - Testes para o sistema de autenticação
- `test_db_setup.py` - Testes para a configuração do banco de dados
- `test_login_window.py` - Testes para a interface de login
- `test_chat_window.py` - Testes para a interface de chat

## Executando os Testes

### Pré-requisitos

Antes de executar os testes, certifique-se de que todas as dependências estão instaladas:

```bash
pip install -r requirements.txt
```

### Executando Todos os Testes

Para executar todos os testes com relatório de cobertura:

```bash
# No diretório raiz do projeto
pytest
```

### Usando o Script Auxiliar

O projeto inclui um script auxiliar para facilitar a execução dos testes:

```bash
# No diretório raiz do projeto
python scripts/run_tests.py --type unit
```

Opções disponíveis:
- `--type unit` - Executa apenas testes unitários
- `--type gui` - Executa apenas testes de interface gráfica
- `--type integration` - Executa apenas testes de integração
- `--type all` - Executa todos os testes
- `--coverage` - Gera relatório de cobertura
- `--verbose` ou `-v` - Mostra informações detalhadas
- `--file FILENAME` - Executa apenas um arquivo de teste específico

Exemplo:
```bash
python scripts/run_tests.py --type unit --file test_memory_manager.py
```

### Executando Testes Específicos

Para executar apenas um arquivo de teste:

```bash
pytest tests/test_memory_manager.py
```

Para executar um teste específico:

```bash
pytest tests/test_memory_manager.py::TestMemoryManager::test_init
```

### Categorias de Testes

Os testes estão organizados com marcadores para facilitar a execução seletiva:

- Testes de GUI (que podem ser lentos em ambientes CI):

```bash
pytest -m "gui"
```

- Testes de integração (que requerem serviços externos):

```bash
pytest -m "integration"
```

- Testes rápidos (excluindo testes lentos):

```bash
pytest -m "not slow"
```

## Estado Atual dos Testes

### Cobertura Atual

A cobertura atual dos testes é aproximadamente:
- `utils/auth.py`: 54% de cobertura
- `utils/db_setup.py`: 55% de cobertura
- `utils/memory_manager.py`: 49% de cobertura
- `ui/chat_window.py`: 73% de cobertura
- `ui/login_window.py`: 54% de cobertura
- **Total**: 59% de cobertura

### Testes Ignorados (Skipped)

Alguns testes estão marcados como ignorados por razões específicas:

1. `test_clear_memories` em `TestChatWindow` - A funcionalidade não está implementada na classe `ChatWindow` atual.
2. Testes de registro e formulários em `TestLoginWindow` - São testes complexos que requerem mocks adicionais.

## Relatórios de Cobertura

Após executar os testes, um relatório de cobertura será gerado nos formatos de terminal e HTML:

```bash
# Para visualizar o relatório HTML (Windows)
start htmlcov/index.html

# Para visualizar o relatório HTML (Linux/macOS)
open htmlcov/index.html
```

## Depuração dos Testes

Para executar os testes em modo de depuração com registros detalhados:

```bash
pytest --log-cli-level=DEBUG
```

## Testes com Mock vs. Testes de Integração

A maioria dos testes utiliza mocks para simular serviços externos como OpenAI e Supabase. Isso torna os testes mais rápidos e confiáveis. No entanto, testes de integração que se conectam a serviços reais são importantes para verificar a integração completa do sistema.

Para executar testes de integração, você precisará configurar as variáveis de ambiente adequadas ou criar um arquivo `.env.test` com credenciais válidas para os serviços externos. 

## Solução de Problemas Comuns com Testes

### Erros de Importação

Se você encontrar erros de importação nos testes, verifique se o caminho do projeto está corretamente configurado e se todas as dependências estão instaladas.

### Falhas nos Testes de GUI

Os testes de GUI podem falhar por várias razões:
- Tempo de espera insuficiente para renderização de componentes
- Configuração incorreta da resolução de tela
- Problemas com o Qt ou display virtual no ambiente de teste

Para testes de GUI, recomenda-se executar em um ambiente com interface gráfica. 
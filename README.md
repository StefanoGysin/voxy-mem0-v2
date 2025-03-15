# Voxy-Mem0-v2: Assistente com Memória Vetorial e Interface Gráfica

![Versão](https://img.shields.io/badge/versão-2.2.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5.0%2B-orange.svg)
![Licença](https://img.shields.io/badge/licença-MIT-yellow.svg)

## 📋 Visão Geral

Voxy-Mem0-v2 é uma evolução do assistente conversacional Voxy-Mem0, agora com uma moderna interface gráfica construída com PyQt6 e sistema de autenticação integrado. Desenvolvido com a biblioteca [Mem0ai](https://github.com/mem0ai/mem0) e integrado com a API da OpenAI e banco de dados Supabase, este assistente oferece uma experiência de conversação personalizada ao lembrar conversas anteriores, preferências e informações contextuais dos usuários.

## ✨ Funcionalidades

- **🧠 Memória Vetorial Persistente**: Armazena e recupera conversas anteriores usando embeddings
- **👁️ Visualização de Memórias**: Exibe as memórias utilizadas em cada resposta com indicadores de relevância
- **🗑️ Gerenciamento de Memórias**: Interface para limpar memórias armazenadas
- **💬 Prompts Personalizados**: Configure o prompt do sistema para personalizar o comportamento do assistente
- **👤 Sistema de Autenticação**: Login e registro de usuários integrado com Supabase
- **🔒 Armazenamento Seguro**: Dados armazenados de forma segura no Supabase com pgvector
- **💬 Interface Gráfica Moderna**: Interface de usuário intuitiva construída com PyQt6
- **📝 Logging Detalhado**: Sistema de registro para monitoramento e depuração

## 🛠️ Requisitos de Sistema

### Requisitos de Hardware
- **Processador**: 2 GHz dual-core ou superior
- **Memória RAM**: Mínimo 4 GB (8 GB recomendado)
- **Armazenamento**: 200 MB disponíveis para a aplicação e dependências
- **Conexão com Internet**: Obrigatória para comunicação com as APIs

### Requisitos de Software
- **Sistema Operacional**:
  - Windows 10/11
  - macOS 10.15 (Catalina) ou superior
  - Linux (Ubuntu 20.04+, Debian 11+, Fedora 34+)
- **Python**: Versão 3.9 ou superior
- **Contas de Serviço**:
  - Conta na [OpenAI](https://platform.openai.com) com chave de API
  - Projeto [Supabase](https://supabase.com) configurado

## 📦 Instalação e Configuração

### 1. Obtenção e Configuração das Credenciais

#### OpenAI API
1. Crie uma conta em [platform.openai.com](https://platform.openai.com) se ainda não tiver
2. Navegue até a seção "API keys" no painel
3. Clique em "Create new secret key"
4. Copie a chave gerada (você não poderá vê-la novamente depois)

#### Supabase
1. Crie uma conta em [supabase.com](https://supabase.com) se ainda não tiver
2. Crie um novo projeto ou use um existente
3. No painel do projeto, vá para "Settings" > "API"
4. Copie a "URL", "anon key" e "service_role key"
5. Ative a extensão pgvector:
   - Navegue até "Database" > "Extensions"
   - Ative a extensão "pgvector"

### 2. Clone o Repositório

```bash
git clone https://github.com/SeuUsuario/voxy-mem0-v2.git
cd voxy-mem0-v2
```

### 3. Configure o Ambiente Virtual

#### No Windows:
```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual (PowerShell)
.\.venv\Scripts\Activate.ps1

# Ou se estiver usando o CMD
# .\.venv\Scripts\activate.bat
```

#### No macOS/Linux:
```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate
```

### 4. Instale as Dependências

```bash
# Atualizar pip para a versão mais recente
python -m pip install --upgrade pip

# Instalar todas as dependências listadas no arquivo requirements.txt
pip install -r requirements.txt
```

Lista de dependências principais:
- **mem0ai**: Biblioteca para gerenciamento de memória vetorial (versão ≥ 0.1.65)
- **openai**: Cliente oficial da OpenAI para Python (versão ≥ 1.33.0)
- **PyQt6**: Framework para interface gráfica (versão ≥ 6.5.0)
- **supabase**: Cliente Supabase para Python (versão ≥ 2.0.0)
- **pgvector**: Extensão para armazenamento e busca vetorial (versão ≥ 0.3.0)
- **vecs**: Abstração para bancos de dados vetoriais (versão ≥ 0.3.1)

### 5. Configure as Variáveis de Ambiente

Copie o arquivo de exemplo para criar seu próprio arquivo de configuração:

```bash
# No Windows (PowerShell)
Copy-Item -Path .env.example -Destination .env

# No macOS/Linux
cp .env.example .env
```

Abra o arquivo `.env` em um editor de texto e preencha com suas credenciais:

```ini
# Configuração da OpenAI
OPENAI_API_KEY=sua_chave_api_aqui
MODEL_CHOICE=gpt-4o-mini

# Configuração do Supabase para armazenamento vetorial
DATABASE_URL=postgres://postgres:SuaSenha@db.xxxxx.supabase.co:5432/postgres?sslmode=require

# Configuração do Supabase para autenticação
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=sua_chave_anon_aqui
SUPABASE_SERVICE_KEY=sua_chave_service_aqui

# Configurações adicionais
ALLOW_ACCOUNT_CREATION=true  # Define se novos usuários podem se registrar
REQUIRE_EMAIL_CONFIRMATION=false  # Define se é necessário confirmar e-mail
LOG_LEVEL=INFO  # Nível de detalhamento dos logs (DEBUG, INFO, WARNING, ERROR)
GUI_THEME=dark  # Tema da interface (light, dark, system)
GUI_LANG=pt-br  # Idioma da interface (pt-br, en-us)
```

## 🚀 Executando o Aplicativo

### Verificando a Configuração

Antes de iniciar o aplicativo, você pode verificar se a configuração do banco de dados está correta:

```bash
# Verifica a conexão com o Supabase e configura as tabelas necessárias
python -c "from utils.db_setup import setup_database; print(setup_database())"
```

### Iniciando o Aplicativo

```bash
# Com o ambiente virtual ativado
python main.py
```

### Primeiro Uso

1. Na primeira execução, você verá a tela de login
2. Caso não tenha uma conta, clique em "Registrar" (se ALLOW_ACCOUNT_CREATION=true)
3. Após o login bem-sucedido, você será direcionado para a interface de chat
4. O aplicativo criará automaticamente as coleções necessárias para armazenar memórias

## 🔄 Processo de Atualização

Caso precise atualizar para uma nova versão do aplicativo:

```bash
# Navegue até o diretório do projeto
cd voxy-mem0-v2

# Atualize o repositório (se estiver usando git)
git pull

# Ative o ambiente virtual
# No Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Ou no macOS/Linux
source .venv/bin/activate

# Atualize as dependências
pip install -r requirements.txt --upgrade
```

## 📂 Estrutura do Projeto

A estrutura do projeto foi organizada seguindo as melhores práticas:

```
voxy-mem0-v2/
│
├── assets/              # Recursos estáticos (imagens, ícones)
├── logs/                # Arquivos de log gerados pela aplicação
├── tests/               # Testes automatizados
├── ui/                  # Componentes da interface gráfica
│   ├── __init__.py
│   ├── login_window.py  # Janela de login e registro
│   └── chat_window.py   # Janela principal de chat
│
├── utils/               # Utilitários e módulos auxiliares
│   ├── __init__.py
│   ├── auth.py          # Gerenciamento de autenticação com Supabase
│   ├── db_setup.py      # Configuração do banco de dados
│   └── memory_manager.py # Gerenciamento da memória vetorial
│
├── .env                 # Variáveis de ambiente (não incluído no repositório)
├── .env.example         # Exemplo de variáveis de ambiente
├── main.py              # Ponto de entrada da aplicação
├── README.md            # Documentação do projeto
└── requirements.txt     # Dependências do projeto
```

## 🔧 Configuração Avançada

### Personalizando a Memória Vetorial

O arquivo `utils/memory_manager.py` contém a implementação da memória vetorial. Os principais métodos são:

- `add_memory`: Adiciona uma nova memória para um usuário
- `retrieve_memories`: Recupera memórias relevantes para uma consulta
- `clear_memories`: Limpa todas as memórias de um usuário
- `process_message`: Processa uma mensagem do usuário e gera uma resposta

Para personalizar os parâmetros de embeddings ou ajustar a recuperação de memória, edite este arquivo.

### Personalizando o Prompt do Sistema

O Voxy-Mem0-v2 permite que cada usuário defina seu próprio prompt do sistema através da interface gráfica:

1. Clique no botão "Configurações" na barra de ferramentas
2. Edite o texto no diálogo de configuração do prompt do sistema
3. Clique em "Salvar" para persistir suas alterações

Os prompts personalizados são armazenados na tabela `user_prompts` no Supabase e são usados automaticamente em todas as conversas futuras. Isso permite personalizar completamente o comportamento, tom e instruções do assistente.

Se nenhum prompt personalizado for definido, o sistema utilizará um prompt padrão definido no código.

### Configurando a Autenticação

O arquivo `utils/auth.py` contém a implementação da autenticação com Supabase. Você pode personalizar:

- Política de senhas
- Método de autenticação (email/senha, OAuth, etc.)
- Permissões e níveis de acesso

### Configuração do Banco de Dados

O arquivo `utils/db_setup.py` configura automaticamente o banco de dados Supabase para uso com memória vetorial.

## 🔍 Solução de Problemas

### Erros Comuns

#### Erro ao Ativar o Ambiente Virtual
- **Windows**: Verifique se a execução de scripts está habilitada (`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)
- **Linux/macOS**: Verifique permissões dos scripts (`chmod +x .venv/bin/activate`)

#### Erro de Importação do Módulo `mem0ai`
- Certifique-se de ter instalado o pacote `mem0ai` (não `mem0`)
- Verifique a versão instalada com `pip show mem0ai`

#### Erro de Conexão com o Supabase
- Verifique se as credenciais no arquivo `.env` estão corretas
- Confirme se a extensão pgvector está ativada no seu projeto Supabase
- Verifique se o seu IP não está bloqueado por regras de firewall do Supabase

#### Erro ao Adicionar Memórias
- Verifique se o formato das mensagens está correto (lista de dicionários com campos 'role' e 'content')
- Confirme que o user_id está sendo passado corretamente
- Verifique os logs para identificar erros específicos da API

#### Interface Gráfica Não Carrega
- Verifique se o PyQt6 foi instalado corretamente
- Em alguns sistemas Linux, pode ser necessário instalar pacotes adicionais (`apt-get install libxcb-xinerama0`)

### Logs e Diagnóstico

Os logs da aplicação são armazenados no diretório `logs/`. Para problemas mais complexos:

1. Defina `LOG_LEVEL=DEBUG` no arquivo `.env`
2. Execute a aplicação
3. Analise os arquivos de log gerados

## 📋 Histórico de Versões

### v2.2.0 (Atual)
- Adição de prompts personalizados do sistema para cada usuário
- Diálogo de configurações para editar o prompt do sistema
- Persistência das configurações no banco de dados
- Melhorias na experiência de usuário com feedback visual
- Correções de bugs e aprimoramentos na interface

### v2.1.0
- Visualização de memórias utilizadas em cada resposta do assistente
- Indicadores de relevância (porcentagem) para cada memória exibida
- Botão para limpar todas as memórias do usuário
- Diálogo para visualizar todas as memórias utilizadas em uma resposta
- Melhoria na cobertura de testes para a interface de chat

### v2.0.0
- Interface gráfica com PyQt6
- Sistema de autenticação integrado com Supabase
- Suporte a biblioteca mem0ai atualizada
- Melhorias na arquitetura e tratamento de erros

### v1.0.0
- Interface de linha de comando
- Memória vetorial básica
- Identificação simples de usuários

## 📄 Licença

Este projeto é licenciado sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 🙏 Agradecimentos

- [Mem0.ai](https://github.com/mem0ai/mem0) pela biblioteca de memória vetorial
- [OpenAI](https://openai.com) pelos modelos de linguagem
- [Supabase](https://supabase.com) pelo banco de dados e autenticação
- [PyQt](https://riverbankcomputing.com/software/pyqt/) pela framework de UI

## 🧪 Testes Automatizados

O projeto inclui uma suíte completa de testes automatizados para garantir a qualidade e estabilidade do código. Os testes estão localizados no diretório `tests/` e utilizam o framework pytest.

### Executando os Testes

Para executar todos os testes:

```bash
# Com o ambiente virtual ativado
python -m pytest
```

Para executar o script auxiliar que facilita a seleção de testes específicos:

```bash
# No Windows (PowerShell)
python scripts/run_tests.py --type all --coverage --verbose

# No Linux/macOS
python scripts/run_tests.py --type all --coverage --verbose
```

### Tipos de Testes

Os testes estão organizados em categorias:

- **Testes Unitários**: Testes isolados para cada componente
  ```bash
  python scripts/run_tests.py --type unit
  ```

- **Testes de Interface**: Testes da interface gráfica usando pytest-qt
  ```bash
  python scripts/run_tests.py --type gui
  ```

- **Testes de Integração**: Testes que verificam a integração com serviços externos
  ```bash
  python scripts/run_tests.py --type integration
  ```

### Relatórios de Cobertura

Os testes geram relatórios de cobertura que ajudam a identificar partes do código que não estão sendo testadas:

```bash
python scripts/run_tests.py --coverage
```

Um relatório HTML será gerado no diretório `htmlcov/`. Abra o arquivo `index.html` para visualizar a cobertura detalhada.

### Estado Atual dos Testes

A cobertura atual dos testes é aproximadamente:
- `utils/auth.py`: 54% de cobertura
- `utils/db_setup.py`: 55% de cobertura
- `utils/memory_manager.py`: 49% de cobertura
- `ui/chat_window.py`: 77% de cobertura
- `ui/login_window.py`: 54% de cobertura
- **Total**: 61% de cobertura

Alguns testes estão marcados como ignorados por razões específicas:
1. Alguns testes de interface gráfica complexos que requerem mocks adicionais.

Para executar um teste específico:

```bash
# Executar um arquivo de teste específico
python scripts/run_tests.py --type unit --file test_memory_manager.py

# Ou diretamente com pytest
python -m pytest tests/test_memory_manager.py::TestMemoryManager::test_init
```

Para mais informações sobre os testes, consulte a documentação em `tests/README.md`.

## 🚀 Desenvolvimento Futuro

Este projeto está em constante evolução. Abaixo estão as funcionalidades e melhorias planejadas para as próximas versões.

### Próximas Funcionalidades Planejadas

#### Curto Prazo (próxima versão)
- **Exportação e Importação de Conversas**: Permitir que usuários exportem e importem históricos de conversas em formatos comuns (JSON, TXT, PDF)
- **Temas Adicionais**: Implementação de mais opções de temas além do escuro atual (claro, sistema, alto contraste)

#### ✅ Funcionalidades Recentemente Implementadas
- **Gerenciamento de Memórias na Interface**: Implementação de botão para limpar memórias diretamente na interface do chat
- **Visualização Avançada de Memórias**: Exibição das memórias utilizadas para gerar cada resposta, com indicadores precisos de relevância (porcentagem)
- **Diálogo de Todas as Memórias**: Opção para visualizar detalhadamente todas as memórias que influenciaram uma resposta específica

#### Médio Prazo
- **Agentes Personalizados**: Criar diferentes perfis de assistente com diferentes personalidades e áreas de conhecimento
- **Integração com Mais Modelos de IA**: Suporte a modelos alternativos como Claude, Llama, Gemini além da OpenAI
- **Sistema de Plugins**: Arquitetura para extensões que adicionam funcionalidades como pesquisa web, visualização de dados, etc.
- **Interface em Múltiplos Idiomas**: Suporte completo a mais idiomas além do português

#### Longo Prazo
- **Versão Web**: Desenvolvimento de uma versão acessível via navegador
- **Compartilhamento Seguro de Conhecimento**: Permitir compartilhar memórias específicas entre usuários autorizados
- **Processamento de Voz**: Integração com reconhecimento e síntese de voz para interação por áudio
- **Assistente Proativo**: Capacidade de iniciar conversas baseadas em padrões, lembretes ou eventos programados

### Melhorias Técnicas

- **Aumentar Cobertura de Testes**: Atingir pelo menos 80% de cobertura de código em todos os módulos
- **Otimização de Desempenho**: Melhorar a velocidade de recuperação de memórias para grandes conjuntos de dados
- **Refatoração de Classes**: Melhorar a organização e modularização, especialmente da classe ChatWindow
- **Suporte a Múltiplos Bancos de Dados**: Adicionar opções além do Supabase (PostgreSQL direto, MongoDB, etc.)
- **Melhoria na Segurança**: Implementação de criptografia de ponta a ponta para mensagens e memórias sensíveis

### Contribuições Bem-vindas

Estamos abertos a contribuições nas seguintes áreas:
- Implementação de novas funcionalidades alinhadas com o roadmap
- Melhorias na interface gráfica e experiência do usuário
- Otimizações de desempenho e segurança
- Testes e documentação adicionais

Se você tem interesse em contribuir, por favor verifique as issues abertas ou crie uma nova descrevendo sua proposta. 
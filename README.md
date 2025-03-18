# Voxy-Mem0-v3: Assistente com Memória Vetorial e Interface Gráfica

![Versão](https://img.shields.io/badge/versão-2.3.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12%2B-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.8.1%2B-orange.svg)
![Licença](https://img.shields.io/badge/licença-MIT-yellow.svg)

## 📋 Visão Geral

Voxy-Mem0-v3 é uma evolução avançada do assistente conversacional Voxy-Mem0, com interface gráfica moderna construída com PyQt6 e sistema de autenticação integrado com Supabase. Desenvolvido com a biblioteca [Mem0ai](https://github.com/mem0ai/mem0) e integrado com a API da OpenAI, este assistente oferece uma experiência de conversação personalizada ao armazenar e recuperar conversas anteriores em uma memória vetorial persistente.

## ✨ Funcionalidades

- **🧠 Memória Vetorial Persistente**: Armazena e recupera conversas anteriores usando embeddings
- **👁️ Visualização de Memórias**: Exibe as memórias utilizadas em cada resposta com indicadores de relevância
- **🗑️ Gerenciamento de Memórias**: Interface para limpar memórias armazenadas
- **💬 Prompts Personalizados**: Configure o prompt do sistema para personalizar o comportamento do assistente
- **👤 Sistema de Autenticação**: Login e registro de usuários integrado com Supabase
- **🔒 Armazenamento Seguro**: Dados armazenados de forma segura no Supabase com pgvector
- **💬 Interface Gráfica Moderna**: Interface de usuário intuitiva construída com PyQt6
- **📝 Logging Colorido**: Sistema de registro avançado com cores e formatação para fácil monitoramento
- **⚡ Otimizações de Desempenho**: Sistema de cache LRU e monitoramento para respostas mais rápidas
- **📊 Barras de Progresso**: Feedback visual no terminal durante operações demoradas
- **🔍 Métricas de Desempenho**: Estatísticas detalhadas sobre tempos de execução de operações críticas

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
- **Python**: Versão 3.12 ou superior (testado com Python 3.12.8)
- **Contas de Serviço**:
  - Conta na [OpenAI](https://platform.openai.com) com chave de API
  - Projeto [Supabase](https://supabase.com) configurado com extensão pgvector

## 📦 Instalação e Configuração

### 1. Obtenção e Configuração das Credenciais

#### OpenAI API
1. Crie uma conta em [platform.openai.com](https://platform.openai.com) se ainda não tiver
2. Navegue até "API keys" no painel e clique em "Create new secret key"
3. Dê um nome descritivo à sua chave (ex: "Voxy-Mem0")
4. Copie a chave gerada imediatamente (você não poderá vê-la novamente depois)

#### Supabase
1. Crie uma conta em [supabase.com](https://supabase.com) se ainda não tiver
2. Crie um novo projeto ou use um existente
3. No painel do projeto, vá para "Settings" > "API"
4. Copie a "URL", "anon key" e "service_role key"
5. Ative a extensão pgvector:
   - Navegue até "Database" > "Extensions"
   - Pesquise por "vector" e ative a extensão "pgvector"
   - Ou use o SQL Editor e execute: `CREATE EXTENSION IF NOT EXISTS vector;`

### 2. Clone o Repositório

```bash
git clone https://github.com/SeuUsuario/voxy-mem0-v3.git
cd voxy-mem0-v3
```

### 3. Configure o Ambiente Virtual

É essencial criar um ambiente virtual para isolar as dependências do projeto.

#### No Windows:
**PowerShell:**
```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
.\.venv\Scripts\Activate

# Se estiver usando PowerShell e receber erro de política de execução:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Prompt de Comando (CMD):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

#### No macOS:
```bash
# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate
```

#### No Linux:
```bash
# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate
```

### 4. Instale as Dependências

```bash
# Atualizar pip para a versão mais recente
python -m pip install --upgrade pip

# Instalar todas as dependências
pip install -r requirements.txt
```

#### Dependências Principais:
- **mem0ai** (≥ 0.1.65): Biblioteca para gerenciamento de memória vetorial
- **openai** (≥ 1.33.0): Cliente oficial da OpenAI para Python
- **PyQt6** (≥ 6.5.0): Framework para interface gráfica
- **supabase** (≥ 2.0.0): Cliente Supabase para Python
- **pgvector** (≥ 0.3.0): Extensão para armazenamento e busca vetorial
- **vecs** (≥ 0.3.1): Abstração para bancos de dados vetoriais

#### Dependências Específicas do Sistema Operacional:

**Windows:**
- Para sistemas Windows, todas as dependências são instaladas automaticamente com o comando acima.

**macOS:**
```bash
# Se ocorrer erro com PyQt6 no macOS, pode ser necessário instalar o Qt:
brew install qt
```

**Linux (Ubuntu/Debian):**
```bash
# Instalar dependências do sistema para o PyQt6
sudo apt update
sudo apt install python3-dev libxcb-xinerama0 libgl1-mesa-glx
```

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
OPENAI_MODEL=gpt-4o-mini         # Recomendado para melhor desempenho
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Configuração do Supabase para armazenamento vetorial
DATABASE_URL=postgres://postgres:SuaSenha@db.xxxxx.supabase.co:5432/postgres?sslmode=require

# Configuração do Supabase para autenticação
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=sua_chave_anon_aqui
SUPABASE_SERVICE_KEY=sua_chave_service_aqui

# Configurações adicionais
ALLOW_ACCOUNT_CREATION=true      # true: permite registro de novos usuários
REQUIRE_EMAIL_CONFIRMATION=false # false: não requer confirmação de email

# Configurações de log e interface
LOG_LEVEL=INFO                   # Opções: DEBUG, INFO, WARNING, ERROR
GUI_THEME=dark                   # Opções: light, dark, system
GUI_LANG=pt-br                   # Opções: pt-br, en-us

# Configurações de desempenho
CACHE_ENABLED=true
CACHE_SIZE=200
CACHE_TTL=300
PERFORMANCE_MONITORING=true
PERFORMANCE_SLOW_OPERATION_THRESHOLD=500
```

## 🚀 Executando o Aplicativo

### Verificando a Configuração

Antes de iniciar o aplicativo, verifique se a configuração do banco de dados está correta:

```bash
# Verifica a conexão com o Supabase e configura as tabelas necessárias
python -c "from utils.db_setup import setup_database; print(setup_database())"
```

Se tudo estiver configurado corretamente, você verá `True` como saída.

### Problemas Comuns na Configuração

1. **Erro de conexão com o Supabase**:
   - Verifique se a URL e as chaves estão corretas
   - Verifique se o endereço IP está liberado nas configurações do Supabase

2. **Erro com pgvector**:
   - Verifique se a extensão pgvector está instalada no projeto Supabase
   - Execute a SQL query para habilitar: `CREATE EXTENSION IF NOT EXISTS vector;`

3. **Erro de autenticação OpenAI**:
   - Verifique se a chave API está correta e não expirou
   - Verifique se há limite de créditos na sua conta OpenAI

### Iniciando o Aplicativo

Com o ambiente virtual ativado, execute:

```bash
python main.py
```

### Primeiro Uso

1. Na primeira execução, você verá a tela de login
2. Caso não tenha uma conta, clique em "Registrar" (se ALLOW_ACCOUNT_CREATION=true)
3. Após o login bem-sucedido, você será direcionado para a interface de chat
4. O aplicativo criará automaticamente as coleções necessárias para armazenar memórias

### Uso do Sistema

1. **Interface de Chat**: Digite suas mensagens na caixa de texto e pressione Enter ou clique no botão enviar
2. **Visualização de Memórias**: No painel lateral direito, você pode ver as memórias que o sistema utilizou
3. **Configurações**: Acesse as configurações através do botão de engrenagem no canto superior direito
4. **Limpar Memórias**: Use o botão "Limpar Memórias" para remover todo o histórico de conversas

## 🔄 Atualizações e Manutenção

Para atualizar o aplicativo para uma nova versão:

```bash
# Navegue até o diretório do projeto
cd voxy-mem0-v3

# Ative o ambiente virtual
# Windows (PowerShell):
.\.venv\Scripts\Activate
# macOS/Linux:
source .venv/bin/activate

# Atualize o repositório
git pull

# Atualize as dependências
pip install -r requirements.txt --upgrade
```

### Backup e Restauração de Dados

Suas memórias e configurações são armazenadas no Supabase. Para fazer backup:

1. Acesse o painel do Supabase
2. Vá para "Database" > "Backups"
3. Clique em "Create backup" para um backup manual

Para restaurar, use a mesma seção para aplicar um backup existente.

## 📂 Estrutura do Projeto

O projeto segue uma estrutura organizada para fácil manutenção:

```
voxy-mem0-v3/
│
├── assets/              # Recursos estáticos (imagens, ícones)
├── logs/                # Arquivos de log gerados pela aplicação
├── scripts/             # Scripts utilitários para testes e manutenção
├── tests/               # Testes automatizados
├── ui/                  # Componentes da interface gráfica
│   ├── __init__.py
│   ├── login_window.py  # Janela de login e registro
│   └── chat_window.py   # Janela principal de chat
│
├── utils/               # Utilitários e módulos auxiliares
│   ├── __init__.py
│   ├── auth.py          # Gerenciamento de autenticação com Supabase
│   ├── cache.py         # Sistema de cache LRU para otimização
│   ├── db_setup.py      # Configuração do banco de dados
│   ├── memory_manager.py # Gerenciamento da memória vetorial
│   └── performance.py   # Monitoramento de desempenho das funções críticas
│
├── .env                 # Variáveis de ambiente (não incluído no repositório)
├── .env.example         # Exemplo de variáveis de ambiente
├── main.py              # Ponto de entrada da aplicação
├── README.md            # Documentação do projeto
└── requirements.txt     # Dependências do projeto
```

## 🔧 Configuração Avançada

### Personalizando o Prompt do Sistema

Você pode personalizar o comportamento do assistente editando o prompt do sistema:

1. Faça login no aplicativo
2. Clique no ícone de configurações (⚙️)
3. Selecione "Configurar Prompt do Sistema"
4. Edite o prompt conforme necessário
5. Clique em "Salvar"

### Ajustando Parâmetros de Memória

Para ajustar como as memórias são recuperadas, edite as seguintes variáveis no arquivo `.env`:

```ini
# Configurações da memória vetorial
MEM0_COLLECTION_NAME=voxy_memories
MEM0_MAX_RESULTS=5             # Quantidade de memórias a recuperar
MEM0_DIMENSION=1536            # Dimensão dos vetores (depende do modelo)
MEM0_SIMILARITY_THRESHOLD=0.8  # Limiar para considerar memórias relevantes
```

### Configuração para Diferentes Modelos da OpenAI

O sistema funciona com diferentes modelos da OpenAI. Recomendamos:

- **GPT-4o-mini**: Melhor equilíbrio entre custo e qualidade (padrão recomendado)
- **GPT-3.5-turbo**: Opção econômica para uso intensivo
- **GPT-4-turbo**: Melhor qualidade para casos que exigem mais capacidade

Para alterar o modelo, edite a variável `OPENAI_MODEL` no arquivo `.env`.

## 📚 Solução de Problemas

### Problemas Comuns e Soluções

1. **Aplicativo não inicia**:
   - Verifique se o ambiente virtual está ativado
   - Verifique se todas as dependências estão instaladas
   - Verifique os logs em `logs/` para mais detalhes

2. **Erro de autenticação**:
   - Verifique se as credenciais do Supabase estão corretas
   - Verifique se o arquivo `.env` foi configurado corretamente

3. **Erros com a memória vetorial**:
   - Verifique se a extensão pgvector está ativa no Supabase
   - Execute o comando de verificação de configuração mencionado anteriormente

4. **Interface gráfica com problemas de exibição**:
   - Em ambientes Linux, instale as dependências necessárias para o Qt
   - Em macOS, verifique se o Qt foi instalado corretamente

### Obtendo Suporte

Se encontrar problemas não cobertos nesta documentação:

1. Verifique os logs em `logs/` para mensagens de erro detalhadas
2. Abra uma issue no repositório GitHub
3. Inclua as mensagens de erro e os passos para reproduzir o problema

## 🔐 Segurança e Privacidade

- Todas as senhas são armazenadas de forma segura (hash + salt) no Supabase
- As comunicações com OpenAI e Supabase são feitas via HTTPS
- Nenhum dado é compartilhado com terceiros além dos serviços necessários (OpenAI/Supabase)
- O sistema armazena histórico de conversas para personalizar respostas futuras

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

---

Desenvolvido com ❤️ pela equipe Voxy
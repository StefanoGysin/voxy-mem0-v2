"""
Configuração do banco de dados Supabase para o Voxy-Mem0-v2
"""
import os
import logging
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import vecs

# Configuração de logging
logger = logging.getLogger("voxy-db-setup")

# Carrega variáveis de ambiente
load_dotenv()

class DatabaseSetup:
    """
    Classe para configurar o banco de dados Supabase
    """
    def __init__(self):
        """
        Inicializa a configuração do banco de dados
        """
        # Obter as credenciais das variáveis de ambiente
        self.database_url = os.getenv('DATABASE_URL')
        
        if not self.database_url:
            logger.error("Variável de ambiente DATABASE_URL não definida")
            raise ValueError("Variável de ambiente DATABASE_URL não definida")
        
        # Cria conexão com o banco de dados
        self.conn = None
    
    def check_connection(self):
        """
        Verifica a conexão com o banco de dados
        
        Returns:
            bool: True se a conexão foi estabelecida com sucesso, False caso contrário
        """
        logger.info("Verificando conexão com o banco de dados Supabase...")
        
        try:
            # Tenta conectar ao banco de dados
            self.conn = psycopg2.connect(self.database_url)
            
            # Verifica se a conexão está ativa
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                
                if result and result[0] == 1:
                    logger.info("[OK] Conexão estabelecida com sucesso!")
                    return True
                else:
                    logger.error("Conexão estabelecida, mas teste de consulta falhou")
                    return False
                
        except psycopg2.Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao conectar ao banco de dados: {e}")
            return False
    
    def check_pgvector_extension(self):
        """
        Verifica se a extensão pgvector está instalada
        
        Returns:
            bool: True se a extensão está instalada, False caso contrário
        """
        try:
            with self.conn.cursor() as cur:
                # Verifica se a extensão pgvector está instalada
                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                result = cur.fetchone()
                
                if result and result[0] == 'vector':
                    logger.info("[OK] Extensão pgvector já está instalada.")
                    return True
                else:
                    logger.warning("Extensão pgvector não está instalada")
                    
                    # Tenta instalar a extensão pgvector
                    try:
                        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                        self.conn.commit()
                        logger.info("Extensão pgvector instalada com sucesso!")
                        return True
                    except psycopg2.Error as e:
                        logger.error(f"Erro ao instalar extensão pgvector: {e}")
                        return False
                
        except psycopg2.Error as e:
            logger.error(f"Erro ao verificar extensão pgvector: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao verificar extensão pgvector: {e}")
            return False
    
    def get_vector_collections(self):
        """
        Obtém as coleções de vetores existentes no banco de dados
        
        Returns:
            list: Lista de nomes das coleções de vetores
        """
        collections = []
        
        try:
            # Conecta usando o vecs
            db = vecs.create_client(self.database_url)
            
            # Obtém as coleções existentes
            collections_objs = db.list_collections()
            
            # Converte os objetos Collection para seus nomes (strings)
            collections = [collection.name for collection in collections_objs]
            
            if collections:
                logger.info(f"Coleções de vetores encontradas: {', '.join(collections)}")
            else:
                logger.info("Nenhuma coleção de vetores encontrada no banco de dados.")
            
            return collections
            
        except Exception as e:
            logger.error(f"Erro ao obter coleções de vetores: {e}")
            return []
    
    def setup_user_tables(self):
        """
        Configura as tabelas de usuários no banco de dados
        
        Returns:
            bool: True se as tabelas foram configuradas com sucesso, False caso contrário
        """
        try:
            with self.conn.cursor() as cur:
                # Primeiro, cria a função de trigger para atualizar updated_at
                # para garantir que ela exista antes de ser usada pelos triggers
                cur.execute("""
                    CREATE OR REPLACE FUNCTION trigger_set_timestamp()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """)
                
                # Verifica se a tabela de usuários já existe
                cur.execute("SELECT to_regclass('public.voxy_users')")
                table_exists = cur.fetchone()[0]
                
                if table_exists:
                    logger.info("[OK] Tabela de usuários (voxy_users) já existe.")
                else:
                    # Cria a tabela de usuários
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS voxy_users (
                            id UUID PRIMARY KEY,
                            email TEXT UNIQUE NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            last_login TIMESTAMPTZ,
                            settings JSONB
                        )
                    """)
                    
                    # Cria o trigger para atualizar updated_at na tabela voxy_users
                    cur.execute("""
                        CREATE TRIGGER set_timestamp
                        BEFORE UPDATE ON voxy_users
                        FOR EACH ROW
                        EXECUTE FUNCTION trigger_set_timestamp();
                    """)
                    
                    logger.info("Tabela de usuários (voxy_users) criada com sucesso!")
                
                # Verifica se a tabela de prompts do sistema já existe
                cur.execute("SELECT to_regclass('public.user_prompts')")
                prompts_table_exists = cur.fetchone()[0]
                
                if prompts_table_exists:
                    logger.info("[OK] Tabela de prompts personalizados (user_prompts) já existe.")
                else:
                    # Cria a tabela de prompts personalizados
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_prompts (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id UUID NOT NULL,
                            system_prompt TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            UNIQUE(user_id)
                        )
                    """)
                    
                    # Cria o trigger para atualizar updated_at na tabela user_prompts
                    cur.execute("""
                        CREATE TRIGGER set_timestamp
                        BEFORE UPDATE ON user_prompts
                        FOR EACH ROW
                        EXECUTE FUNCTION trigger_set_timestamp();
                    """)
                    
                    logger.info("Tabela de prompts personalizados (user_prompts) criada com sucesso!")
                
                # Commit das alterações
                self.conn.commit()
                
                return True
                
        except psycopg2.Error as e:
            logger.error(f"Erro ao configurar tabelas de usuários: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao configurar tabelas de usuários: {e}")
            self.conn.rollback()
            return False
    
    def setup_database(self):
        """
        Configura o banco de dados para uso com o Voxy-Mem0-v2
        
        Returns:
            bool: True se o banco de dados foi configurado com sucesso, False caso contrário
        """
        logger.info("Iniciando configuração do banco de dados...")
        
        # Verifica a conexão com o banco de dados
        if not self.check_connection():
            return False
        
        # Verifica a extensão pgvector
        if not self.check_pgvector_extension():
            return False
        
        # Configura as tabelas de usuários
        if not self.setup_user_tables():
            return False
        
        # Verifica as coleções de vetores existentes
        collections = self.get_vector_collections()
        
        if not collections:
            logger.info("\n[AVISO] Nenhuma coleção de vetores encontrada.")
            logger.info("   As coleções serão criadas na primeira execução do agente.")
        
        # Fecha a conexão com o banco de dados
        if self.conn:
            self.conn.close()
        
        logger.info("[OK] Configuração do banco de dados concluída com sucesso!")
        return True


def setup_database():
    """
    Função de entrada para configurar o banco de dados
    
    Returns:
        bool: True se o banco de dados foi configurado com sucesso, False caso contrário
    """
    try:
        db_setup = DatabaseSetup()
        return db_setup.setup_database()
    except Exception as e:
        logger.error(f"Erro ao configurar banco de dados: {e}")
        return False


if __name__ == "__main__":
    # Configuração de logging para exibir mensagens no console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Executa a configuração do banco de dados
    result = setup_database()
    
    if result:
        print("Banco de dados configurado com sucesso!")
    else:
        print("Erro ao configurar banco de dados. Verifique os logs para mais detalhes.") 
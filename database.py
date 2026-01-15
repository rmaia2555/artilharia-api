import os
import sqlite3
from datetime import datetime

# -----------------------------------------------------------------------------
# Config / Detecção de engine
# -----------------------------------------------------------------------------
RAW_DATABASE_URL = os.getenv("DATABASE_URL")  # pode ser None

USE_POSTGRES = False
DATABASE_URL = None
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/noticias.db")

if RAW_DATABASE_URL:
    DATABASE_URL = RAW_DATABASE_URL.strip()

    # Alguns providers usam "postgres://", normalizamos para "postgresql://"
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    if DATABASE_URL.startswith("postgresql://"):
        USE_POSTGRES = True

if USE_POSTGRES:
    import psycopg2  # noqa: E402
else:
    psycopg2 = None  # noqa: E402


class Database:
    def __init__(self):
        if USE_POSTGRES:
            self.conn = psycopg2.connect(DATABASE_URL)
            self.conn.autocommit = True
        else:
            # SQLite
            db_dir = os.path.dirname(DATABASE_PATH)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)

        self.criar_tabelas()

    def criar_tabelas(self):
        cur = self.conn.cursor()

        if USE_POSTGRES:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS noticias (
                    id SERIAL PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    fonte TEXT,
                    data_publicacao TEXT,
                    resumo TEXT,
                    palavras_chave TEXT,
                    enviado BOOLEAN DEFAULT FALSE,
                    data_envio TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS estatisticas (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    noticias_encontradas INTEGER,
                    noticias_enviadas INTEGER,
                    tempo_execucao REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS noticias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    fonte TEXT,
                    data_publicacao TEXT,
                    resumo TEXT,
                    palavras_chave TEXT,
                    enviado BOOLEAN DEFAULT 0,
                    data_envio TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS estatisticas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    noticias_encontradas INTEGER,
                    noticias_enviadas INTEGER,
                    tempo_execucao REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self.conn.commit()

    # -----------------------------------------------------------------------------
    # Helpers de query (para endpoints não precisarem saber se é Postgres ou SQLite)
    # -----------------------------------------------------------------------------
    def _placeholder(self):
        return "%s" if USE_POSTGRES else "?"

    def query_one(self, sql_pg: str, sql_sqlite: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(sql_pg if USE_POSTGRES else sql_sqlite, params)
        return cur.fetchone()

    def query_all(self, sql_pg: str, sql_sqlite: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(sql_pg if USE_POSTGRES else sql_sqlite, params)
        return cur.fetchall()

    def exec(self, sql_pg: str, sql_sqlite: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(sql_pg if USE_POSTGRES else sql_sqlite, params)
        if not USE_POSTGRES:
            self.conn.commit()
        return cur

    # -----------------------------------------------------------------------------
    # Funções usadas pelo bot (mantive compatível)
    # -----------------------------------------------------------------------------
    def noticia_existe(self, url: str) -> bool:
        row = self.query_one(
            "SELECT id FROM noticias WHERE url = %s",
            "SELECT id FROM noticias WHERE url = ?",
            (url,),
        )
        return row is not None

    def adicionar_noticia(self, titulo, url, fonte, data_pub, resumo="", keywords=""):
        try:
            if USE_POSTGRES:
                cur = self.exec(
                    """
                    INSERT INTO noticias (titulo, url, fonte, data_publicacao, resumo, palavras_chave)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    "",
                    (titulo, url, fonte, data_pub, resumo, keywords),
                )
                return cur.fetchone()[0]
            else:
                cur = self.exec(
                    "",
                    """
                    INSERT INTO noticias (titulo, url, fonte, data_publicacao, resumo, palavras_chave)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (titulo, url, fonte, data_pub, resumo, keywords),
                )
                return cur.lastrowid
        except Exception:
            return None

    def marcar_como_enviada(self, noticia_id: int):
        now = datetime.now().isoformat()
        self.exec(
            "UPDATE noticias SET enviado = TRUE, data_envio = %s WHERE id = %s",
            "UPDATE noticias SET enviado = 1, data_envio = ? WHERE id = ?",
            (now, noticia_id),
        )

    def registrar_execucao(self, encontradas: int, enviadas: int, tempo: float):
        now = datetime.now().isoformat()
        self.exec(
            """
            INSERT INTO estatisticas (data, noticias_encontradas, noticias_enviadas, tempo_execucao)
            VALUES (%s, %s, %s, %s)
            """,
            """
            INSERT INTO estatisticas (data, noticias_encontradas, noticias_enviadas, tempo_execucao)
            VALUES (?, ?, ?, ?)
            """,
            (now, encontradas, enviadas, tempo),
        )

    def fechar(self):
        try:
            self.conn.close()
        except Exception:
            pass

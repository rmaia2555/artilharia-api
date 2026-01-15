# database.py
import os
import sqlite3
from typing import Optional

# Postgres (psycopg2)
try:
    import psycopg2
except Exception:
    psycopg2 = None


def _normalize_database_url(url: str) -> str:
    """
    Render às vezes fornece postgres://
    psycopg2 prefere postgresql://
    """
    url = url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL_RAW: Optional[str] = os.getenv("DATABASE_URL")
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/noticias.db")

USE_POSTGRES: bool = False
DATABASE_URL: Optional[str] = None

if DATABASE_URL_RAW:
    normalized = _normalize_database_url(DATABASE_URL_RAW)
    if normalized.startswith("postgresql://"):
        DATABASE_URL = normalized
        USE_POSTGRES = True


class Database:
    def __init__(self):
        self.conn = None

        if USE_POSTGRES:
            if psycopg2 is None:
                raise RuntimeError(
                    "USE_POSTGRES=True mas psycopg2 não está disponível. "
                    "Confira requirements.txt (psycopg2-binary) e versão do Python no Render."
                )
            self.conn = psycopg2.connect(DATABASE_URL)
            self.conn.autocommit = True
        else:
            # SQLite local
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
                    created_at TIMESTAMP DEFAULT NOW()
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
                    enviado INTEGER DEFAULT 0,
                    data_envio TEXT,
                    created_at TEXT
                );
                """
            )
            self.conn.commit()

    def fechar(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass

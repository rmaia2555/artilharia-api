import os
import sqlite3
from datetime import datetime

# =========================
# Config / seleção do banco
# =========================
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Às vezes o provedor usa postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = DATABASE_URL.startswith("postgresql://")

# SQLite (dev/local)
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/noticias.db")

# Postgres (produção/Render)
if USE_POSTGRES:
    import psycopg2


class Database:
    def __init__(self):
        if USE_POSTGRES:
            self.conn = psycopg2.connect(DATABASE_URL)
            self.conn.autocommit = True
        else:
            db_dir = os.path.dirname(DATABASE_PATH)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)

        self.criar_tabelas()

    def criar_tabelas(self):
        cursor = self.conn.cursor()

        if USE_POSTGRES:
            cursor.execute(
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

            cursor.execute(
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
            cursor.execute(
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

            cursor.execute(
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

    def noticia_existe(self, url: str) -> bool:
        cursor = self.conn.cursor()
        if USE_POSTGRES:
            cursor.execute("SELECT id FROM noticias WHERE url = %s", (url,))
        else:
            cursor.execute("SELECT id FROM noticias WHERE url = ?", (url,))
        return cursor.fetchone() is not None

    def adicionar_noticia(self, titulo, url, fonte, data_pub, resumo="", keywords=""):
        try:
            cursor = self.conn.cursor()
            if USE_POSTGRES:
                cursor.execute(
                    """
                    INSERT INTO noticias
                    (titulo, url, fonte, data_publicacao, resumo, palavras_chave)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (titulo, url, fonte, data_pub, resumo, keywords),
                )
                return cursor.fetchone()[0]
            else:
                cursor.execute(
                    """
                    INSERT INTO noticias
                    (titulo, url, fonte, data_publicacao, resumo, palavras_chave)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (titulo, url, fonte, data_pub, resumo, keywords),
                )
                self.conn.commit()
                return cursor.lastrowid
        except Exception:
            return None

    def marcar_como_enviada(self, noticia_id: int):
        cursor = self.conn.cursor()
        agora = datetime.now().isoformat()

        if USE_POSTGRES:
            cursor.execute(
                "UPDATE noticias SET enviado = TRUE, data_envio = %s WHERE id = %s",
                (agora, noticia_id),
            )
        else:
            cursor.execute(
                "UPDATE noticias SET enviado = 1, data_envio = ? WHERE id = ?",
                (agora, noticia_id),
            )
            self.conn.commit()

    def obter_estatisticas(self):
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM noticias")
        total = cursor.fetchone()[0]

        if USE_POSTGRES:
            cursor.execute("SELECT COUNT(*) FROM noticias WHERE enviado = TRUE")
        else:
            cursor.execute("SELECT COUNT(*) FROM noticias WHERE enviado = 1")

        enviadas = cursor.fetchone()[0]

        return {"total": total, "enviadas": enviadas, "pendentes": total - enviadas}

    def registrar_execucao(self, encontradas: int, enviadas: int, tempo: float):
        cursor = self.conn.cursor()
        agora = datetime.now().isoformat()

        if USE_POSTGRES:
            cursor.execute(
                """
                INSERT INTO estatisticas (data, noticias_encontradas, noticias_enviadas, tempo_execucao)
                VALUES (%s, %s, %s, %s)
                """,
                (agora, encontradas, enviadas, tempo),
            )
        else:
            cursor.execute(
                """
                INSERT INTO estatisticas (data, noticias_encontradas, noticias_enviadas, tempo_execucao)
                VALUES (?, ?, ?, ?)
                """,
                (agora, encontradas, enviadas, tempo),
            )
            self.conn.commit()

    def fechar(self):
        self.conn.close()

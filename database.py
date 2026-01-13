import sqlite3
import os
from datetime import datetime
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/noticias.db')
class Database:
    def __init__(self):
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.criar_tabelas()
    
    def criar_tabelas(self):
        cursor = self.conn.cursor()
        cursor.execute('''
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
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estatisticas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                noticias_encontradas INTEGER,
                noticias_enviadas INTEGER,
                tempo_execucao REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def noticia_existe(self, url):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM noticias WHERE url = ?', (url,))
        return cursor.fetchone() is not None
    
    def adicionar_noticia(self, titulo, url, fonte, data_pub, resumo='', keywords=''):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO noticias 
                (titulo, url, fonte, data_publicacao, resumo, palavras_chave)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (titulo, url, fonte, data_pub, resumo, keywords))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def marcar_como_enviada(self, noticia_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE noticias 
            SET enviado = 1, data_envio = ? 
            WHERE id = ?
        ''', (datetime.now().isoformat(), noticia_id))
        self.conn.commit()
    
    def obter_estatisticas(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM noticias')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM noticias WHERE enviado = 1')
        enviadas = cursor.fetchone()[0]
        return {
            'total': total,
            'enviadas': enviadas,
            'pendentes': total - enviadas
        }
    
    def registrar_execucao(self, encontradas, enviadas, tempo):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO estatisticas 
            (data, noticias_encontradas, noticias_enviadas, tempo_execucao)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), encontradas, enviadas, tempo))
        self.conn.commit()
    
    def fechar(self):
        self.conn.close()
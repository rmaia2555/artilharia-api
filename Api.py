# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import Database
from datetime import datetime, timedelta
from typing import List, Optional

app = FastAPI(title="Artilharia Global API", version="1.0")

# Permitir acesso do app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()

# ==================== NOTÍCIAS ====================

@app.get("/noticias")
def listar_noticias(
    limite: int = 20,
    dias: int = 7,
    categoria: Optional[str] = None
):
    """
    Lista notícias recentes
    
    Parâmetros:
    - limite: quantas notícias retornar (padrão: 20)
    - dias: últimos N dias (padrão: 7)
    - categoria: filtrar por equipamento (ex: M777, HIMARS)
    """
    cursor = db.conn.cursor()
    
    data_inicio = (datetime.now() - timedelta(days=dias)).isoformat()
    
    if categoria:
        cursor.execute('''
            SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
            FROM noticias
            WHERE data_publicacao >= ?
            AND (palavras_chave LIKE ? OR titulo LIKE ?)
            ORDER BY data_publicacao DESC
            LIMIT ?
        ''', (data_inicio, f'%{categoria}%', f'%{categoria}%', limite))
    else:
        cursor.execute('''
            SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
            FROM noticias
            WHERE data_publicacao >= ?
            ORDER BY data_publicacao DESC
            LIMIT ?
        ''', (data_inicio, limite))
    
    noticias = []
    for row in cursor.fetchall():
        noticias.append({
            "id": row[0],
            "titulo": row[1],
            "url": row[2],
            "fonte": row[3],
            "data_publicacao": row[4],
            "resumo": row[5],
            "palavras_chave": row[6].split(',') if row[6] else []
        })
    
    return {
        "total": len(noticias),
        "noticias": noticias
    }

@app.get("/noticias/{noticia_id}")
def detalhe_noticia(noticia_id: int):
    """Detalhes de uma notícia específica"""
    cursor = db.conn.cursor()
    cursor.execute('''
        SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
        FROM noticias
        WHERE id = ?
    ''', (noticia_id,))
    
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")
    
    return {
        "id": row[0],
        "titulo": row[1],
        "url": row[2],
        "fonte": row[3],
        "data_publicacao": row[4],
        "resumo": row[5],
        "palavras_chave": row[6].split(',') if row[6] else []
    }

# ==================== ESTATÍSTICAS ====================

@app.get("/estatisticas")
def estatisticas_gerais():
    """Estatísticas do sistema"""
    cursor = db.conn.cursor()
    
    # Total de notícias
    cursor.execute('SELECT COUNT(*) FROM noticias')
    total = cursor.fetchone()[0]
    
    # Últimas 24h
    ontem = (datetime.now() - timedelta(days=1)).isoformat()
    cursor.execute('SELECT COUNT(*) FROM noticias WHERE data_publicacao >= ?', (ontem,))
    ultimas_24h = cursor.fetchone()[0]
    
    # Últimos 7 dias
    semana = (datetime.now() - timedelta(days=7)).isoformat()
    cursor.execute('SELECT COUNT(*) FROM noticias WHERE data_publicacao >= ?', (semana,))
    ultimos_7dias = cursor.fetchone()[0]
    
    # Top 5 fontes
    cursor.execute('''
        SELECT fonte, COUNT(*) as count
        FROM noticias
        GROUP BY fonte
        ORDER BY count DESC
        LIMIT 5
    ''')
    top_fontes = [{"fonte": row[0], "total": row[1]} for row in cursor.fetchall()]
    
    return {
        "total_noticias": total,
        "ultimas_24h": ultimas_24h,
        "ultimos_7_dias": ultimos_7dias,
        "top_fontes": top_fontes
    }

# ==================== EXÉRCITOS ====================

@app.get("/exercitos")
def listar_exercitos():
    """Lista todos os exércitos cadastrados"""
    # Por enquanto, dados estáticos
    # Depois vamos popular no banco
    exercitos = [
        {
            "id": 1,
            "pais": "Brasil",
            "nome_oficial": "Exército Brasileiro",
            "bandeira": "🇧🇷",
            "efetivo_total": 360000,
            "efetivo_artilharia": 15000,
            "principais_sistemas": ["ASTROS II", "M109A5", "Gepard"]
        },
        {
            "id": 2,
            "pais": "Estados Unidos",
            "nome_oficial": "United States Army",
            "bandeira": "🇺🇸",
            "efetivo_total": 1390000,
            "efetivo_artilharia": 180000,
            "principais_sistemas": ["M777", "HIMARS", "M109A7", "Patriot"]
        },
        {
            "id": 3,
            "pais": "Rússia",
            "nome_oficial": "Exército Russo",
            "bandeira": "🇷🇺",
            "efetivo_total": 1150000,
            "efetivo_artilharia": 200000,
            "principais_sistemas": ["2S19 Msta", "BM-30 Smerch", "S-400"]
        },
    ]
    
    return {"total": len(exercitos), "exercitos": exercitos}

@app.get("/exercitos/{exercito_id}")
def detalhe_exercito(exercito_id: int):
    """Detalhes de um exército específico"""
    # Exemplo estático
    if exercito_id == 1:
        return {
            "id": 1,
            "pais": "Brasil",
            "nome_oficial": "Exército Brasileiro",
            "bandeira_url": "https://flagcdn.com/w320/br.png",
            "efetivo_total": 360000,
            "efetivo_artilharia": 15000,
            "orcamento_anual": "23 bilhões USD",
            "doutrina_resumo": "Baseada em doutrina francesa e americana...",
            "principais_sistemas": [
                {
                    "nome": "ASTROS II",
                    "tipo": "MLRS",
                    "alcance": "90 km"
                },
                {
                    "nome": "M109A5 Howitzer",
                    "tipo": "Obuseiro Autopropulsado",
                    "alcance": "30 km"
                }
            ],
            "curiosidades": [
                "Maior exército da América do Sul",
                "Possui Sistema ASTROS desenvolvido nacionalmente"
            ]
        }
    
    raise HTTPException(status_code=404, detail="Exército não encontrado")

# ==================== EQUIPAMENTOS ====================

@app.get("/equipamentos")
def listar_equipamentos(tipo: Optional[str] = None):
    """
    Lista equipamentos
    
    Parâmetros:
    - tipo: filtrar por tipo (obuseiro, mlrs, aa)
    """
    # Dados estáticos por enquanto
    equipamentos = [
        {
            "id": 1,
            "nome": "M777 Howitzer",
            "tipo": "obuseiro",
            "pais_origem": "🇺🇸 EUA",
            "alcance_km": 40,
            "usuarios": ["EUA", "Canadá", "Austrália", "Índia", "Ucrânia"]
        },
        {
            "id": 2,
            "nome": "HIMARS",
            "tipo": "mlrs",
            "pais_origem": "🇺🇸 EUA",
            "alcance_km": 300,
            "usuarios": ["EUA", "Polônia", "Romênia", "Ucrânia"]
        },
        {
            "id": 3,
            "nome": "Caesar",
            "tipo": "obuseiro",
            "pais_origem": "🇫🇷 França",
            "alcance_km": 42,
            "usuarios": ["França", "Dinamarca", "Ucrânia", "Marrocos"]
        },
    ]
    
    if tipo:
        equipamentos = [e for e in equipamentos if e["tipo"] == tipo.lower()]
    
    return {"total": len(equipamentos), "equipamentos": equipamentos}

@app.get("/equipamentos/{equipamento_id}")
def detalhe_equipamento(equipamento_id: int):
    """Detalhes de um equipamento específico"""
    if equipamento_id == 1:
        return {
            "id": 1,
            "nome": "M777 Howitzer",
            "tipo": "Obuseiro Rebocado",
            "pais_origem": "Estados Unidos",
            "bandeira_origem": "🇺🇸",
            "imagem_url": "https://exemplo.com/m777.jpg",
            "especificacoes": {
                "calibre": "155mm",
                "alcance_max": "40 km (projétil guiado)",
                "alcance_normal": "24 km",
                "peso": "4.200 kg",
                "tripulacao": 5,
                "cadencia_tiro": "2 tiros/minuto (sustentado)"
            },
            "ano_introducao": 2005,
            "usuarios": [
                {"pais": "Estados Unidos", "quantidade": 1000},
                {"pais": "Canadá", "quantidade": 37},
                {"pais": "Austrália", "quantidade": 57},
                {"pais": "Índia", "quantidade": 145},
                {"pais": "Ucrânia", "quantidade": 126}
            ],
            "em_producao": True,
            "curiosidades": [
                "Construído majoritariamente em titânio para reduzir peso",
                "Pode ser transportado por helicóptero",
                "Sistema de pontaria digital avançado"
            ],
            "noticias_relacionadas": [
                {
                    "id": 123,
                    "titulo": "EUA entrega mais M777 para Ucrânia",
                    "data": "2026-01-09"
                }
            ]
        }
    
    raise HTTPException(status_code=404, detail="Equipamento não encontrado")

# ==================== HEALTH CHECK ====================

@app.get("/")
def root():
    return {
        "app": "Artilharia Global API",
        "versao": "1.0",
        "status": "online",
        "endpoints": [
            "/noticias",
            "/noticias/{id}",
            "/estatisticas",
            "/exercitos",
            "/exercitos/{id}",
            "/equipamentos",
            "/equipamentos/{id}"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
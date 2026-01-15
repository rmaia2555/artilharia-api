# api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, timedelta

from database import Database, USE_POSTGRES

app = FastAPI(title="Artilharia Global API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()


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
            "/equipamentos/{id}",
            "/debug/db",
        ],
    }


@app.get("/noticias")
def listar_noticias(
    limite: int = 20,
    dias: int = 7,
    categoria: Optional[str] = None,
):
    cur = db.conn.cursor()
    data_inicio_iso = (datetime.utcnow() - timedelta(days=dias)).isoformat()

    if USE_POSTGRES:
        # Convert RSS date string -> timestamp for correct filtering
        # Example RSS: "Wed, 14 Jan 2026 15:38:00 GMT"
        # fmt: "Dy, DD Mon YYYY HH24:MI:SS GMT"
        if categoria:
            cur.execute(
                """
                SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
                FROM noticias
                WHERE to_timestamp(data_publicacao, 'Dy, DD Mon YYYY HH24:MI:SS "GMT"') >= %s::timestamp
                  AND (palavras_chave ILIKE %s OR titulo ILIKE %s)
                ORDER BY to_timestamp(data_publicacao, 'Dy, DD Mon YYYY HH24:MI:SS "GMT"') DESC
                LIMIT %s
                """,
                (data_inicio_iso, f"%{categoria}%", f"%{categoria}%", limite),
            )
        else:
            cur.execute(
                """
                SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
                FROM noticias
                WHERE to_timestamp(data_publicacao, 'Dy, DD Mon YYYY HH24:MI:SS "GMT"') >= %s::timestamp
                ORDER BY to_timestamp(data_publicacao, 'Dy, DD Mon YYYY HH24:MI:SS "GMT"') DESC
                LIMIT %s
                """,
                (data_inicio_iso, limite),
            )
        rows = cur.fetchall()
    else:
        # SQLite fallback: keep as-is (string compare), but your production is Postgres anyway.
        if categoria:
            cur.execute(
                """
                SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
                FROM noticias
                WHERE data_publicacao >= ?
                  AND (palavras_chave LIKE ? OR titulo LIKE ?)
                ORDER BY data_publicacao DESC
                LIMIT ?
                """,
                (data_inicio_iso, f"%{categoria}%", f"%{categoria}%", limite),
            )
        else:
            cur.execute(
                """
                SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
                FROM noticias
                WHERE data_publicacao >= ?
                ORDER BY data_publicacao DESC
                LIMIT ?
                """,
                (data_inicio_iso, limite),
            )
        rows = cur.fetchall()

    noticias = []
    for row in rows:
        noticias.append(
            {
                "id": row[0],
                "titulo": row[1],
                "url": row[2],
                "fonte": row[3],
                "data_publicacao": row[4],
                "resumo": row[5] or "",
                "palavras_chave": row[6].split(",") if row[6] else [],
            }
        )

    return {"total": len(noticias), "noticias": noticias}


@app.get("/noticias/{noticia_id}")
def detalhe_noticia(noticia_id: int):
    cur = db.conn.cursor()

    if USE_POSTGRES:
        cur.execute(
            """
            SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
            FROM noticias
            WHERE id = %s
            """,
            (noticia_id,),
        )
    else:
        cur.execute(
            """
            SELECT id, titulo, url, fonte, data_publicacao, resumo, palavras_chave
            FROM noticias
            WHERE id = ?
            """,
            (noticia_id,),
        )

    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Notícia não encontrada")

    return {
        "id": row[0],
        "titulo": row[1],
        "url": row[2],
        "fonte": row[3],
        "data_publicacao": row[4],
        "resumo": row[5] or "",
        "palavras_chave": row[6].split(",") if row[6] else [],
    }


@app.get("/estatisticas")
def estatisticas_gerais():
    cur = db.conn.cursor()

    cur.execute("SELECT COUNT(*) FROM noticias")
    total = cur.fetchone()[0]

    if USE_POSTGRES:
        # Use SQL timestamps to get correct windows
        cur.execute(
            """
            SELECT COUNT(*) FROM noticias
            WHERE to_timestamp(data_publicacao, 'Dy, DD Mon YYYY HH24:MI:SS "GMT"') >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '24 hours'
            """
        )
        ultimas_24h = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*) FROM noticias
            WHERE to_timestamp(data_publicacao, 'Dy, DD Mon YYYY HH24:MI:SS "GMT"') >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days'
            """
        )
        ultimos_7dias = cur.fetchone()[0]

        cur.execute(
            """
            SELECT fonte, COUNT(*) as count
            FROM noticias
            GROUP BY fonte
            ORDER BY count DESC
            LIMIT 5
            """
        )
        top_fontes = [{"fonte": r[0], "total": r[1]} for r in cur.fetchall()]
    else:
        # SQLite fallback (not perfect if RSS date), but OK for local
        ontem = (datetime.utcnow() - timedelta(days=1)).isoformat()
        semana = (datetime.utcnow() - timedelta(days=7)).isoformat()

        cur.execute("SELECT COUNT(*) FROM noticias WHERE data_publicacao >= ?", (ontem,))
        ultimas_24h = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM noticias WHERE data_publicacao >= ?", (semana,))
        ultimos_7dias = cur.fetchone()[0]

        cur.execute(
            """
            SELECT fonte, COUNT(*) as count
            FROM noticias
            GROUP BY fonte
            ORDER BY count DESC
            LIMIT 5
            """
        )
        top_fontes = [{"fonte": r[0], "total": r[1]} for r in cur.fetchall()]

    return {
        "total_noticias": total,
        "ultimas_24h": ultimas_24h,
        "ultimos_7_dias": ultimos_7dias,
        "top_fontes": top_fontes,
    }


@app.get("/exercitos")
def listar_exercitos():
    exercitos = [
        {
            "id": 1,
            "pais": "Brasil",
            "nome_oficial": "Exército Brasileiro",
            "bandeira": "🇧🇷",
            "efetivo_total": 360000,
            "efetivo_artilharia": 15000,
            "principais_sistemas": ["ASTROS II", "M109A5", "Gepard"],
        },
        {
            "id": 2,
            "pais": "Estados Unidos",
            "nome_oficial": "United States Army",
            "bandeira": "🇺🇸",
            "efetivo_total": 1390000,
            "efetivo_artilharia": 180000,
            "principais_sistemas": ["M777", "HIMARS", "M109A7", "Patriot"],
        },
        {
            "id": 3,
            "pais": "Rússia",
            "nome_oficial": "Exército Russo",
            "bandeira": "🇷🇺",
            "efetivo_total": 1150000,
            "efetivo_artilharia": 200000,
            "principais_sistemas": ["2S19 Msta", "BM-30 Smerch", "S-400"],
        },
    ]
    return {"total": len(exercitos), "exercitos": exercitos}


@app.get("/exercitos/{exercito_id}")
def detalhe_exercito(exercito_id: int):
    if exercito_id == 1:
        return {
            "id": 1,
            "pais": "Brasil",
            "nome_oficial": "Exército Brasileiro",
            "bandeira_url": "https://flagcdn.com/w320/br.png",
            "efetivo_total": 360000,
            "efetivo_artilharia": 15000,
            "orcamento_anual": "23 bilhões USD",
            "doutrina_resumo": "Baseada em doutrina francesa e americana",
            "principais_sistemas": [
                {"nome": "ASTROS II", "tipo": "MLRS", "alcance": "90 km"},
                {"nome": "M109A5 Howitzer", "tipo": "Obuseiro Autopropulsado", "alcance": "30 km"},
            ],
            "curiosidades": [
                "Maior exército da América do Sul",
                "Possui Sistema ASTROS desenvolvido nacionalmente",
            ],
        }
    raise HTTPException(status_code=404, detail="Exército não encontrado")


@app.get("/equipamentos")
def listar_equipamentos(tipo: Optional[str] = None):
    equipamentos = [
        {
            "id": 1,
            "nome": "M777 Howitzer",
            "tipo": "obuseiro",
            "pais_origem": "🇺🇸 EUA",
            "alcance_km": 40,
            "usuarios": ["EUA", "Canadá", "Austrália", "Índia", "Ucrânia"],
        },
        {
            "id": 2,
            "nome": "HIMARS",
            "tipo": "mlrs",
            "pais_origem": "🇺🇸 EUA",
            "alcance_km": 300,
            "usuarios": ["EUA", "Polônia", "Romênia", "Ucrânia"],
        },
        {
            "id": 3,
            "nome": "Caesar",
            "tipo": "obuseiro",
            "pais_origem": "🇫🇷 França",
            "alcance_km": 42,
            "usuarios": ["França", "Dinamarca", "Ucrânia", "Marrocos"],
        },
    ]

    if tipo:
        equipamentos = [e for e in equipamentos if e["tipo"] == tipo.lower()]

    return {"total": len(equipamentos), "equipamentos": equipamentos}


@app.get("/equipamentos/{equipamento_id}")
def detalhe_equipamento(equipamento_id: int):
    if equipamento_id == 1:
        return {
            "id": 1,
            "nome": "M777 Howitzer",
            "tipo": "Obuseiro Rebocado",
            "pais_origem": "Estados Unidos",
            "bandeira_origem": "🇺🇸",
            "especificacoes": {
                "calibre": "155mm",
                "alcance_max": "40 km (projétil guiado)",
                "alcance_normal": "24 km",
                "peso": "4.200 kg",
                "tripulacao": 5,
                "cadencia_tiro": "2 tiros/minuto (sustentado)",
            },
            "ano_introducao": 2005,
            "usuarios": [
                {"pais": "Estados Unidos", "quantidade": 1000},
                {"pais": "Canadá", "quantidade": 37},
                {"pais": "Austrália", "quantidade": 57},
                {"pais": "Índia", "quantidade": 145},
                {"pais": "Ucrânia", "quantidade": 126},
            ],
            "em_producao": True,
            "curiosidades": [
                "Construído majoritariamente em titânio para reduzir peso",
                "Pode ser transportado por helicóptero",
                "Sistema de pontaria digital avançado",
            ],
        }
    raise HTTPException(status_code=404, detail="Equipamento não encontrado")


@app.get("/debug/db")
def debug_db():
    cur = db.conn.cursor()

    if USE_POSTGRES:
        cur.execute("SELECT current_database(), current_user;")
        dbinfo = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM noticias;")
        total = cur.fetchone()[0]

        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'noticias'
            ORDER BY ordinal_position;
            """
        )
        cols = [r[0] for r in cur.fetchall()]

        return {"engine": "postgres", "dbinfo": dbinfo, "total_noticias": total, "cols": cols}

    cur.execute("SELECT COUNT(*) FROM noticias;")
    total = cur.fetchone()[0]
    return {"engine": "sqlite", "total_noticias": total}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

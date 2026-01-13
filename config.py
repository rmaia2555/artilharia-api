Configurações do Monitor de Artilharia
Desenvolvido por Cap Maia - 2026
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ==================== CREDENCIAIS (de variáveis de ambiente) ====================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY')

# ==================== PALAVRAS-CHAVE ====================
KEYWORDS = {
    'pt': [
        'artilharia', 'obuseiro', 'obuses', 'canhão', 'canhões',
        'howitzer', 'artilharia autopropulsada',
        'defesa antiaérea', 'artilharia antiaérea',
        'foguete guiado', 'míssil terra-ar'
    ],
    'en': [
        'artillery', 'howitzer', 'self-propelled artillery',
        'anti-aircraft', 'air defense', 'SPG',
        'HIMARS', 'M777', 'Caesar', 'PzH 2000', 'K9 Thunder',
        'Paladin', 'ARCHER', 'Krab', 'Zuzana',
        'rocket artillery', 'MLRS', 'guided rocket'
    ],
    'es': [
        'artillería', 'obús', 'artillería autopropulsada',
        'defensa antiaérea', 'cohete guiado'
    ]
}

EQUIPAMENTOS = [
    'M777', 'HIMARS', 'Caesar', 'PzH 2000', 'K9 Thunder',
    'M109 Paladin', 'ARCHER', 'Krab', 'Zuzana', 'AS90',
    'Type 99', 'PLZ-05', '2S19 Msta', 'Koalitsiya-SV',
    'ATMOS', 'G6 Rhino', 'Nora B-52'
]

EXCLUDE_KEYWORDS = [
    'world war', 'ww2', 'wwii', 'segunda guerra', 'second world war',
    'museum', 'museu', 'memorial', 'history', 'história',
    'historic', 'histórico', 'antique', 'antigo',
    'replica', 'réplica', 'restoration', 'restauração'
]

NEWS_SOURCES = {
    'priority': [
        'defense-news', 'military-times', 'the-guardian',
        'bbc-news', 'reuters', 'associated-press', 'al-jazeera-english'
    ],
    'general': [
        'cnn', 'fox-news', 'nbc-news', 'abc-news',
        'the-washington-post', 'the-wall-street-journal'
    ]
}

MAX_NOTICIAS_POR_BUSCA = 20
IDADE_MAXIMA_HORAS = 48
INTERVALO_BUSCA_HORAS = 6
MAX_RESUMO_TOKENS = 300

DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/noticias.db')
LOG_PATH = "logs/monitor.log"

MENSAGEM_BOAS_VINDAS = """🎖️ *MONITOR DE ARTILHARIA ATIVADO*

Olá, Cap Maia!

Sistema de monitoramento de notícias militares em operação.

📰 Fontes: NewsAPI + Google News
🔍 Palavras-chave: Artillery, Howitzer, Defense
⏰ Frequência: A cada 6 horas
🤖 IA: Resumos automáticos com Groq

*Comandos Disponíveis:*
/hoje - Notícias de hoje
/stats - Estatísticas
/help - Ajuda

_Desenvolvido por Cap Maia - 2026_
"""

MENSAGEM_AJUDA = """🎖️ *COMANDOS DO MONITOR*

/start - Inicia o bot
/hoje - Notícias de hoje
/stats - Estatísticas
/help - Esta mensagem

*Funcionamento:*
- Busca automática a cada 6 horas
- Filtros inteligentes
- Resumos gerados por IA
- Apenas notícias atuais

_Cap Maia - 2026_
"""
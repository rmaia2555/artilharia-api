@echo off
chcp 65001 >nul
color 0B

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         🌐 ARTILHARIA GLOBAL API - INICIANDO              ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d E:\App

echo [1/2] Ativando ambiente virtual...
if not exist venv (
    echo ❌ Ambiente virtual não encontrado!
    echo    Execute INSTALAR_API.bat primeiro
    pause
    exit /b 1
)
call venv\Scripts\activate
echo ✅ Ambiente ativado
echo.

echo [2/2] Iniciando API...
echo.
echo ════════════════════════════════════════════════════════════════
echo   🌐 API rodando em: http://localhost:8000
echo   📚 Documentação: http://localhost:8000/docs
echo   
echo   Endpoints disponíveis:
echo   • GET /noticias
echo   • GET /estatisticas
echo   • GET /exercitos
echo   • GET /equipamentos
echo.
echo   Pressione Ctrl+C para parar
echo ════════════════════════════════════════════════════════════════
echo.

python api.py

echo.
echo ════════════════════════════════════════════════════════════════
echo API encerrada
echo ════════════════════════════════════════════════════════════════
echo.
pause
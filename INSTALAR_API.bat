@echo off
chcp 65001 >nul
color 0A

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║         🌐 INSTALAÇÃO - ARTILHARIA GLOBAL API             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

cd /d E:\App

echo [1/6] Copiando arquivos necessários...
if not exist database.py (
    echo    Copiando database.py...
    copy E:\BOT\database.py . >nul
)
if not exist config.py (
    echo    Copiando config.py...
    copy E:\BOT\config.py . >nul
)
echo ✅ Arquivos copiados
echo.

echo [2/6] Criando pasta data...
if not exist data mkdir data
echo ✅ Pasta criada
echo.

echo [3/6] Criando ambiente virtual...
if exist venv (
    echo    Removendo ambiente antigo...
    rmdir /s /q venv
)
python -m venv venv
echo ✅ Ambiente criado
echo.

echo [4/6] Ativando ambiente...
call venv\Scripts\activate
echo ✅ Ambiente ativado
echo.

echo [5/6] Atualizando pip...
python -m pip install --upgrade pip -q
echo ✅ Pip atualizado
echo.

echo [6/6] Instalando dependências...
pip install fastapi==0.109.0 -q
echo    ✅ fastapi
pip install uvicorn==0.27.0 -q
echo    ✅ uvicorn
echo.

echo ════════════════════════════════════════════════════════════════
echo ✅ INSTALAÇÃO CONCLUÍDA!
echo.
echo 📁 Estrutura:
echo    E:\App\
echo    ├── api.py
echo    ├── database.py
echo    ├── config.py
echo    ├── data\
echo    └── venv\
echo.
echo 🚀 PRÓXIMO PASSO: Execute RODAR_API.bat
echo ════════════════════════════════════════════════════════════════
echo.
pause
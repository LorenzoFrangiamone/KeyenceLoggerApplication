
@echo off
set APP_NAME=KCompareAgent

call .\venv\Scripts\activate

echo Checking llama_cpp...
python -c "from llama_cpp import Llama; print('llama_cpp OK')"
if errorlevel 1 (
    echo llama_cpp non trovato nel venv.
    pause
    exit /b 1
)

echo Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Building...
python -m PyInstaller ^
  --onedir ^
  --windowed ^
  --collect-all llama_cpp ^
  --hidden-import llama_cpp ^
  --name %APP_NAME% ^
  Main.py

echo Preparing models folder...
mkdir dist\%APP_NAME%\models
copy models\LEGGIMI.txt dist\%APP_NAME%\models\

echo Compressing portable package...
if exist dist\%APP_NAME%.zip del dist\%APP_NAME%.zip
powershell -NoProfile -Command "Compress-Archive -Path 'dist\%APP_NAME%' -DestinationPath 'dist\%APP_NAME%.zip'"

echo Done.
pause

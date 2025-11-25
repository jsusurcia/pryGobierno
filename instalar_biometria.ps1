# ========================================
# Script de Instalación Automática
# Sistema de Biometría Facial
# ========================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Instalación de Biometría Facial" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Verificar Python 3.11
Write-Host "[1/7] Verificando Python 3.11..." -ForegroundColor Yellow
$pythonVersion = py -3.11 --version 2>&1

if ($pythonVersion -match "Python 3.11") {
    Write-Host "✓ Python 3.11 encontrado: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python 3.11 no encontrado" -ForegroundColor Red
    Write-Host "Por favor, instala Python 3.11 desde:" -ForegroundColor Red
    Write-Host "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -ForegroundColor Yellow
    exit 1
}

# Paso 2: Renombrar entorno virtual anterior
Write-Host ""
Write-Host "[2/7] Respaldando entorno virtual anterior..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    if (Test-Path ".venv_old") {
        Remove-Item -Recurse -Force .venv_old
    }
    Rename-Item .venv .venv_old
    Write-Host "✓ Entorno anterior respaldado como .venv_old" -ForegroundColor Green
} else {
    Write-Host "✓ No hay entorno anterior" -ForegroundColor Green
}

# Paso 3: Crear nuevo entorno virtual con Python 3.11
Write-Host ""
Write-Host "[3/7] Creando nuevo entorno virtual..." -ForegroundColor Yellow
py -3.11 -m venv .venv
if ($?) {
    Write-Host "✓ Entorno virtual creado" -ForegroundColor Green
} else {
    Write-Host "✗ Error al crear entorno virtual" -ForegroundColor Red
    exit 1
}

# Paso 4: Activar entorno virtual
Write-Host ""
Write-Host "[4/7] Activando entorno virtual..." -ForegroundColor Yellow
.\.venv\Scripts\activate
Write-Host "✓ Entorno activado" -ForegroundColor Green

# Paso 5: Actualizar pip
Write-Host ""
Write-Host "[5/7] Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✓ pip actualizado" -ForegroundColor Green

# Paso 6: Instalar dependencias básicas
Write-Host ""
Write-Host "[6/7] Instalando dependencias básicas..." -ForegroundColor Yellow
Write-Host "    - Flask, psycopg2, numpy, opencv-python, Pillow, cloudinary..." -ForegroundColor Gray
pip install Flask psycopg2 numpy opencv-python Pillow cloudinary --quiet

if ($?) {
    Write-Host "✓ Dependencias básicas instaladas" -ForegroundColor Green
} else {
    Write-Host "✗ Error al instalar dependencias" -ForegroundColor Red
    exit 1
}

# Paso 7: Instrucciones para dlib
Write-Host ""
Write-Host "[7/7] Instalación de dlib..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SIGUIENTE PASO MANUAL" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Descarga el wheel de dlib desde:" -ForegroundColor Yellow
Write-Host "   https://github.com/z-mahmud22/Dlib_Windows_Python3.x" -ForegroundColor White
Write-Host ""
Write-Host "2. Busca el archivo:" -ForegroundColor Yellow
Write-Host "   dlib-19.24.1-cp311-cp311-win_amd64.whl" -ForegroundColor White
Write-Host ""
Write-Host "3. Descárgalo a tu carpeta de Descargas" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Luego ejecuta estos comandos:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   .\.venv\Scripts\activate" -ForegroundColor Cyan
Write-Host "   pip install `"C:\Users\cance\Downloads\dlib-19.24.1-cp311-cp311-win_amd64.whl`"" -ForegroundColor Cyan
Write-Host "   pip install face_recognition" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Verifica con:" -ForegroundColor Yellow
Write-Host "   python -c `"import face_recognition; print('✓ Biometría lista')`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "✓ Script completado. Sigue los pasos manuales arriba." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan


@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 🚨 EMERGENCIA - IP PÚBLICA COMPROMETIDA
echo ========================================
echo.
echo ⚠️  CRÍTICO: Se ha subido IP pública al repositorio
echo 🌐 Información sensible: IP pública en commits
echo 📅 Necesita limpieza inmediata del historial
echo.
echo 🛡️  ACCIONES DE SEGURIDAD INMEDIATAS:
echo.

echo 1️⃣ Verificando archivos con IPs públicas...
echo.

REM Buscar archivos que puedan contener IPs públicas
findstr /r /n "79\.117\.198\.163" *.bat *.py *.js *.md 2>nul
if %errorlevel% equ 0 (
    echo ❌ Se encontraron referencias a IP pública
) else (
    echo ✅ No se encontraron referencias directas
)

echo.
echo 2️⃣ Revisando commits recientes...
git log --oneline -10

echo.
echo ========================================
echo 🔥 OPCIONES DE LIMPIEZA
echo ========================================
echo.
echo A) Revertir último commit (si la IP está solo ahí)
echo B) Purga completa del historial (como con las claves)
echo C) Editar commits específicos
echo.
echo ⚠️  ADVERTENCIA: Cualquier opción reescribirá el historial
echo.

set /p choice="¿Qué opción prefieres? (A/B/C): "

if /i "%choice%"=="A" goto revert_last
if /i "%choice%"=="B" goto full_purge  
if /i "%choice%"=="C" goto interactive_edit
goto end

:revert_last
echo.
echo 🔄 Revirtiendo último commit...
git reset --hard HEAD~1
echo ✅ Último commit revertido
echo.
echo ⚠️  Necesitarás hacer force push: git push --force-with-lease origin main
goto end

:full_purge
echo.
echo 🔥 PURGA COMPLETA DEL HISTORIAL
echo ========================================
echo.
echo ⚠️  ADVERTENCIA: Esto eliminará TODA referencia a la IP
echo.
set /p confirm="¿Continuar con purga completa? (S/N): "
if /i not "%confirm%"=="S" goto end

echo.
echo 🔥 Iniciando purga del historial...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch -r ." --prune-empty --tag-name-filter cat -- --all
git filter-branch --force --tree-filter "find . -type f -exec sed -i 's/79\.117\.198\.163/[REDACTED_IP]/g' {} \;" HEAD

echo.
echo 🧹 Limpiando referencias...
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ✅ Purga completada
echo.
echo 📤 Para aplicar cambios al repositorio remoto:
echo git push --force-with-lease origin main
goto end

:interactive_edit
echo.
echo 🛠️  EDICIÓN INTERACTIVA
echo ========================================
echo.
echo Usa: git rebase -i HEAD~N (donde N es número de commits)
echo Cambia 'pick' por 'edit' en commits con IP
echo Edita archivos manualmente
echo git add . && git rebase --continue
echo.
goto end

:end
echo.
echo ========================================
echo ⚠️  PRÓXIMOS PASOS CRÍTICOS
echo ========================================
echo.
echo 1️⃣ Verificar que no queden referencias a la IP
echo 2️⃣ Hacer force push si es necesario
echo 3️⃣ Considerar cambiar configuración de red si es necesario
echo 4️⃣ Revisar todos los archivos antes del próximo commit
echo.
echo 🛡️  PREVENCIÓN FUTURA:
echo ✅ Siempre revisar commits antes de push
echo ✅ Usar variables de entorno para IPs
echo ✅ Usar placeholders en ejemplos
echo.
pause
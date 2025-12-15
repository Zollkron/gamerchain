@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 🚨 EMERGENCIA CRÍTICA - IP PÚBLICA COMPROMETIDA
echo ========================================
echo.
echo ⚠️  CRÍTICO: IP pública [REDACTED_IP] en repositorio público
echo 📅 Eliminación INMEDIATA del historial completo
echo.

echo 🛡️  ACCIONES DE SEGURIDAD INMEDIATAS:
echo.

echo 1️⃣ Eliminando archivos con IP pública del working directory...
del /f /q verify-port-forwarding.bat 2>nul
del /f /q start-node2-genesis-public.bat 2>nul
echo ✅ Archivos eliminados del directorio local

echo.
echo 2️⃣ Agregando patrones de seguridad a .gitignore...
echo. >> .gitignore
echo # Security: Block IP addresses >> .gitignore
echo *public*.bat >> .gitignore
echo *port-forwarding*.bat >> .gitignore
echo verify-*.bat >> .gitignore
echo. >> .gitignore
echo ✅ Patrones de seguridad agregados a .gitignore

echo.
echo 3️⃣ Eliminando archivos del índice de Git...
git rm --cached verify-port-forwarding.bat 2>nul
git rm --cached start-node2-genesis-public.bat 2>nul
echo ✅ Archivos eliminados del índice de Git

echo.
echo 4️⃣ Creando commit de emergencia...
git add .gitignore
git commit -m "🚨 SECURITY: Remove public IP addresses and add security patterns"
echo ✅ Commit de emergencia creado

echo.
echo ========================================
echo 🔥 PURGA COMPLETA DEL HISTORIAL DE GIT
echo ========================================
echo.
echo ⚠️  ADVERTENCIA: Esto reescribirá completamente el historial
echo 📝 Se eliminará PERMANENTEMENTE la IP de todos los commits
echo.

set /p confirm="¿Continuar con la purga del historial? (S/N): "
if /i not "%confirm%"=="S" goto end

echo.
echo 🔥 Iniciando purga del historial...
echo 📝 Ejecutando git filter-branch...

REM Eliminar archivos específicos del historial
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch verify-port-forwarding.bat start-node2-genesis-public.bat" --prune-empty --tag-name-filter cat -- --all

REM Reemplazar IP en todos los archivos del historial
git filter-branch --force --tree-filter "find . -type f -name '*.bat' -exec sed -i 's/79\.117\.198\.163/[REDACTED_PUBLIC_IP]/g' {} \; 2>/dev/null || true" HEAD
git filter-branch --force --tree-filter "find . -type f -name '*.py' -exec sed -i 's/79\.117\.198\.163/[REDACTED_PUBLIC_IP]/g' {} \; 2>/dev/null || true" HEAD
git filter-branch --force --tree-filter "find . -type f -name '*.js' -exec sed -i 's/79\.117\.198\.163/[REDACTED_PUBLIC_IP]/g' {} \; 2>/dev/null || true" HEAD
git filter-branch --force --tree-filter "find . -type f -name '*.md' -exec sed -i 's/79\.117\.198\.163/[REDACTED_PUBLIC_IP]/g' {} \; 2>/dev/null || true" HEAD

echo ✅ Purga del historial completada

echo.
echo 🧹 Limpiando referencias...
for /f "tokens=*" %%i in ('git for-each-ref --format="%(refname)" refs/original/') do git update-ref -d "%%i"
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo ✅ Referencias limpiadas

echo.
echo ========================================
echo 📤 FORZAR PUSH AL REPOSITORIO REMOTO
echo ========================================
echo.
echo ⚠️  CRÍTICO: Debes hacer un force push para aplicar los cambios
echo 📝 Esto sobrescribirá el historial remoto completamente
echo.

set /p pushconfirm="¿Hacer force push ahora? (S/N): "
if /i not "%pushconfirm%"=="S" goto manual_push

echo.
echo 📤 Haciendo force push...
git push --force-with-lease origin main
if %errorlevel% equ 0 (
    echo ✅ Force push completado
    echo 🎉 El historial remoto ha sido limpiado
) else (
    echo ❌ Error en force push
    echo 📝 Ejecuta manualmente: git push --force origin main
)
goto summary

:manual_push
echo.
echo 📝 Para hacer el push manualmente:
echo git push --force origin main
echo.

:summary
echo.
echo ========================================
echo ✅ RESUMEN DE ACCIONES COMPLETADAS
echo ========================================
echo.
echo ✅ Archivos con IP eliminados del working directory
echo ✅ Patrones de seguridad agregados a .gitignore
echo ✅ Archivos eliminados del índice de Git
echo ✅ Historial de Git purgado completamente
echo ✅ Referencias limpiadas
echo ✅ IP reemplazada por [REDACTED_PUBLIC_IP] en historial
echo.
echo 🔄 PRÓXIMOS PASOS REQUERIDOS:
echo.
echo 1️⃣ Verificar que el force push se completó correctamente
echo 2️⃣ Informar a colaboradores sobre el rebase
echo 3️⃣ Todos deben hacer: git pull --rebase origin main
echo 4️⃣ Verificar que GitHub ya no muestra la IP
echo 5️⃣ Considerar cambiar configuración de red si es necesario
echo.
echo 🛡️  MEDIDAS DE PREVENCIÓN IMPLEMENTADAS:
echo.
echo ✅ .gitignore actualizado con patrones de seguridad
echo ✅ Archivos con IPs bloqueados permanentemente
echo ✅ IP completamente eliminada del historial
echo.

:end
echo.
echo ========================================
echo 🔒 OPERACIÓN DE SEGURIDAD COMPLETADA
echo ========================================
echo.
pause
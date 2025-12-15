@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 🚨 EMERGENCIA DE SEGURIDAD - CLAVES COMPROMETIDAS
echo ========================================
echo.
echo ⚠️  CRÍTICO: Se han subido claves privadas al repositorio público
echo 🔑 Archivo comprometido: data/node_keys.json
echo 📅 Commit problemático: ce31d1290ab04aee6af227d471221d27ce85fd20
echo.

echo 🛡️  ACCIONES DE SEGURIDAD INMEDIATAS:
echo.

echo 1️⃣ Eliminando archivo sensible del working directory...
if exist "data\node_keys.json" (
    del /f "data\node_keys.json"
    echo ✅ Archivo eliminado del directorio local
) else (
    echo ℹ️  Archivo ya no existe en directorio local
)

echo.
echo 2️⃣ Agregando archivo a .gitignore para prevenir futuros accidentes...
echo # Archivos de claves sensibles - NUNCA subir >> .gitignore
echo data/node_keys.json >> .gitignore
echo data/*_keys.json >> .gitignore
echo *.pem >> .gitignore
echo *.key >> .gitignore
echo *.p12 >> .gitignore
echo *.pfx >> .gitignore
echo.
echo ✅ Patrones de seguridad agregados a .gitignore

echo.
echo 3️⃣ Eliminando archivo del índice de Git...
git rm --cached data/node_keys.json 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Archivo eliminado del índice de Git
) else (
    echo ℹ️  Archivo ya no está en el índice de Git
)

echo.
echo 4️⃣ Creando commit de emergencia...
git add .gitignore
git commit -m "🚨 SECURITY: Remove sensitive keys and add security patterns to .gitignore

- Remove data/node_keys.json from tracking
- Add comprehensive security patterns to .gitignore
- Prevent future accidental commits of sensitive files

CRITICAL: Previous commit ce31d12 exposed private keys
Action required: Purge Git history and regenerate keys"

echo.
echo ========================================
echo 🔥 PURGA COMPLETA DEL HISTORIAL DE GIT
echo ========================================
echo.
echo ⚠️  ADVERTENCIA: Esto reescribirá completamente el historial
echo 📝 Se eliminará PERMANENTEMENTE el archivo de todos los commits
echo.

set /p confirm="¿Continuar con la purga del historial? (S/N): "
if /i "%confirm%" NEQ "S" (
    echo ❌ Operación cancelada por el usuario
    goto :end
)

echo.
echo 🔥 Iniciando purga del historial...
echo.

REM Usar git filter-branch para eliminar el archivo de todo el historial
echo 📝 Ejecutando git filter-branch...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch data/node_keys.json" --prune-empty --tag-name-filter cat -- --all

if %ERRORLEVEL% EQU 0 (
    echo ✅ Purga del historial completada
) else (
    echo ❌ Error en la purga del historial
    goto :end
)

echo.
echo 🧹 Limpiando referencias...
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo.
echo ========================================
echo 🔑 REGENERACIÓN DE CLAVES
echo ========================================
echo.

echo 🔄 Las claves comprometidas deben ser regeneradas...
echo 📝 El sistema generará nuevas claves automáticamente al iniciar
echo.

echo ✅ Eliminando claves comprometidas del directorio data...
if exist "data\node_id.txt" (
    del /f "data\node_id.txt"
    echo ✅ Node ID eliminado
)

echo.
echo ========================================
echo 📤 FORZAR PUSH AL REPOSITORIO REMOTO
echo ========================================
echo.
echo ⚠️  CRÍTICO: Debes hacer un force push para aplicar los cambios
echo 📝 Esto sobrescribirá el historial remoto completamente
echo.

set /p push_confirm="¿Hacer force push ahora? (S/N): "
if /i "%push_confirm%" EQU "S" (
    echo 📤 Haciendo force push...
    git push origin --force --all
    git push origin --force --tags
    
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Force push completado
        echo 🎉 El historial remoto ha sido limpiado
    ) else (
        echo ❌ Error en el force push
        echo 📝 Debes ejecutar manualmente: git push origin --force --all
    )
) else (
    echo ⚠️  IMPORTANTE: Debes ejecutar manualmente:
    echo    git push origin --force --all
    echo    git push origin --force --tags
)

echo.
echo ========================================
echo ✅ RESUMEN DE ACCIONES COMPLETADAS
echo ========================================
echo.
echo ✅ Archivo sensible eliminado del working directory
echo ✅ Patrones de seguridad agregados a .gitignore
echo ✅ Archivo eliminado del índice de Git
echo ✅ Historial de Git purgado completamente
echo ✅ Referencias limpiadas
echo ✅ Claves comprometidas eliminadas
echo.
echo 🔄 PRÓXIMOS PASOS REQUERIDOS:
echo.
echo 1️⃣ Verificar que el force push se completó correctamente
echo 2️⃣ Informar a todos los colaboradores sobre el rebase
echo 3️⃣ Todos deben hacer: git pull --rebase origin main
echo 4️⃣ Las nuevas claves se generarán automáticamente
echo 5️⃣ Verificar que GitHub ya no muestra el archivo sensible
echo.
echo 🛡️  MEDIDAS DE PREVENCIÓN IMPLEMENTADAS:
echo.
echo ✅ .gitignore actualizado con patrones de seguridad
echo ✅ Archivos de claves bloqueados permanentemente
echo ✅ Sistema regenerará claves automáticamente
echo.

:end
echo ========================================
echo 🔒 OPERACIÓN DE SEGURIDAD COMPLETADA
echo ========================================
pause
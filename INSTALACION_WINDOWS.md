# Instalación de PlayerGold en Windows

## Requisitos Previos

1. **Python 3.9 o superior**
   - Descargar desde: https://python.org/downloads/
   - ⚠️ **IMPORTANTE**: Durante la instalación, marcar la casilla "Add Python to PATH"

2. **Requisitos de Hardware**
   - 4GB VRAM (para operación de nodo IA)
   - 4+ núcleos CPU
   - 8GB RAM

## Instalación Rápida

### Opción 1: Instalación Automática
1. Descargar o clonar el proyecto
2. Hacer doble clic en `install.bat`
3. Esperar a que termine la instalación
4. Hacer doble clic en `start.bat` para ejecutar

### Opción 2: Instalación Manual
1. Abrir PowerShell o CMD en la carpeta del proyecto
2. Ejecutar: `pip install -r requirements.txt`
3. Copiar archivo de configuración: `copy .env.example .env`
4. Ejecutar: `python main.py`

## Verificación de la Instalación

Para verificar que todo está instalado correctamente:

```cmd
python -c "import torch, transformers, fastapi; print('✅ Dependencias instaladas correctamente')"
```

## Solución de Problemas Comunes

### Error: "Python no se reconoce como comando"
- **Solución**: Reinstalar Python marcando "Add Python to PATH"
- O agregar manualmente Python al PATH del sistema

### Error: "No se puede cargar el archivo... ejecución de scripts está deshabilitada"
- **Solución**: Ejecutar en PowerShell como administrador:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

### Error de dependencias faltantes
- **Solución**: Ejecutar `install.bat` o instalar manualmente:
  ```cmd
  pip install torch transformers fastapi
  ```

### Error de memoria insuficiente durante instalación
- **Solución**: Instalar dependencias una por una:
  ```cmd
  pip install torch
  pip install transformers
  pip install fastapi
  ```

## Estructura del Proyecto

```
gamerchain/
├── install.bat          # Instalador automático
├── start.bat           # Ejecutor del proyecto
├── main.py             # Archivo principal
├── requirements.txt    # Dependencias Python
├── .env.example       # Configuración de ejemplo
├── .env               # Tu configuración (se crea automáticamente)
└── src/               # Código fuente
```

## Comandos Útiles

- **Instalar dependencias**: `install.bat` o `pip install -r requirements.txt`
- **Ejecutar proyecto**: `start.bat` o `python main.py`
- **Verificar instalación**: `python -c "import torch; print('OK')"`
- **Ver ayuda**: `python main.py --help`

## Configuración

El archivo `.env` contiene la configuración del proyecto. Se crea automáticamente desde `.env.example` durante la instalación.

Principales configuraciones:
- `ENVIRONMENT=development` - Modo de desarrollo
- `DEBUG=true` - Activar debug
- `NETWORK__P2P_PORT=8333` - Puerto P2P
- `NETWORK__API_PORT=8080` - Puerto API

## Soporte

Si tienes problemas:
1. Verificar que Python 3.9+ está instalado
2. Verificar que pip funciona: `pip --version`
3. Ejecutar `install.bat` para reinstalar dependencias
4. Revisar los logs en caso de errores

---

**PlayerGold** - Blockchain para Gaming desarrollado por Zollkron
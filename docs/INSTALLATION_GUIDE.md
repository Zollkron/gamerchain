# 🚀 Guía de Instalación - PlayerGold

## 📋 Requisitos del Sistema

### Requisitos Mínimos
- **Sistema Operativo**: Windows 10/11, Linux, macOS
- **Python**: 3.8 o superior
- **Node.js**: 16 o superior (para wallet)
- **RAM**: 4GB mínimo
- **Almacenamiento**: 2GB libres

### Requisitos Recomendados
- **RAM**: 8GB o más (para minería IA)
- **GPU**: Compatible con CUDA (opcional, para IA avanzada)
- **CPU**: 4+ núcleos
- **Conexión**: Internet estable

## 🛠️ Instalación Rápida (Windows)

### Paso 1: Instalar Dependencias del Sistema

1. **Python 3.8+**
   - Descarga desde: https://python.org/downloads/
   - ⚠️ **IMPORTANTE**: Marca "Add Python to PATH" durante la instalación

2. **Node.js 16+** (para wallet)
   - Descarga desde: https://nodejs.org/
   - Selecciona la versión LTS (recomendada)

### Paso 2: Configurar PlayerGold

```bash
# Clonar o descargar el proyecto
git clone https://github.com/tu-repo/playergold.git
cd playergold

# Ejecutar setup automático
setup.bat
```

### Paso 3: Seleccionar Tipo de Instalación

El script `setup.bat` te dará estas opciones:

1. **Setup Completo** - Backend + Wallet (recomendado)
2. **Solo Backend** - Solo nodo blockchain
3. **Solo Wallet** - Solo interfaz de usuario
4. **Verificar Sistema** - Comprobar dependencias
5. **Limpiar e Instalar Todo** - Instalación desde cero

## 🐧 Instalación en Linux/macOS

### Instalar Dependencias

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nodejs npm

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm

# macOS (con Homebrew)
brew install python3 node
```

### Configurar PlayerGold

```bash
# Clonar proyecto
git clone https://github.com/tu-repo/playergold.git
cd playergold

# Instalar dependencias Python
pip3 install -r requirements.txt

# Instalar dependencias Wallet
cd wallet
npm install
npm run build
cd ..
```

## 🎮 Iniciar PlayerGold

### Opción 1: Todo en Uno (Recomendado)
```bash
# Windows
cd wallet
build-complete.bat

# Linux/macOS
cd wallet
npm start
```

### Opción 2: Por Separado

#### Backend (Nodo Blockchain)
```bash
python scripts/start_multinode_network.py
```

#### Wallet (Interfaz)
```bash
cd wallet
npm start
```

## 🔧 Solución de Problemas

### "Python no encontrado"
- Reinstala Python desde python.org
- Asegúrate de marcar "Add Python to PATH"
- Reinicia tu computadora

### "Node.js no encontrado"
- Instala Node.js desde nodejs.org
- Selecciona la versión LTS
- Reinicia tu terminal

### "Error al instalar dependencias"
- Verifica tu conexión a Internet
- Ejecuta como administrador (Windows) o con sudo (Linux)
- Actualiza pip: `python -m pip install --upgrade pip`

### "Wallet no compila"
- Verifica que Node.js esté instalado
- Limpia cache: `npm cache clean --force`
- Elimina node_modules y reinstala: `rm -rf node_modules && npm install`

### "Error de GPU/CUDA"
- Es normal si no tienes GPU compatible
- PlayerGold funciona sin GPU (modo CPU)
- Para IA avanzada, instala drivers CUDA apropiados

## 📚 Próximos Pasos

Después de la instalación:

1. **Configurar Red Testnet**: Lee `docs/TESTNET_SETUP_GUIDE.md`
2. **Crear tu Primera Wallet**: Abre la aplicación y sigue el asistente
3. **Obtener Tokens de Prueba**: Usa el faucet integrado
4. **Empezar a Minar**: Descarga un modelo IA y comienza

## 🆘 Soporte

Si tienes problemas:

1. **Verifica el sistema**: Ejecuta `setup.bat` → opción 4
2. **Revisa logs**: Carpeta `logs/` para errores detallados
3. **Documentación**: Lee `docs/DEVELOPMENT_HISTORY.md`
4. **Comunidad**: PlayerGold es código abierto

---

**¡Bienvenido a la revolución del gaming blockchain!** 🎮⛏️

*PlayerGold Team - Hecho por gamers para gamers*
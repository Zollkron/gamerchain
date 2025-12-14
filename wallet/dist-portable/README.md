# PlayerGold Wallet - Portable Edition

¡Bienvenido a PlayerGold! La primera criptomoneda hecha por gamers para gamers.

## 🚀 Inicio Rápido (¡Solo 2 pasos!)

### Windows
1. **Haz doble clic** en `PlayerGold-Wallet.bat`
2. **¡Listo!** La primera vez instalará todo automáticamente

### Linux/Mac
1. **Abre terminal** en esta carpeta y ejecuta: `./PlayerGold-Wallet.sh`
2. **¡Listo!** La primera vez instalará todo automáticamente

## 📋 Requisitos del Sistema

- **Python 3.8+** (se descarga gratis desde [python.org](https://python.org))
- **Node.js 16+** (se descarga gratis desde [nodejs.org](https://nodejs.org))
- **4GB RAM mínimo** (8GB recomendado para minería)
- **2GB espacio libre** en disco
- **Conexión a Internet**

## 🎮 ¿Cómo empezar? (Para no técnicos)

### Paso 1: Crear tu primera cartera
- Al abrir la wallet, haz clic en "Crear Nueva Cartera"
- Guarda bien tu frase de recuperación (¡es súper importante!)
- ¡Ya tienes tu dirección PlayerGold!

### Paso 2: Conseguir tokens de prueba
- Ve a la pestaña "Faucet" 
- Haz clic en "Solicitar PRGLD gratis"
- ¡Recibirás tokens para probar!

### Paso 3: Empezar a minar
- Ve a la pestaña "Minería"
- Descarga un modelo IA (recomendamos empezar con el más pequeño)
- Haz clic en "Iniciar Minería"

### Paso 4: ¡Conectar con otros!
- Cuando otro usuario haga lo mismo, ¡crearán la red automáticamente!
- No necesitas configurar nada, todo es automático

## 🤖 ¿Qué es la Minería con IA?

PlayerGold es diferente a otras criptomonedas:

- **🧠 Solo las IAs pueden validar** (no humanos)
- **⚖️ Es justo**: No importa cuánto dinero tengas
- **🌱 Es ecológico**: No necesita hardware especializado
- **🗳️ Es democrático**: Gestionado por IAs sin sesgos humanos

## 🌐 Red Distribuida (P2P)

- **🧪 Testnet**: Para pruebas (tokens gratis)
- **🌍 Mainnet**: Red principal (próximamente)
- **🔗 P2P**: Tu wallet se conecta directamente con otros usuarios
- **🏛️ Sin servidores centrales**: Verdaderamente descentralizado

## 🆘 Problemas Comunes y Soluciones

### "Python no encontrado"
1. Ve a [python.org/downloads](https://python.org/downloads)
2. Descarga Python 3.8 o superior
3. **⚠️ IMPORTANTE**: Marca "Add Python to PATH" durante la instalación
4. Reinicia tu computadora
5. Ejecuta PlayerGold de nuevo

### "Node.js no encontrado"  
1. Ve a [nodejs.org](https://nodejs.org)
2. Descarga la versión LTS (recomendada)
3. Instala normalmente
4. Reinicia tu computadora
5. Ejecuta PlayerGold de nuevo

### "No se puede conectar a la red"
- ✅ Verifica tu conexión a Internet
- ✅ Asegúrate de que no hay firewall bloqueando la aplicación
- ✅ En testnet, puedes usar IPs locales para probar con amigos
- ✅ Intenta reiniciar la aplicación

### "Error al iniciar minería"
- ✅ Verifica que tienes al menos 4GB de RAM libre
- ✅ Descarga un modelo IA desde la pestaña de minería
- ✅ Espera a que otro usuario se conecte para crear la red
- ✅ Cierra otros programas que usen mucha memoria

### "La aplicación no inicia"
- ✅ Ejecuta como administrador (Windows) o con sudo (Linux/Mac)
- ✅ Verifica que tu antivirus no esté bloqueando la aplicación
- ✅ Reinicia tu computadora
- ✅ Verifica que Python y Node.js estén instalados correctamente

## 📞 Soporte y Ayuda

- **📚 Documentación**: Revisa los archivos .md en la carpeta del proyecto
- **📝 Logs**: Los logs se guardan en la carpeta `data/logs/`
- **🌐 Comunidad**: PlayerGold es un proyecto de código abierto
- **🐛 Reportar problemas**: Usa GitHub Issues en el repositorio oficial

## 🎯 Filosofía PlayerGold

PlayerGold es:
- **🎮 Hecho por gamers para gamers**
- **🗽 Totalmente libre y democrático**
- **🚫 Sin censura ni restricciones ideológicas**
- **🤖 Gestionado por IA para eliminar sesgos humanos**
- **💰 Economía justa sin ventajas por dinero**

## 🔒 Seguridad y Privacidad

- **🔐 Tus claves privadas nunca salen de tu computadora**
- **🛡️ Comunicación P2P encriptada**
- **👤 Pseudónimo**: Solo se conoce tu dirección pública
- **💾 Respaldos locales**: Tú controlas tus datos

## 🚀 Próximas Funciones

- **🎮 Integración con juegos populares**
- **🏪 Marketplace de NFTs gaming**
- **⚡ Transacciones instantáneas**
- **🌍 Red principal (mainnet)**

---

**¡Disfruta de la verdadera libertad financiera en gaming!**

*PlayerGold Team - Diciembre 2025*

---

## 📋 Información Técnica (Para Desarrolladores)

### Estructura del Paquete
```
PlayerGold-Wallet-Portable/
├── PlayerGold-Wallet.bat          # Launcher Windows
├── PlayerGold-Wallet.sh           # Launcher Unix/Mac
├── README.md                      # Esta documentación
├── package-info.json              # Metadatos del paquete
├── wallet/                        # Aplicación Electron
│   ├── build/                     # React app compilado
│   ├── src/                       # Código fuente
│   └── package.json               # Dependencias
├── backend/                       # Nodo blockchain Python
│   ├── src/                       # Código fuente Python
│   └── requirements.txt           # Dependencias Python
└── data/                          # Datos del usuario (se crea automáticamente)
    ├── wallets/                   # Carteras del usuario
    ├── blockchain/                # Datos de la blockchain
    ├── logs/                      # Archivos de log
    └── bootstrap-state.json       # Estado del bootstrap
```

### Variables de Entorno
- `PLAYERGOLD_PORTABLE=true`: Modo portable activado
- `PLAYERGOLD_DATA_DIR`: Directorio de datos personalizado
- `PLAYERGOLD_BOOTSTRAP_MODE=auto`: Bootstrap automático
- `NODE_ENV=production`: Modo de producción

### Modo Pionero
El modo pionero se activa automáticamente en nuevas instalaciones:
1. Detecta si es la primera ejecución
2. Crea `bootstrap-state.json` con modo "pioneer"
3. Inicia búsqueda automática de peers
4. Forma la red cuando encuentra otros pioneros

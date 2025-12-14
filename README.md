# PlayerGold ($PRGLD) - GamerChain Blockchain

**Desarrollado por**: Zollkron  
**Web oficial**: https://playergold.es  
**Repositorio**: https://github.com/Zollkron/gamerchain

PlayerGold es una blockchain revolucionaria para el ecosistema gaming, construida sobre la tecnología GamerChain, implementando un mecanismo de consenso Proof-of-AI-Participation (PoAIP). El sistema está diseñado por gamers, para gamers, proporcionando pagos sin censura con comisiones justas y gobernanza democrática gestionada exclusivamente por inteligencia artificial.

## ⚠️ DISCLAIMER LEGAL / DESCARGO DE RESPONSABILIDAD

**⚠️ LEA ATENTAMENTE ANTES DE USAR ESTE SOFTWARE ⚠️**

El desarrollador (Zollkron) **NO se hace responsable de manera alguna** del uso que cualquier persona o entidad pueda hacer de este software, blockchain o token. 

**Condiciones importantes:**

1. Este proyecto se desarrolla como **hobby personal**, sin obligaciones contractuales con nadie
2. El desarrollador se limita únicamente a programar y publicar el código
3. **Cualquier uso de esta herramienta se realiza EXCLUSIVAMENTE BAJO SU PROPIA RESPONSABILIDAD**
4. El desarrollador NO está obligado a seguir dictámenes o regulaciones de ninguna jurisdicción
5. La blockchain es completamente auditable por cualquier persona en cualquier momento
6. Los usuarios son responsables de cumplir con las leyes de sus respectivas jurisdicciones

**Para información legal completa, consulte [PROJECT_INFO.md](PROJECT_INFO.md)**

## 🎮 Visión

**"Hecho por gamers para gamers, totalmente libre, democrático y sin censura"**

PlayerGold busca eliminar el sesgo humano y la corrupción de la gobernanza blockchain utilizando nodos de IA distribuidos para el consenso. Esto asegura una gestión justa, transparente e ideológicamente neutral de la economía gaming.

## 🚀 Inicio Rápido

### Instalación Automática (Windows)
```bash
# 1. Descargar o clonar el proyecto
git clone https://github.com/Zollkron/gamerchain.git
cd gamerchain

# 2. Ejecutar setup automático
setup.bat
```

### Instalación Manual (Linux/macOS)
```bash
# 1. Instalar dependencias
pip install -r requirements.txt
cd wallet && npm install && npm run build

# 2. Iniciar nodo
python scripts/start_multinode_network.py

# 3. Iniciar wallet (en otra terminal)
cd wallet && npm start
```

## 🏗️ Arquitectura

### Componentes Principales

- **🤖 Nodos IA**: Distribuidos ejecutando modelos certificados (Gemma 3 4B, Mistral 3B, Qwen 3 4B)
- **⚖️ Consenso PoAIP**: Proof-of-AI-Participation - solo IAs validan bloques
- **💰 Economía Justa**: 90% validadores IA, 10% stakers - sin ventaja económica
- **🔥 Gestión de Fees**: 60% quemado → 0% (deflación progresiva), 30% → 60% mantenimiento
- **🎮 Gaming APIs**: SDKs para Unity, Unreal, JavaScript y más

### Características Implementadas

- ✅ **Red Multi-Nodo**: Sistema P2P con bootstrap automático
- ✅ **Wallet Electron**: Interfaz completa con minería IA integrada
- ✅ **Consenso IA**: 66% threshold, validación cruzada entre nodos
- ✅ **Sistema de Halving**: Redistribución automática de fees cada 100k bloques
- ✅ **Modo Pionero**: Auto-descubrimiento y formación de red
- ✅ **Testnet Segura**: Configuración sin exponer información sensible
- ✅ **Build Unificado**: Script único para todos los tipos de compilación
- ✅ **Network Coordinator**: Sistema centralizado con respaldo distribuido para mapeo de red
- ✅ **Validación Obligatoria**: Prevención 100% de forks mediante validación obligatoria del coordinador

## 📁 Estructura del Proyecto

```
gamerchain/
├── 🚀 setup.bat                    # Setup automático completo
├── 📊 monitor_genesis_node.bat     # Monitor de red en tiempo real
├── 📋 requirements.txt             # Dependencias Python
├── 
├── 📂 src/                         # Código fuente del blockchain
│   ├── blockchain/                 # Core blockchain (bloques, transacciones)
│   ├── consensus/                  # PoAIP, bootstrap, halving
│   ├── p2p/                       # Red P2P y descubrimiento
│   ├── ai_nodes/                   # Carga y verificación de modelos IA
│   ├── network_coordinator/        # Coordinador de red centralizado
│   └── api/                       # APIs REST y GraphQL
├── 
├── 📂 wallet/                      # Wallet Electron
│   ├── 🔨 build-complete.bat      # Build unificado (dev/prod/portable/installer)
│   ├── src/                       # Código fuente React + Electron
│   └── scripts/build-portable.js  # Generador de paquetes portables
├── 
├── 📂 scripts/                     # Scripts de utilidad
│   ├── start_multinode_network.py # Iniciar red multi-nodo
│   ├── start_network_coordinator.py # Iniciar coordinador de red
│   ├── setup_testnet_genesis.py   # Configurar testnet segura
│   └── launch_testnet.py          # Lanzar testnet completa
├── 
├── 📂 docs/                        # Documentación consolidada
│   ├── INSTALLATION_GUIDE.md      # Guía de instalación completa
│   ├── TESTNET_SETUP_GUIDE.md     # Configuración de testnet segura
│   └── DEVELOPMENT_HISTORY.md     # Historial de desarrollo
├── 
├── 📂 tests/                       # Tests unitarios y de integración
│   ├── test_*.py                  # Tests unitarios Python
│   ├── integration/               # Tests de integración
│   └── wallet/src/**/__tests__/   # Tests del wallet
└── 
└── 📂 .kiro/specs/                 # Especificaciones de features
    ├── auto-bootstrap-p2p/        # Spec bootstrap automático
    ├── distributed-ai-nodes/      # Spec nodos IA distribuidos
    ├── halving-fee-redistribution/ # Spec redistribución de fees
    └── network-coordinator/        # Spec coordinador de red
```

## 🌐 Network Coordinator

### Arquitectura Híbrida Centralizada-Distribuida

El Network Coordinator es un sistema innovador que combina las ventajas de la centralización con la robustez de la distribución:

**Coordinador Principal (playergold.es)**
- Mantiene registro cifrado de todos los nodos activos
- Procesa KeepAlive messages cada 60 segundos
- Detecta y resuelve forks automáticamente
- Proporciona mapas de red actualizados

**Respaldo Distribuido**
- Nodos de backup mantienen copias del registro
- Failover automático si el coordinador principal falla
- Sincronización continua entre respaldos
- Los wallets pueden obtener mapas desde cualquier backup

### Características Clave

- **🔒 Cifrado AES-256**: Toda la información de nodos está cifrada
- **📍 Geolocalización**: Cálculo de proximidad para conexiones óptimas
- **🔄 KeepAlive Automático**: Monitoreo continuo del estado de nodos
- **🚫 Prevención de Forks**: Detección y resolución automática de divisiones
- **🌍 Alcance Global**: Funciona desde cualquier ubicación geográfica
- **⚡ Failover Rápido**: Cambio automático a backups en caso de falla

### Flujo de Funcionamiento

1. **🔒 Validación Obligatoria**: Wallet DEBE conectarse al coordinador antes de operar
2. **📥 Descarga de Mapa**: Obtención del net_map.json cifrado y verificado
3. **✅ Verificación de Integridad**: Validación de firmas y timestamps
4. **🚀 Registro de Nodo**: Wallet se registra automáticamente al iniciar
5. **📡 KeepAlive Continuo**: Envío de estado cada 60 segundos
6. **🗺️ Mapa de Red**: Descarga periódica de nodos cercanos
7. **🔍 Detección de Forks**: Monitoreo de altura de blockchain
8. **⚖️ Resolución Automática**: Selección de cadena canónica
9. **💾 Backup Distribuido**: Sincronización con nodos de respaldo

### Prevención 100% de Forks

**Regla Crítica**: Sin conexión al coordinador = Sin operación de wallet

- **Primera Ejecución**: OBLIGATORIO conectarse a playergold.es
- **Ejecuciones Posteriores**: Puede usar net_map.json local válido
- **Modo Offline**: Solo si tiene mapa válido y se conecta a nodos registrados
- **Modo Pionero**: Solo si el coordinador confirma que puede crear blockchain

## 🌐 Redes

### Testnet (Red de Pruebas)

Red para desarrollo y pruebas con tokens ficticios:
- Tokens sin valor real
- Blockchain independiente de mainnet
- Reseteable si es necesario
- Acceso público para pruebas

### Mainnet (Red Principal)

Red de producción con tokens reales:
- Tokens con valor real ($PRGLD)
- Blockchain permanente e inmutable
- Transacciones definitivas

### Escalabilidad y Quorum

**Principio**: "Donde hayan dos reunidos, mi espíritu está con ellos"

- **Quorum fijo**: 66% (dos tercios) de los nodos activos
- **Mínimo de nodos**: 2 nodos para funcionamiento
- **Escalabilidad dinámica**: Se adapta automáticamente al número de nodos
- **Tolerancia a fallos**: Hasta 33% de nodos pueden fallar sin afectar consenso

Ejemplos:
- 2 nodos → Quorum: 2 (100%)
- 3 nodos → Quorum: 2 (66%)
- 10 nodos → Quorum: 7 (66%)
- 100 nodos → Quorum: 67 (66%)
- 1000 nodos → Quorum: 667 (66%)

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.9 o superior
- 4GB VRAM (para operación de nodo IA)
- 4+ núcleos CPU
- 8GB RAM

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Zollkron/gamerchain.git
   cd gamerchain
   ```

2. **Configurar el entorno**
   ```bash
   make setup
   make dev-install
   ```

3. **Configurar la aplicación**
   ```bash
   cp .env.example .env
   # Editar .env con tu configuración
   ```

4. **Ejecutar PlayerGold**
   ```bash
   make run
   # o
   python -m src.main
   ```

### Comandos de Desarrollo

```bash
# Instalar dependencias
make install          # Dependencias de producción
make dev-install      # Dependencias de desarrollo

# Desarrollo
make run             # Ejecutar la aplicación
make test            # Ejecutar suite de tests
make lint            # Ejecutar verificaciones de linting
make format          # Formatear código con black
make clean           # Limpiar artefactos de build

# Gestión de proyecto
make setup           # Configuración inicial del proyecto
make check-structure # Ver estructura del proyecto
```

## 📁 Estructura del Proyecto

```
gamerchain/
├── src/                    # Código fuente principal
│   ├── blockchain/         # Core blockchain y consenso PoAIP
│   ├── consensus/          # Sistemas de consenso y tolerancia a fallos
│   ├── ai_nodes/          # Gestión y validación de modelos IA
│   ├── p2p/               # Red peer-to-peer
│   ├── reputation/        # Sistema de reputación
│   ├── monitoring/        # Monitoreo y alertas
│   ├── api/               # REST/GraphQL API para juegos
│   ├── utils/             # Utilidades comunes y logging
│   ├── main.py            # Punto de entrada de la aplicación
│   └── cli.py             # Interfaz de línea de comandos
├── wallet/                # Wallet de escritorio (Electron)
├── web/                   # Landing page y interfaz web
├── explorer/              # Explorador de blockchain
├── config/                # Gestión de configuración
│   ├── config.py          # Clases de configuración
│   └── default.yaml       # Configuración por defecto
├── tests/                 # Suite de tests
├── docs/                  # Documentación
├── examples/              # Ejemplos de uso
├── requirements.txt       # Dependencias Python
├── pyproject.toml        # Configuración del proyecto
├── PROJECT_INFO.md       # Información legal y del proyecto
└── Makefile              # Comandos de desarrollo
```

## 🔧 Configuración

PlayerGold usa un sistema de configuración jerárquico:

1. **Valores por defecto** en `config/config.py`
2. **Archivos YAML** como `config/default.yaml`
3. **Variables de entorno** desde archivo `.env`
4. **Argumentos de línea de comandos**

### Opciones de Configuración Clave

```yaml
# Configuración de red
network:
  p2p_port: 8333
  api_port: 8080
  max_peers: 50
  quorum_percentage: 0.66  # 66% quorum

# Configuración IA
ai:
  models_dir: "./models"
  challenge_timeout: 0.1
  min_validators: 3

# Configuración blockchain
blockchain:
  data_dir: "./data"
  block_time: 10
  reward_distribution:
    ai_nodes: 0.9
    stakers: 0.1
```

## 🤖 Modelos IA

PlayerGold soporta modelos de IA certificados con hashes SHA-256 verificados:

- **Gemma 3 4B**: Optimizado para desafíos matemáticos
- **Mistral 3B**: Inferencia y validación eficiente
- **Qwen 3 4B**: Soporte multilingüe y robustez

### Verificación de Modelos

Todos los modelos IA pasan por verificación estricta:
1. Validación de hash SHA-256 contra lista certificada
2. Pruebas de capacidad para operaciones blockchain
3. Benchmarking de rendimiento para respuesta <300ms

## 🎯 Mecanismo de Consenso (PoAIP)

Proof-of-AI-Participation asegura que solo inteligencia artificial puede participar en consenso:

1. **Generación de Desafíos**: Problemas matemáticos que requieren capacidades IA
2. **Envío de Soluciones**: IAs resuelven desafíos en <300ms
3. **Validación Cruzada**: Mínimo 3 IAs validan cada solución
4. **Distribución de Recompensas**: Recompensas iguales para todas las IAs participantes

## 🛡️ Características de Seguridad

- **Integridad de Modelos**: Verificación SHA-256 de modelos IA
- **Ejecución Aislada**: Ejecución de modelos IA en sandbox
- **Validación Cruzada**: Verificación múltiple de soluciones por IAs
- **Sistema de Reputación**: Seguimiento de comportamiento y penalizaciones
- **Encriptación de Red**: TLS 1.3 para todas las comunicaciones
- **Tolerancia a Fallos**: Recuperación automática de nodos caídos
- **Defensa contra Ataques**: Detección y mitigación automática

## 🧪 Testing

Ejecutar la suite completa de tests:

```bash
# Ejecutar todos los tests
make test

# Ejecutar categorías específicas de tests
pytest tests/test_infrastructure.py -v
pytest tests/test_blockchain.py -v
pytest tests/test_ai_nodes.py -v
pytest tests/test_consensus.py -v
pytest tests/test_fault_tolerance.py -v
```

## 🌐 Landing Page

PlayerGold cuenta con una landing page moderna y responsive:

```bash
# Ver la landing page localmente
cd web
python -m http.server 8000
# Visitar http://localhost:8000
```

Características:
- **Detección Automática de SO**: Recomienda la descarga correcta del wallet
- **Diseño Moderno**: Tema oscuro con animaciones suaves y gradientes
- **Responsive**: Optimizado para escritorio, tablet y móvil
- **Declaración de Misión**: Presentación clara de valores y objetivos
- **Visión General Tecnológica**: Explicación del consenso PoAIP y GamerChain

Ver [web/README.md](web/README.md) para instrucciones de despliegue.

## 📚 Documentación

- [PROJECT_INFO.md](PROJECT_INFO.md) - Información legal y del proyecto
- [Technical Whitepaper](docs/Technical_Whitepaper.md) - Arquitectura detallada
- [Fault Tolerance](docs/Fault_Tolerance_Implementation_Summary.md) - Sistema de tolerancia a fallos
- [P2P Network](docs/P2P_Network_Implementation.md) - Red peer-to-peer
- [Game Integration API](docs/Game_Integration_API.md) - Guía de integración para juegos

## 🤝 Contribuciones

Este es un proyecto de código abierto desarrollado como hobby. Las contribuciones son bienvenidas:

1. Fork el repositorio
2. Crea una rama de feature
3. Realiza tus cambios
4. Añade tests para nueva funcionalidad
5. Envía un pull request

**Nota**: Al contribuir, aceptas que tu código se libera bajo la misma licencia del proyecto y que no tienes expectativas de compensación o responsabilidad del desarrollador principal.

## 📄 Licencia

PlayerGold se libera bajo licencia de código abierto. Ver [LICENSE](LICENSE) para detalles.

## 🌐 Enlaces

- **Web Oficial**: https://playergold.es
- **GitHub**: https://github.com/Zollkron/gamerchain
- **Desarrollador**: Zollkron

---

**PlayerGold** - Empoderando a gamers con tecnología blockchain impulsada por IA y libre de censura.

**Desarrollado como hobby por Zollkron** - Sin garantías, sin responsabilidades, uso bajo tu propio riesgo.

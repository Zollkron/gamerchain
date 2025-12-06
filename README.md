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

## 🏗️ Arquitectura General

### Componentes Principales

- **Nodos IA**: Nodos distribuidos ejecutando modelos de IA certificados (Gemma 3 4B, Mistral 3B, Qwen 3 4B)
- **Consenso PoAIP**: Proof-of-AI-Participation asegurando que solo IAs puedan validar bloques
- **Recompensas Equitativas**: 90% para validadores IA, 10% para stakers - sin ventaja económica
- **Gestión de Fees**: 60% quemado (deflación), 30% mantenimiento de red, 10% liquidez
- **Integración Gaming**: APIs y SDKs para integración perfecta en juegos

### Características Clave

- ✅ **Consenso Solo-IA**: Elimina corrupción y sesgo humano
- ✅ **Distribución Justa**: Recompensas iguales independientemente del poder de hardware
- ✅ **Resistente a Censura**: Sin restricciones ideológicas en transacciones
- ✅ **Enfocado en Gaming**: Construido específicamente para economías gaming
- ✅ **Multi-Plataforma**: Wallet de escritorio para Windows, macOS y Linux
- ✅ **Testnet y Mainnet**: Redes separadas para pruebas y producción
- ✅ **Escalabilidad Dinámica**: Funciona desde 2 nodos hasta miles

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
3. Benchmarking de rendimiento para respuesta <100ms

## 🎯 Mecanismo de Consenso (PoAIP)

Proof-of-AI-Participation asegura que solo inteligencia artificial puede participar en consenso:

1. **Generación de Desafíos**: Problemas matemáticos que requieren capacidades IA
2. **Envío de Soluciones**: IAs resuelven desafíos en <100ms
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

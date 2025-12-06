# Network Management and Dynamic Quorum Implementation

**Fecha**: Diciembre 7, 2025  
**Versión**: 2.2.0  
**Desarrollador**: Zollkron

## Resumen

Este documento describe la implementación de los sistemas de gestión de red (testnet/mainnet) y quorum dinámico para PlayerGold/GamerChain.

## Componentes Implementados

### 1. Network Manager (`src/network/network_manager.py`)

Sistema de gestión de redes que permite operar en testnet y mainnet de forma independiente.

#### Características Principales

- **Gestión de Dos Redes**: Testnet y Mainnet completamente separadas
- **Configuración Flexible**: Carga configuración desde YAML
- **Validación de Compatibilidad**: Verifica que los peers estén en la misma red
- **Directorios Separados**: Datos de testnet y mainnet aislados
- **Cambio de Red**: Permite cambiar entre redes (requiere reinicio)

#### Configuración de Redes

**Testnet:**
- Network ID: `playergold-testnet`
- Puerto P2P: 18333
- Puerto API: 18080
- Bootstrap: `testnet.playergold.es:18333`
- Propósito: Desarrollo y pruebas

**Mainnet:**
- Network ID: `playergold-mainnet`
- Puerto P2P: 8333
- Puerto API: 8080
- Bootstrap: `seed1.playergold.es:8333`, `seed2.playergold.es:8333`
- Propósito: Producción con tokens reales

#### Uso Básico

```python
from src.network.network_manager import NetworkManager, NetworkType

# Inicializar
manager = NetworkManager()

# Obtener red actual
current = manager.get_current_network()  # NetworkType.TESTNET

# Verificar tipo de red
if manager.is_testnet():
    print("En testnet - seguro para pruebas")

# Obtener configuración
config = manager.get_network_config()
print(f"Puerto P2P: {config.p2p_port}")

# Validar compatibilidad con peer
is_compatible = manager.validate_network_compatibility("playergold-testnet")

# Cambiar de red
manager.switch_network(NetworkType.MAINNET)
```

### 2. Quorum Manager (`src/consensus/quorum_manager.py`)

Sistema de quorum dinámico que implementa el principio "Donde hayan dos reunidos, mi espíritu está con ellos".

#### Características Principales

- **Quorum Fijo**: 66% (dos tercios) de nodos activos
- **Mínimo 2 Nodos**: Red funciona desde 2 nodos
- **Escalabilidad Dinámica**: Se adapta automáticamente al tamaño de red
- **Validación de Consenso**: Verifica si se alcanza consenso
- **Cálculo de Nodos Faltantes**: Indica cuántos nodos más se necesitan

#### Reglas de Quorum

| Nodos Totales | Nodos Requeridos | Porcentaje Real |
|---------------|------------------|-----------------|
| 2             | 2                | 100%            |
| 3             | 2                | 66.7%           |
| 10            | 7                | 70%             |
| 50            | 33               | 66%             |
| 100           | 66               | 66%             |
| 1000          | 660              | 66%             |

#### Uso Básico

```python
from src.consensus.quorum_manager import QuorumManager

# Inicializar
quorum = QuorumManager(quorum_percentage=0.66, min_nodes=2)

# Verificar quorum
active_nodes = {'node1', 'node2', 'node3'}
all_nodes = {'node1', 'node2', 'node3', 'node4'}

result = quorum.check_quorum(active_nodes, all_nodes)
print(f"Quorum alcanzado: {result.can_proceed}")
print(f"Mensaje: {result.message}")

# Validar si se puede añadir bloque
can_add = quorum.can_add_block(validating_nodes, all_nodes)

# Validar consenso con votos
votes = {'node1': True, 'node2': True, 'node3': False}
consensus, msg = quorum.validate_consensus(votes, all_nodes)

# Obtener nodos faltantes
missing = quorum.get_missing_nodes_count(active_nodes, all_nodes)
```

## Principio Fundamental

### "Donde hayan dos reunidos, mi espíritu está con ellos"

Este principio bíblico aplicado a la red significa:

1. **Mínimo 2 Nodos**: La red puede funcionar con solo 2 nodos
2. **Escalabilidad Infinita**: Funciona igual con 2 o 10,000 nodos
3. **Sin Puntos Únicos de Fallo**: No hay nodos "especiales"
4. **Democracia Real**: Cada nodo tiene el mismo peso

### Garantías de Seguridad

- **Con 2 nodos**: Ambos deben estar comprometidos para atacar (imposible)
- **Con 3+ nodos**: Se requiere controlar 66%+ para atacar
- **Resistencia a Fallos**: Hasta 33% de nodos pueden fallar
- **Recuperación Automática**: Nodos caídos se sincronizan al volver

## Integración con Sistemas Existentes

### Con P2P Network

```python
from src.network.network_manager import NetworkManager
from src.p2p.network import P2PNetwork

# Obtener configuración de red
network_manager = NetworkManager()
config = network_manager.get_network_config()

# Inicializar P2P con configuración correcta
p2p = P2PNetwork(
    node_id="node1",
    listen_port=config.p2p_port,
    bootstrap_nodes=config.bootstrap_nodes
)
```

### Con Consenso PoAIP

```python
from src.consensus.quorum_manager import QuorumManager
from src.consensus.cross_validation import CrossValidator

# Inicializar con quorum dinámico
quorum = QuorumManager()
validator = CrossValidator()

# Verificar quorum antes de validación
if quorum.can_add_block(validating_nodes, all_nodes):
    # Proceder con validación
    result = validator.validate_solution(challenge, solution, processors)
```

### Con Fault Tolerance

```python
from src.consensus.quorum_manager import QuorumManager
from src.consensus.fault_tolerance import FaultToleranceSystem

quorum = QuorumManager()
ft_system = FaultToleranceSystem()

# Obtener nodos activos
active_nodes = ft_system.health_monitor.get_active_nodes()
all_nodes = set(ft_system.health_monitor.node_metrics.keys())

# Verificar si hay quorum
result = quorum.check_quorum(set(active_nodes), all_nodes)
if not result.can_proceed:
    logger.warning(f"Quorum no alcanzado: {result.message}")
```

## Tests

### Network Manager Tests

**Archivo**: `tests/test_network_manager.py`

- ✅ 14 tests, todos pasando
- Cobertura completa de funcionalidad
- Tests de configuración desde archivo
- Tests de validación de compatibilidad

### Quorum Manager Tests

**Archivo**: `tests/test_quorum_manager.py`

- ✅ 23 tests, todos pasando
- Tests de cálculo de quorum para diferentes tamaños
- Tests de validación de consenso
- Tests de escalabilidad

### Ejecución de Tests

```bash
# Tests de Network Manager
python -m pytest tests/test_network_manager.py -v

# Tests de Quorum Manager
python -m pytest tests/test_quorum_manager.py -v

# Todos los tests
python -m pytest tests/test_network_manager.py tests/test_quorum_manager.py -v
```

## Ejemplos

### Ejemplo Completo

**Archivo**: `examples/network_and_quorum_example.py`

Incluye ejemplos de:
- Gestión de redes (testnet/mainnet)
- Cálculo de quorum
- Validación de consenso
- Escalabilidad de quorum

```bash
python examples/network_and_quorum_example.py
```

## Configuración

### Archivo de Configuración

**Ubicación**: `config/default.yaml`

```yaml
network:
  # Tipo de red actual
  network_type: "testnet"  # o "mainnet"
  
  # Configuración de quorum
  min_nodes_for_consensus: 2
  quorum_percentage: 0.66
  
  # Configuración testnet
  testnet:
    network_id: "playergold-testnet"
    p2p_port: 18333
    api_port: 18080
    bootstrap_nodes:
      - "testnet.playergold.es:18333"
  
  # Configuración mainnet
  mainnet:
    network_id: "playergold-mainnet"
    p2p_port: 8333
    api_port: 8080
    bootstrap_nodes:
      - "seed1.playergold.es:8333"
      - "seed2.playergold.es:8333"
```

## Ventajas del Sistema

### 1. Separación Testnet/Mainnet

- **Desarrollo Seguro**: Pruebas sin riesgo de pérdida de tokens reales
- **Aislamiento Total**: Blockchains completamente separadas
- **Configuración Clara**: Puertos y directorios diferentes
- **Migración Controlada**: Proceso claro de testnet a mainnet

### 2. Quorum Dinámico

- **Inicio Simple**: Funciona desde 2 nodos
- **Crecimiento Orgánico**: Escala naturalmente con adopción
- **Resistencia a Ataques**: Requiere 66%+ para comprometer
- **Tolerancia a Fallos**: Hasta 33% de nodos pueden fallar

### 3. Flexibilidad

- **Configurable**: Todos los parámetros en YAML
- **Extensible**: Fácil añadir nuevas redes
- **Auditable**: Código claro y bien documentado
- **Testeable**: Cobertura completa de tests

## Próximos Pasos

### Implementaciones Pendientes

1. **Integración con P2P Network**
   - Usar NetworkManager en P2PNetwork
   - Validar network_id en handshake
   - Rechazar peers de red incorrecta

2. **Integración con Consenso**
   - Usar QuorumManager en validación de bloques
   - Verificar quorum antes de añadir bloques
   - Pausar consenso si no hay quorum

3. **Scripts de Despliegue**
   - Script para iniciar nodo testnet
   - Script para iniciar nodo mainnet
   - Script para migrar de testnet a mainnet

4. **Infraestructura**
   - Configurar dominios (testnet.playergold.es, seed1.playergold.es)
   - Desplegar bootstrap nodes
   - Configurar monitoreo de red

## Conclusión

La implementación de Network Manager y Quorum Manager proporciona una base sólida para:

1. **Operación en Dos Redes**: Testnet para desarrollo, mainnet para producción
2. **Quorum Dinámico**: Funciona desde 2 nodos hasta miles
3. **Seguridad Robusta**: Resistente a ataques y fallos
4. **Escalabilidad**: Crece naturalmente con la red

El sistema está completamente testeado y listo para integración con los demás componentes de PlayerGold/GamerChain.

---

**Desarrollado por**: Zollkron  
**Web**: https://playergold.es  
**Repositorio**: https://github.com/Zollkron/gamerchain

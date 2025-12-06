# Integration Summary - Network Manager & Quorum Manager

**Fecha**: Diciembre 7, 2025  
**Versión**: 2.2.1  
**Desarrollador**: Zollkron

## Resumen

Este documento describe las integraciones realizadas del NetworkManager y QuorumManager con los sistemas existentes de PlayerGold/GamerChain.

## Integración 1: P2P Network con NetworkManager

### Cambios Realizados

**Archivo**: `src/p2p/network.py`

#### 1. Import de NetworkManager

```python
from ..network.network_manager import NetworkManager, NetworkType
```

#### 2. Actualización de PeerInfo

Añadido campo `network_id` para validar compatibilidad:

```python
@dataclass
class PeerInfo:
    peer_id: str
    address: str
    port: int
    public_key: str
    network_id: str  # Nuevo campo
    # ... otros campos
```

#### 3. Constructor P2PNetwork Actualizado

```python
def __init__(self, 
             node_id: str,
             listen_port: Optional[int] = None,  # Ahora opcional
             max_peers: int = 50,
             enable_mdns: bool = True,
             enable_dht: bool = True,
             network_manager: Optional[NetworkManager] = None):  # Nuevo parámetro
```

**Características:**
- Acepta NetworkManager opcional (crea uno si no se proporciona)
- Usa puerto de red automáticamente si no se especifica
- Almacena network_id y network_type
- Registra información de red en logs

#### 4. Handshake con Validación de Red

El método `_perform_handshake` ahora:
- Envía `network_id` y `network_type` en el handshake
- Valida que el peer esté en la misma red
- Rechaza peers incompatibles automáticamente
- Registra rechazos en estadísticas

```python
# Validación de compatibilidad
if not self.network_manager.validate_network_compatibility(peer_network_id):
    logger.warning(f"Rejecting peer: incompatible network")
    self.stats['incompatible_peers_rejected'] += 1
    return None
```

### Beneficios

1. **Aislamiento de Redes**: Testnet y mainnet completamente separadas
2. **Prevención de Errores**: Imposible conectar nodos de diferentes redes
3. **Configuración Automática**: Puerto correcto según la red
4. **Auditoría**: Registro de intentos de conexión incompatibles

### Uso

```python
from src.p2p.network import P2PNetwork
from src.network.network_manager import NetworkManager

# Opción 1: Usar configuración automática
p2p = P2PNetwork(node_id="node1")  # Usa testnet por defecto

# Opción 2: Especificar NetworkManager
network_manager = NetworkManager()
network_manager.switch_network(NetworkType.MAINNET)
p2p = P2PNetwork(node_id="node1", network_manager=network_manager)

# Opción 3: Puerto personalizado
p2p = P2PNetwork(node_id="node1", listen_port=9000)
```

## Integración 2: Consenso con QuorumManager

### Próxima Implementación

La integración del QuorumManager con el sistema de consenso incluirá:

1. **Validación de Quorum en Bloques**
   - Verificar quorum antes de añadir bloques
   - Pausar consenso si no hay quorum suficiente

2. **Integración con CrossValidator**
   - Usar quorum dinámico en validación cruzada
   - Ajustar número de validadores según tamaño de red

3. **Integración con FaultTolerance**
   - Coordinar con sistema de tolerancia a fallos
   - Verificar quorum con nodos activos

## Subdominios (Mockup/Placeholder)

**NOTA**: Los siguientes subdominios están configurados como mockup y no están operativos aún:

### Testnet
- `testnet.playergold.es:18333` - Bootstrap node testnet (placeholder)

### Mainnet
- `seed1.playergold.es:8333` - Seed node 1 mainnet (placeholder)
- `seed2.playergold.es:8333` - Seed node 2 mainnet (placeholder)

### Cuando estén operativos

Los subdominios deberán apuntar a:
1. **Servidores con IP estática**
2. **Nodos bootstrap ejecutando P2PNetwork**
3. **Configuración de firewall** para puertos 8333 y 18333
4. **Monitoreo** para alta disponibilidad

## Scripts de Despliegue

### Script para Nodo Testnet

**Archivo**: `scripts/start_testnet_node.py`

```python
#!/usr/bin/env python3
"""
Script para iniciar un nodo en testnet
"""
import asyncio
from src.network.network_manager import NetworkManager, NetworkType
from src.p2p.network import P2PNetwork

async def main():
    # Configurar para testnet
    network_manager = NetworkManager()
    network_manager.switch_network(NetworkType.TESTNET)
    
    # Iniciar nodo P2P
    node_id = "testnet_node_1"
    p2p = P2PNetwork(node_id=node_id, network_manager=network_manager)
    
    await p2p.start()
    print(f"✓ Nodo testnet iniciado: {node_id}")
    print(f"  Network: {network_manager.get_network_info()['network_id']}")
    print(f"  Puerto: {p2p.listen_port}")
    
    # Mantener ejecutando
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await p2p.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Script para Nodo Mainnet

**Archivo**: `scripts/start_mainnet_node.py`

```python
#!/usr/bin/env python3
"""
Script para iniciar un nodo en mainnet
⚠️ ADVERTENCIA: Mainnet usa tokens REALES
"""
import asyncio
from src.network.network_manager import NetworkManager, NetworkType
from src.p2p.network import P2PNetwork

async def main():
    print("⚠️  ADVERTENCIA: Iniciando nodo MAINNET")
    print("    - Los tokens tienen valor REAL")
    print("    - Las transacciones son PERMANENTES")
    print("    - Asegúrate de saber lo que haces")
    
    # Configurar para mainnet
    network_manager = NetworkManager()
    network_manager.switch_network(NetworkType.MAINNET)
    
    # Iniciar nodo P2P
    node_id = "mainnet_node_1"
    p2p = P2PNetwork(node_id=node_id, network_manager=network_manager)
    
    await p2p.start()
    print(f"✓ Nodo mainnet iniciado: {node_id}")
    print(f"  Network: {network_manager.get_network_info()['network_id']}")
    print(f"  Puerto: {p2p.listen_port}")
    
    # Mantener ejecutando
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await p2p.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Verificación de Integración

### Test de Compatibilidad de Red

```python
import pytest
from src.p2p.network import P2PNetwork
from src.network.network_manager import NetworkManager, NetworkType

@pytest.mark.asyncio
async def test_network_compatibility():
    """Test que nodos de diferentes redes no se conectan"""
    
    # Nodo testnet
    nm_testnet = NetworkManager()
    nm_testnet.switch_network(NetworkType.TESTNET)
    node_testnet = P2PNetwork("node_testnet", network_manager=nm_testnet)
    
    # Nodo mainnet
    nm_mainnet = NetworkManager()
    nm_mainnet.switch_network(NetworkType.MAINNET)
    node_mainnet = P2PNetwork("node_mainnet", network_manager=nm_mainnet)
    
    # Verificar que tienen network_ids diferentes
    assert node_testnet.network_id != node_mainnet.network_id
    
    # Verificar que la validación rechazaría la conexión
    assert not nm_testnet.validate_network_compatibility(node_mainnet.network_id)
    assert not nm_mainnet.validate_network_compatibility(node_testnet.network_id)
```

## Estadísticas Nuevas

El P2PNetwork ahora incluye:

```python
self.stats = {
    # ... estadísticas existentes
    'incompatible_peers_rejected': 0  # Nueva estadística
}
```

Permite monitorear intentos de conexión de redes incompatibles.

## Próximos Pasos

### 1. Completar Integración con Consenso
- [ ] Integrar QuorumManager con validación de bloques
- [ ] Añadir verificación de quorum en CrossValidator
- [ ] Coordinar con FaultToleranceSystem

### 2. Scripts Adicionales
- [ ] Script de migración testnet → mainnet
- [ ] Script de monitoreo de red
- [ ] Script de diagnóstico de conectividad

### 3. Infraestructura
- [ ] Configurar subdominios reales
- [ ] Desplegar bootstrap nodes
- [ ] Configurar monitoreo y alertas

### 4. Documentación
- [ ] Guía de despliegue de nodos
- [ ] Guía de migración
- [ ] FAQ de redes

## Conclusión

La integración del NetworkManager con P2PNetwork proporciona:

1. **Separación Clara**: Testnet y mainnet completamente aisladas
2. **Seguridad**: Imposible mezclar redes accidentalmente
3. **Flexibilidad**: Fácil cambio entre redes
4. **Auditoría**: Registro completo de conexiones

El sistema está listo para operación en ambas redes, con los subdominios configurados como placeholders hasta que la infraestructura esté lista.

---

**Desarrollado por**: Zollkron  
**Web**: https://playergold.es  
**Repositorio**: https://github.com/Zollkron/gamerchain

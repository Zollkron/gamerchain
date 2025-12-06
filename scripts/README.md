# Scripts de Despliegue PlayerGold

Scripts para iniciar y gestionar nodos PlayerGold en testnet y mainnet.

## Scripts Disponibles

### 1. start_testnet_node.py

Inicia un nodo en la red de pruebas (testnet).

**Características:**
- Tokens sin valor real
- Blockchain reseteable
- Seguro para desarrollo y pruebas
- Puerto por defecto: 18333

**Uso:**

```bash
# Inicio básico
python scripts/start_testnet_node.py

# Con ID personalizado
python scripts/start_testnet_node.py --node-id mi_nodo_test

# Con puerto personalizado
python scripts/start_testnet_node.py --node-id node1 --port 19000
```

**Opciones:**
- `--node-id`: ID único para el nodo (default: testnet_node_1)
- `--port`: Puerto de escucha (default: 18333)

### 2. start_mainnet_node.py

Inicia un nodo en la red principal (mainnet).

**⚠️ ADVERTENCIA:**
- Tokens con valor REAL
- Transacciones PERMANENTES
- Requiere confirmación explícita

**Uso:**

```bash
# Requiere --confirm
python scripts/start_mainnet_node.py --confirm

# Con ID personalizado
python scripts/start_mainnet_node.py --node-id mi_nodo --confirm

# Con puerto personalizado
python scripts/start_mainnet_node.py --node-id node1 --port 9000 --confirm
```

**Opciones:**
- `--node-id`: ID único para el nodo (default: mainnet_node_1)
- `--port`: Puerto de escucha (default: 8333)
- `--confirm`: Confirmación requerida (obligatorio)

**Proceso de Confirmación:**
1. Mostrar advertencia de riesgos
2. Requiere flag `--confirm`
3. Solicita confirmación interactiva (escribir 'SI')

## Requisitos

### Dependencias

```bash
pip install -r requirements.txt
```

### Configuración

Los scripts usan la configuración de `config/default.yaml`. Puedes personalizarla según tus necesidades.

## Diferencias entre Testnet y Mainnet

| Característica | Testnet | Mainnet |
|----------------|---------|---------|
| Valor de tokens | Sin valor | Valor REAL |
| Transacciones | Reversibles | PERMANENTES |
| Blockchain | Reseteable | Inmutable |
| Puerto P2P | 18333 | 8333 |
| Puerto API | 18080 | 8080 |
| Directorio datos | ./data/testnet | ./data/mainnet |
| Bootstrap | testnet.playergold.es:18333 | seed1.playergold.es:8333 |

## Subdominios Bootstrap (Mockup)

**NOTA**: Los siguientes subdominios están configurados como mockup y no están operativos aún:

### Testnet
- `testnet.playergold.es:18333` - Bootstrap node testnet (placeholder)

### Mainnet
- `seed1.playergold.es:8333` - Seed node 1 mainnet (placeholder)
- `seed2.playergold.es:8333` - Seed node 2 mainnet (placeholder)

Cuando estén operativos, los nodos se conectarán automáticamente a estos bootstrap nodes.

## Logs

Los scripts generan logs detallados:

```
2025-12-07 12:00:00 - INFO - PlayerGold Testnet Node
2025-12-07 12:00:00 - INFO - Network Configuration:
2025-12-07 12:00:00 - INFO -   Type: TESTNET
2025-12-07 12:00:00 - INFO -   Network ID: playergold-testnet
2025-12-07 12:00:00 - INFO -   Default Port: 18333
2025-12-07 12:00:00 - INFO - ✓ Testnet node started successfully!
```

## Detener un Nodo

Presiona `Ctrl+C` para detener el nodo de forma segura:

```
^C
Shutting down testnet node...
✓ Node stopped
```

## Monitoreo

Los nodos registran estadísticas cada 60 segundos:

```
Stats: 5 peers, 5 connections
```

## Solución de Problemas

### Puerto en uso

Si el puerto está en uso:

```bash
# Usar puerto personalizado
python scripts/start_testnet_node.py --port 19000
```

### No se puede conectar a bootstrap nodes

Los bootstrap nodes son placeholders. Cuando estén operativos, la conexión será automática.

### Error de permisos

En Linux/Mac, puede que necesites permisos de ejecución:

```bash
chmod +x scripts/start_testnet_node.py
chmod +x scripts/start_mainnet_node.py
```

## Seguridad

### Testnet
- Seguro para experimentar
- Sin riesgo de pérdida de fondos
- Ideal para desarrollo

### Mainnet
- Requiere precauciones extremas
- Hacer backups de claves privadas
- Entender completamente el sistema
- Leer PROJECT_INFO.md antes de usar

## Disclaimer

**El desarrollador (Zollkron) NO se hace responsable del uso de estos scripts o del software PlayerGold.**

Uso bajo tu propia responsabilidad. Ver [PROJECT_INFO.md](../PROJECT_INFO.md) para información legal completa.

## Soporte

- **Repositorio**: https://github.com/Zollkron/gamerchain
- **Web**: https://playergold.es
- **Issues**: https://github.com/Zollkron/gamerchain/issues

---

**Desarrollado por**: Zollkron  
**Versión**: 2.2.1

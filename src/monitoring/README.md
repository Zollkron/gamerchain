# Sistema de Monitoreo y Alertas - PlayerGold

Sistema completo de monitoreo, alertas y logging inmutable para la red GamerChain.

## Características

### Sistema de Alertas
- **Detección de anomalías automática**: Detecta patrones inusuales en TPS, latencia y nodos
- **Múltiples niveles de severidad**: INFO, WARNING, ERROR, CRITICAL
- **Handlers configurables**: Console, File, Webhook
- **Alertas en tiempo real**: Notificaciones inmediatas de eventos críticos

### Logging Inmutable
- **Cadena criptográfica**: Cada log está enlazado al anterior mediante hash
- **Verificación de integridad**: Detecta cualquier manipulación de logs
- **Categorización**: Logs organizados por categoría (Consensus, Transaction, Block, etc.)
- **Análisis de patrones**: Detecta comportamientos anómalos automáticamente

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Sistema de Alertas

#### Configuración Básica

```python
from src.monitoring import create_alert_system, ConsoleAlertHandler, FileAlertHandler

# Crear sistema con handlers
alert_system = create_alert_system([
    ConsoleAlertHandler(),
    FileAlertHandler('alerts.log')
])

# Verificar salud de la red
metrics = {
    'tps': 50,
    'latency': 150,
    'active_nodes': 25
}
alert_system.check_network_health(metrics)

# Verificar comportamiento de nodo
behavior_data = {
    'invalid_hash': False,
    'reputation_drop': 5
}
alert_system.check_node_behavior('node123', behavior_data)
```

#### Crear Alertas Manualmente

```python
from src.monitoring import AlertType, AlertSeverity

alert = alert_system.create_alert(
    AlertType.HIGH_LATENCY,
    AlertSeverity.WARNING,
    "Latencia alta detectada: 2500ms",
    {'latency': 2500, 'threshold': 2000}
)

# Resolver alerta
alert_system.resolve_alert(alert.alert_id)
```

#### Consultar Alertas

```python
# Obtener alertas activas
active_alerts = alert_system.get_active_alerts()

# Filtrar por severidad
critical_alerts = alert_system.get_active_alerts(AlertSeverity.CRITICAL)

# Obtener alertas recientes
recent = alert_system.get_recent_alerts(hours=24)

# Estadísticas
stats = alert_system.get_statistics()
print(f"Total alertas: {stats['total_alerts']}")
print(f"Alertas activas: {stats['active_alerts']}")
```

#### Webhook Handler

```python
from src.monitoring import WebhookAlertHandler

webhook_handler = WebhookAlertHandler('https://your-webhook-url.com/alerts')
alert_system.add_handler(webhook_handler)
```

### Logging Inmutable

#### Configuración Básica

```python
from src.monitoring import create_immutable_logger, LogCategory

# Crear logger
logger = create_immutable_logger(log_dir='logs')

# Registrar eventos
logger.info(LogCategory.CONSENSUS, "Bloque validado exitosamente", {
    'block_height': 12345,
    'validators': ['node1', 'node2', 'node3']
})

logger.error(LogCategory.NETWORK, "Fallo de conexión con peer", {
    'peer_id': 'node456',
    'error': 'Connection timeout'
})

logger.critical(LogCategory.SECURITY, "Hash de modelo inválido detectado", {
    'node_id': 'node789',
    'expected_hash': 'abc123',
    'actual_hash': 'def456'
})
```

#### Niveles de Log

```python
from src.monitoring import LogLevel

logger.debug(LogCategory.SYSTEM, "Mensaje de debug")
logger.info(LogCategory.TRANSACTION, "Transacción procesada")
logger.warning(LogCategory.NODE, "Nodo con latencia alta")
logger.error(LogCategory.CONSENSUS, "Fallo en validación")
logger.critical(LogCategory.SECURITY, "Intento de ataque detectado")
```

#### Consultar Logs

```python
# Por categoría
consensus_logs = logger.get_logs(category=LogCategory.CONSENSUS)

# Por nivel
errors = logger.get_logs(level=LogLevel.ERROR)

# Por rango de tiempo
import time
one_hour_ago = time.time() - 3600
recent_logs = logger.get_logs(start_time=one_hour_ago)

# Logs recientes
last_24h = logger.get_recent_logs(hours=24)

# Solo logs críticos
critical = logger.get_critical_logs(hours=24)

# Buscar por texto
results = logger.search_logs("validation failed")
```

#### Verificar Integridad

```python
# Verificar que la cadena de logs no ha sido manipulada
is_valid = logger.verify_integrity()
if not is_valid:
    print("¡ALERTA! Los logs han sido manipulados")
```

#### Exportar Logs

```python
# Exportar todos los logs
logger.export_logs('export_all.log')

# Exportar por categoría
logger.export_logs('consensus_logs.log', category=LogCategory.CONSENSUS)

# Exportar por rango de tiempo
logger.export_logs('today_logs.log', 
                  start_time=time.time() - 86400,
                  end_time=time.time())
```

### Análisis de Patrones

```python
from src.monitoring import PatternAnalyzer

analyzer = PatternAnalyzer(logger)

# Analizar patrones de errores
error_patterns = analyzer.analyze_error_patterns(hours=24)
print(f"Total errores: {error_patterns['total_errors']}")
print(f"Mensajes repetidos: {error_patterns['repeated_messages']}")

# Detectar actividad anómala
anomalies = analyzer.detect_anomalous_activity(threshold=100)
for anomaly in anomalies:
    print(f"Actividad anómala: {anomaly['log_count']} logs en 5 minutos")

# Analizar comportamiento de nodo específico
node_behavior = analyzer.analyze_node_behavior('node123', hours=24)
print(f"Tasa de errores: {node_behavior['error_rate']:.2%}")
```

## Integración con la Red

### En el Blockchain Core

```python
from src.monitoring import create_alert_system, create_immutable_logger
from src.monitoring import LogCategory, AlertType, AlertSeverity

class GamerChainBlockchain:
    def __init__(self):
        self.alert_system = create_alert_system()
        self.logger = create_immutable_logger()
    
    def add_block(self, block):
        # Log la operación
        self.logger.info(LogCategory.BLOCK, "Nuevo bloque añadido", {
            'block_height': block.index,
            'hash': block.hash,
            'transactions': len(block.transactions)
        })
        
        # Verificar salud
        if len(block.transactions) > 1000:
            self.alert_system.create_alert(
                AlertType.TRANSACTION_SPIKE,
                AlertSeverity.WARNING,
                f"Pico de transacciones: {len(block.transactions)}",
                {'block_height': block.index}
            )
```

### En el Sistema de Consenso

```python
def validate_block(self, block):
    start_time = time.time()
    
    try:
        # Validación...
        result = self._perform_validation(block)
        
        latency = (time.time() - start_time) * 1000
        
        self.logger.info(LogCategory.CONSENSUS, "Bloque validado", {
            'block_height': block.index,
            'latency_ms': latency,
            'validators': len(block.ai_validators)
        })
        
        if latency > 100:
            self.alert_system.create_alert(
                AlertType.BLOCK_VALIDATION_TIMEOUT,
                AlertSeverity.WARNING,
                f"Validación lenta: {latency}ms"
            )
        
        return result
        
    except Exception as e:
        self.logger.error(LogCategory.CONSENSUS, "Fallo en validación", {
            'block_height': block.index,
            'error': str(e)
        })
        
        self.alert_system.create_alert(
            AlertType.CONSENSUS_FAILURE,
            AlertSeverity.CRITICAL,
            "Fallo crítico en consenso"
        )
        raise
```

### En el Sistema de Reputación

```python
def update_reputation(self, node_id, event):
    old_score = self.get_reputation(node_id)
    new_score = self._calculate_new_score(node_id, event)
    
    self.logger.info(LogCategory.REPUTATION, "Reputación actualizada", {
        'node_id': node_id,
        'old_score': old_score,
        'new_score': new_score,
        'event': event
    })
    
    drop = old_score - new_score
    if drop > 20:
        self.alert_system.create_alert(
            AlertType.REPUTATION_DROP,
            AlertSeverity.WARNING,
            f"Caída significativa de reputación: {drop} puntos",
            {'node_id': node_id, 'drop': drop}
        )
```

## Tipos de Alertas

| Tipo | Descripción |
|------|-------------|
| `NODE_FAILURE` | Fallo o desconexión de nodo IA |
| `HIGH_LATENCY` | Latencia de red o validación alta |
| `LOW_TPS` | Throughput de transacciones bajo |
| `CONSENSUS_FAILURE` | Fallo en el consenso PoAIP |
| `NETWORK_PARTITION` | Partición de red detectada |
| `SUSPICIOUS_ACTIVITY` | Actividad sospechosa detectada |
| `INVALID_MODEL_HASH` | Hash de modelo IA inválido |
| `REPUTATION_DROP` | Caída significativa de reputación |
| `TRANSACTION_SPIKE` | Pico anómalo de transacciones |
| `BLOCK_VALIDATION_TIMEOUT` | Timeout en validación de bloque |

## Categorías de Logs

| Categoría | Uso |
|-----------|-----|
| `CONSENSUS` | Eventos del consenso PoAIP |
| `TRANSACTION` | Procesamiento de transacciones |
| `BLOCK` | Creación y validación de bloques |
| `NODE` | Eventos de nodos IA |
| `NETWORK` | Comunicación P2P |
| `SECURITY` | Eventos de seguridad |
| `REPUTATION` | Sistema de reputación |
| `SYSTEM` | Eventos generales del sistema |

## Requisitos Cumplidos

✅ **Requisito 14.2**: Sistema de detección de anomalías con alertas automáticas
✅ **Requisito 14.4**: Logs inmutables de todas las operaciones críticas
✅ Análisis de patrones de comportamiento inusuales
✅ Múltiples handlers para alertas (console, file, webhook)
✅ Verificación criptográfica de integridad de logs
✅ Categorización y búsqueda de logs
✅ Estadísticas y análisis de patrones

## Arquitectura

```
┌─────────────────────────────────────────┐
│         Aplicación Principal            │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────────┐  ┌────▼──────────┐
│Alert System│  │Immutable Logger│
└───┬────────┘  └────┬──────────┘
    │                │
    │  ┌─────────────┴──────────┐
    │  │                        │
┌───▼──▼────┐  ┌────────┐  ┌───▼────┐
│ Handlers  │  │ Anomaly│  │Pattern │
│           │  │Detector│  │Analyzer│
└───────────┘  └────────┘  └────────┘
```

## Mejores Prácticas

1. **Siempre verificar integridad**: Ejecuta `logger.verify_integrity()` periódicamente
2. **Categorizar correctamente**: Usa la categoría apropiada para cada log
3. **Incluir contexto**: Añade datos relevantes en el campo `data`
4. **Resolver alertas**: Marca alertas como resueltas cuando se solucionen
5. **Monitorear estadísticas**: Revisa regularmente las estadísticas de alertas y logs
6. **Exportar logs**: Realiza backups periódicos de los logs
7. **Configurar webhooks**: Para alertas críticas, usa webhooks para notificaciones externas

## Licencia

Parte del proyecto PlayerGold - Hecho por gamers para gamers

# PlayerGold Block Explorer

Explorador de bloques en tiempo real para la blockchain GamerChain con métricas de red, visualización de transacciones y monitoreo de nodos IA.

## Características

### Dashboard de Red
- **TPS (Transacciones por segundo)**: Métricas en tiempo real del throughput de la red
- **Latencia promedio**: Tiempo de validación de bloques
- **Nodos IA activos**: Cantidad de nodos validadores operativos
- **Altura del bloque**: Número actual de bloques en la cadena

### Visualización de Datos
- **Bloques recientes**: Lista de los últimos bloques validados con detalles
- **Transacciones recientes**: Historial de transacciones confirmadas y pendientes
- **Distribución de nodos**: Estadísticas de modelos IA y su distribución en la red

### Búsqueda
- Buscar por hash de bloque
- Buscar por hash de transacción
- Buscar por dirección de wallet

### Gráficos en Tiempo Real
- Gráfico de TPS histórico
- Distribución de modelos IA (gráfico de dona)

## Instalación

### Dependencias

```bash
pip install flask flask-cors flask-socketio
```

### Iniciar el Servidor API

```python
from src.api.explorer_api import create_explorer_api

# Crear instancia del explorador
explorer = create_explorer_api(blockchain, p2p_network, reputation_manager)

# Iniciar servidor
explorer.run(host='0.0.0.0', port=5000)
```

### Abrir el Explorador Web

Simplemente abre `explorer/index.html` en tu navegador, o sirve los archivos con un servidor web:

```bash
# Opción 1: Python simple HTTP server
python -m http.server 8000 --directory explorer

# Opción 2: Node.js http-server
npx http-server explorer -p 8000
```

Luego visita: `http://localhost:8000`

## API Endpoints

### Métricas de Red
```
GET /api/network/metrics
```
Retorna métricas actuales de la red (TPS, latencia, nodos activos, etc.)

### Bloques Recientes
```
GET /api/blocks/recent?limit=10
```
Retorna los últimos N bloques

### Bloque por Hash
```
GET /api/blocks/<block_hash>
```
Retorna detalles de un bloque específico

### Transacciones Recientes
```
GET /api/transactions/recent?limit=10
```
Retorna las últimas N transacciones

### Transacción por Hash
```
GET /api/transactions/<tx_hash>
```
Retorna detalles de una transacción específica

### Información de Dirección
```
GET /api/address/<address>
```
Retorna balance, transacciones y reputación de una dirección

### Distribución de Nodos
```
GET /api/nodes/distribution
```
Retorna estadísticas de distribución de nodos IA

### Búsqueda
```
GET /api/search?q=<query>
```
Busca bloques, transacciones o direcciones

### Historial de TPS
```
GET /api/stats/tps?hours=1
```
Retorna historial de TPS para las últimas N horas

### Historial de Latencia
```
GET /api/stats/latency?hours=1
```
Retorna historial de latencia para las últimas N horas

## WebSocket

El explorador usa WebSocket para actualizaciones en tiempo real:

```javascript
ws://localhost:5000/ws
```

### Eventos WebSocket

- `new_block`: Nuevo bloque validado
- `new_transaction`: Nueva transacción recibida
- `metrics_update`: Actualización de métricas de red
- `node_update`: Actualización de estado de nodo

## Arquitectura

```
┌─────────────────┐
│  Frontend Web   │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │
         │ HTTP/WebSocket
         │
┌────────▼────────┐
│  Explorer API   │
│    (Flask)      │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬────────────┐
    │         │          │            │
┌───▼───┐ ┌──▼──┐ ┌─────▼─────┐ ┌───▼────┐
│Blockchain│ │P2P  │ │Reputation │ │Metrics │
│  Core   │ │Network│ │ Manager  │ │Collector│
└─────────┘ └─────┘ └───────────┘ └────────┘
```

## Personalización

### Cambiar Intervalo de Actualización

En `explorer.js`, modifica los intervalos en `startAutoRefresh()`:

```javascript
// Actualizar métricas cada 5 segundos
setInterval(() => {
    this.updateNetworkMetrics();
}, 5000);
```

### Cambiar Colores del Theme

En `styles.css`, modifica los gradientes:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Agregar Nuevas Métricas

1. Agregar cálculo en `explorer_api.py`:
```python
def calculate_custom_metric(self):
    # Tu lógica aquí
    return value
```

2. Agregar al dashboard en `index.html`:
```html
<div class="metric-card">
    <div class="metric-value" id="custom-metric">0</div>
    <div class="metric-label">Tu Métrica</div>
</div>
```

3. Actualizar en `explorer.js`:
```javascript
document.getElementById('custom-metric').textContent = metrics.custom_metric;
```

## Requisitos Cumplidos

✅ **Requisito 14.1**: Interfaz web para visualizar bloques, transacciones y estadísticas
✅ **Requisito 14.3**: Métricas en tiempo real de TPS, latencia y distribución de nodos
✅ Dashboards para monitoreo de salud de la red
✅ Búsqueda de bloques, transacciones y direcciones
✅ Gráficos interactivos con Chart.js
✅ Actualizaciones en tiempo real vía WebSocket

## Tecnologías Utilizadas

- **Backend**: Flask, Flask-SocketIO, Flask-CORS
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Gráficos**: Chart.js
- **WebSocket**: Socket.IO
- **Diseño**: CSS Grid, Flexbox, Gradientes

## Licencia

Parte del proyecto PlayerGold - Hecho por gamers para gamers

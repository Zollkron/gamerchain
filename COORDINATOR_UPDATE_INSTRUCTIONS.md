# PlayerGold Network Coordinator - Update Instructions

## 🎯 Objetivo
Actualizar el coordinador en el servidor para que todos los endpoints funcionen correctamente.

## 📊 Estado Actual (ACTUALIZADO)
- ❌ **Health endpoint**: 503 Service Unavailable
- ❌ **Register endpoint**: 503 Service Unavailable
- ❌ **Network Map endpoint**: 503 Service Unavailable  
- ❌ **KeepAlive endpoint**: 503 Service Unavailable
- ❌ **Stats endpoint**: 503 Service Unavailable

## 🔧 Problema Identificado
El coordinador devuelve 503 Service Unavailable, lo que significa que Apache está funcionando pero el servicio backend del coordinador no está ejecutándose. Según los logs anteriores, el problema es la dependencia `aiohttp` faltante que impide que el servicio se inicie.

## ✅ Solución Completa
He creado un script automatizado que soluciona todos los problemas de dependencias y reinicia el servicio correctamente.

## 📋 Pasos para Solucionar (MÉTODO RÁPIDO)

### 1. Conectar al Servidor
```bash
ssh root@playergold.es
```

### 2. Ir al Directorio del Proyecto
```bash
cd /path/to/gamerchain  # Ajustar según la ubicación real del proyecto
```

### 3. Ejecutar Script de Solución Automática
```bash
# Hacer el script ejecutable
chmod +x scripts/fix_coordinator_dependencies.sh

# Ejecutar la solución completa
sudo ./scripts/fix_coordinator_dependencies.sh
```

Este script automáticamente:
- ✅ Instala la dependencia `aiohttp` faltante
- ✅ Verifica todas las dependencias Python necesarias
- ✅ Actualiza la configuración del servicio systemd
- ✅ Reinicia el coordinador correctamente
- ✅ Prueba los endpoints localmente
- ✅ Verifica que Apache proxy funcione

### 4. Verificar que Todo Funciona
```bash
# Verificar estado del servicio
sudo systemctl status playergold-coordinator

# Ver logs en tiempo real (opcional)
sudo journalctl -u playergold-coordinator -f

# Probar endpoints localmente
curl -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost:8000/api/v1/health
```

## 🧪 Verificación desde Windows
Después de ejecutar el script de solución, probar desde Windows:
```bash
node test_coordinator_endpoints_final.js
```

**Resultado esperado**: 
- Cambio de `503 Service Unavailable` a `200 OK` en todos los endpoints
- Mensaje final: "🎉 ALL ENDPOINTS WORKING! Coordinator is fully operational."

## 🔍 Verificación Adicional (Opcional)
Si quieres verificar el setup antes de ejecutar:
```bash
# En el servidor, verificar dependencias
python3 scripts/verify_coordinator_setup.py
```

## 📁 Archivos Importantes

### En el Servidor
- `/opt/playergold/src/network_coordinator/server.py` - Servidor principal
- `/opt/playergold/scripts/start_network_coordinator.py` - Script de inicio
- `/etc/systemd/system/playergold-coordinator.service` - Servicio systemd
- `/etc/apache2/sites-available/playergold-coordinator.conf` - Configuración Apache

### Logs
- `sudo journalctl -u playergold-coordinator` - Logs del coordinador
- `/opt/playergold/logs/network_coordinator.log` - Log de aplicación
- `/var/log/apache2/playergold_error.log` - Logs de Apache

## 🔍 Diagnóstico de Problemas

### Si los endpoints siguen devolviendo 404:
1. Verificar que el servicio está ejecutándose:
   ```bash
   sudo systemctl status playergold-coordinator
   ```

2. Verificar que está escuchando en el puerto correcto:
   ```bash
   sudo netstat -tlnp | grep 8000
   ```

3. Probar endpoint directamente (sin Apache):
   ```bash
   curl -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost:8000/api/v1/register
   ```

4. Verificar configuración de Apache:
   ```bash
   sudo apache2ctl configtest
   ```

### Si hay errores en los logs:
1. Ver logs detallados:
   ```bash
   sudo journalctl -u playergold-coordinator --no-pager -n 50
   ```

2. Verificar dependencias Python:
   ```bash
   sudo -u playergold /opt/playergold/venv/bin/pip list
   ```

## 🎉 Resultado Final Esperado
Después de ejecutar el script de solución, la wallet debería:
- ✅ Conectarse exitosamente al coordinador (cambio de 503 a 200)
- ✅ Registrarse como nodo (regular o pionero)
- ✅ Obtener el mapa de red real del coordinador
- ✅ Enviar keepalive messages correctamente
- ✅ Salir del modo desarrollo/fallback

## 🧪 Prueba Final de la Wallet
Para verificar que la wallet puede conectarse después del fix:
```bash
# Desde Windows, en el directorio del proyecto
node test_wallet_coordinator_connection.js
```

**Resultado esperado**: 
- "🎉 SUCCESS! Wallet can connect to coordinator and get real network map"
- "✅ Wallet validation: CAN OPERATE"

## 📞 Soporte y Diagnóstico
Si hay problemas después de ejecutar el script:

### 1. Verificar servicio del coordinador:
```bash
sudo systemctl status playergold-coordinator
sudo journalctl -u playergold-coordinator -n 20
```

### 2. Verificar dependencias Python:
```bash
python3 scripts/verify_coordinator_setup.py
```

### 3. Probar endpoints manualmente:
```bash
# Localmente en el servidor
curl -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost:8000/api/v1/health

# A través de Apache HTTPS
curl -k -H "User-Agent: PlayerGold-Wallet/1.0.0" https://playergold.es/api/v1/health
```

### 4. Verificar logs de Apache:
```bash
tail -f /var/log/apache2/playergold_error.log
```

## 🚀 Archivos Creados para la Solución
- `scripts/fix_coordinator_dependencies.sh` - Script principal de solución
- `scripts/verify_coordinator_setup.py` - Verificación de dependencias
- `test_wallet_coordinator_connection.js` - Prueba de conexión de wallet
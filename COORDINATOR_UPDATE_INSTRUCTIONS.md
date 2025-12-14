# PlayerGold Network Coordinator - Update Instructions

## 🎯 Objetivo
Actualizar el coordinador en el servidor para que todos los endpoints funcionen correctamente.

## 📊 Estado Actual
- ✅ **Health endpoint**: Funcionando (https://playergold.es/api/v1/health)
- ❌ **Register endpoint**: 404 Not Found
- ❌ **Network Map endpoint**: 404 Not Found  
- ❌ **KeepAlive endpoint**: 404 Not Found
- ❌ **Stats endpoint**: 404 Not Found

## 🔧 Solución
El coordinador está ejecutando solo un endpoint básico de health. Necesitamos actualizar a la aplicación FastAPI completa.

## 📋 Pasos para Actualizar

### 1. Conectar al Servidor
```bash
ssh root@playergold.es
```

### 2. Ir al Directorio del Proyecto
```bash
cd /path/to/gamerchain  # Ajustar según la ubicación real
```

### 3. Ejecutar Script de Actualización
```bash
sudo ./scripts/update_coordinator_endpoints.sh
```

### 4. Verificar Estado
```bash
# Verificar que el servicio está funcionando
sudo systemctl status playergold-coordinator

# Ver logs en tiempo real
sudo journalctl -u playergold-coordinator -f

# Probar endpoints localmente
curl -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost:8000/api/v1/health
```

## 🧪 Verificación desde Windows
Después de la actualización, ejecutar desde Windows:
```bash
node test_coordinator_endpoints_final.js
```

**Resultado esperado**: Todos los endpoints deben devolver status 200.

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
Después de la actualización, la wallet debería:
- ✅ Conectarse exitosamente al coordinador
- ✅ Registrarse como nodo (regular o pionero)
- ✅ Obtener el mapa de red real
- ✅ Enviar keepalive messages
- ✅ Salir del modo desarrollo

## 📞 Soporte
Si hay problemas durante la actualización:
1. Revisar logs del coordinador
2. Verificar que Apache está proxy-ing correctamente
3. Comprobar que el firewall permite conexiones al puerto 8000
4. Verificar que el usuario `playergold` tiene permisos correctos
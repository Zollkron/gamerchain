# PlayerGold Network Coordinator - Configuración SSL/HTTPS

## 📋 Resumen

El coordinador de red ya está funcionando correctamente en tu servidor Ubuntu 24.04. Ahora necesitas configurar SSL/HTTPS para que funcione en producción de forma segura.

## ✅ Estado Actual

Según los logs que compartiste, el coordinador está:
- ✅ **Activo y funcionando** (39.4MB memoria, 1-2ms respuesta)
- ✅ **Apache2 funcionando** como proxy reverso
- ✅ **Validación User-Agent** bloqueando accesos no autorizados
- ✅ **Rate limiting** operacional
- ✅ **Logs funcionando** correctamente

## 🔒 Configuración SSL Pendiente

Para completar el despliegue en producción, necesitas configurar HTTPS:

### Paso 1: Configurar SSL/HTTPS

```bash
# Ejecutar el script de configuración SSL
sudo ./scripts/configure_ssl_coordinator.sh
```

Este script:
- 🔍 **Detecta automáticamente** los certificados SSL existentes de Apache2
- 🔧 **Configura HTTPS** para el coordinador en playergold.es
- 🛡️ **Añade headers de seguridad** (HSTS, CSP, etc.)
- 🔄 **Configura redirección** HTTP → HTTPS
- 🚫 **Mantiene la validación** User-Agent en HTTPS
- 📱 **Actualiza fail2ban** para proteger HTTPS
- 🔄 **Configura renovación automática** (si usa Let's Encrypt)

### Paso 2: Verificar Estado Completo

```bash
# Verificar que todo funciona correctamente
./scripts/check_coordinator_status.sh
```

Este script verifica:
- 🔧 **Servicios del sistema** (Apache2, coordinador, fail2ban, UFW)
- 🌐 **Puertos y conectividad** (80, 443, 8000)
- 🔌 **APIs funcionando** (HTTP, HTTPS, directo)
- 🛡️ **Protecciones de seguridad** (User-Agent, fail2ban)
- 🔒 **Certificados SSL** y headers de seguridad
- 📊 **Logs y rendimiento** del coordinador

## 🧪 Scripts de Prueba Disponibles

Una vez configurado SSL, tendrás estos scripts de prueba:

```bash
# Pruebas completas del coordinador
sudo -u playergold /opt/playergold/test_deployment.sh

# Pruebas específicas de SSL/HTTPS
sudo -u playergold /opt/playergold/test_ssl.sh

# Verificación de estado general
./scripts/check_coordinator_status.sh
```

## 🚨 Script de Emergencia

Si necesitas desbloquear IPs de fail2ban:

```bash
# Desbloquear IP específica
sudo /opt/playergold/emergency_unblock.sh 192.168.1.100

# Menú interactivo de emergencia
sudo /opt/playergold/emergency_unblock.sh
```

## 📊 URLs del Coordinador (después de SSL)

Una vez configurado SSL, el coordinador estará disponible en:

- **Health Check**: `https://playergold.es/api/v1/health`
- **Registro de wallets**: `https://playergold.es/api/v1/register`
- **Mapa de red**: `https://playergold.es/api/v1/network-map`
- **Admin** (solo localhost): `https://playergold.es/admin/stats`

## 🔧 Comandos de Administración

```bash
# Ver estado del coordinador
sudo systemctl status playergold-coordinator

# Ver logs en tiempo real
sudo journalctl -u playergold-coordinator -f

# Reiniciar coordinador
sudo systemctl restart playergold-coordinator

# Ver logs de Apache2
sudo tail -f /var/log/apache2/error.log

# Estado de fail2ban
sudo fail2ban-client status
```

## 🛡️ Protecciones Implementadas

### Validación User-Agent
- ✅ Solo acepta requests de `PlayerGold-Wallet/1.0.0`
- ✅ Bloquea automáticamente IPs sospechosas
- ✅ Funciona tanto en HTTP como HTTPS

### Rate Limiting
- ✅ 30 requests por minuto por IP
- ✅ Límites específicos por endpoint:
  - `/api/v1/register`: 5/min
  - `/api/v1/keepalive`: 60/min
  - `/api/v1/network-map`: 10/min
  - Otros endpoints: 20/min

### Fail2ban Anti-DDoS
- ✅ Protección HTTP y HTTPS
- ✅ Detección de ataques DDoS
- ✅ Baneos automáticos temporales
- ✅ Whitelist de IPs administrativas

### Firewall UFW
- ✅ Solo puertos necesarios abiertos (22, 80, 443)
- ✅ Puerto 8000 solo desde localhost
- ✅ Configuración segura por defecto

## 📈 Monitoreo Automático

El sistema incluye monitoreo automático cada 5 minutos que:
- 🔍 **Verifica servicios** (Apache2, coordinador)
- 🔄 **Reinicia automáticamente** si hay problemas
- 📝 **Registra eventos** en `/opt/playergold/logs/monitor.log`
- 🔧 **Auto-recuperación** de fallos temporales

## 🔄 Renovación de Certificados

### Let's Encrypt (automática)
Si usas Let's Encrypt, la renovación es automática:
- ✅ **certbot.timer** habilitado
- ✅ **Hook de post-renovación** configurado
- ✅ **Apache2 se recarga** automáticamente

### Certificados Personalizados (manual)
Si usas certificados personalizados:
- ⚠️ **Renovación manual** requerida
- 📅 **Verificar fechas** de expiración regularmente
- 🔄 **Recargar Apache2** después de renovar

## 🎯 Próximos Pasos

1. **Ejecutar configuración SSL**: `sudo ./scripts/configure_ssl_coordinator.sh`
2. **Verificar funcionamiento**: `./scripts/check_coordinator_status.sh`
3. **Probar desde wallets**: Configurar wallets para usar `https://playergold.es`
4. **Monitorear logs**: Revisar logs regularmente
5. **Configurar backups**: Implementar backup de la base de datos

## 🆘 Solución de Problemas

### El coordinador no responde
```bash
# Verificar estado
sudo systemctl status playergold-coordinator

# Ver logs
sudo journalctl -u playergold-coordinator -n 50

# Reiniciar
sudo systemctl restart playergold-coordinator
```

### Apache2 no funciona
```bash
# Verificar configuración
sudo apache2ctl configtest

# Ver logs de error
sudo tail -f /var/log/apache2/error.log

# Reiniciar Apache2
sudo systemctl restart apache2
```

### Problemas de SSL
```bash
# Verificar certificados
openssl s_client -connect playergold.es:443 -servername playergold.es

# Probar configuración SSL
sudo -u playergold /opt/playergold/test_ssl.sh

# Ver logs SSL de Apache2
sudo tail -f /var/log/apache2/playergold-coordinator-ssl-error.log
```

### IPs bloqueadas por fail2ban
```bash
# Ver IPs bloqueadas
sudo fail2ban-client status

# Desbloquear IP específica
sudo /opt/playergold/emergency_unblock.sh 192.168.1.100

# Desbloquear todas las IPs (emergencia)
sudo /opt/playergold/emergency_unblock.sh
```

## 📞 Contacto y Soporte

Si tienes problemas:
1. **Ejecuta el script de estado**: `./scripts/check_coordinator_status.sh`
2. **Revisa los logs**: `sudo journalctl -u playergold-coordinator -n 50`
3. **Usa el script de emergencia** si es necesario
4. **Comparte los logs** para diagnóstico

---

**¡El coordinador está listo para producción una vez configurado SSL!** 🚀
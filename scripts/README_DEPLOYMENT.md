# PlayerGold Network Coordinator - Despliegue en Ubuntu

Este directorio contiene los scripts necesarios para desplegar el coordinador de red PlayerGold en un servidor Ubuntu con protección completa anti-DDoS y validación de wallets legítimos.

## 🚀 Instalación Rápida (Recomendada)

Para una instalación completa con todas las protecciones:

```bash
# Clonar el repositorio
git clone <repository-url>
cd playergold

# Hacer ejecutable el script
chmod +x scripts/install_coordinator_complete.sh

# Ejecutar instalación completa
sudo ./scripts/install_coordinator_complete.sh playergold.es
```

## 📋 Scripts Disponibles

### 1. `install_coordinator_complete.sh` (Recomendado)
**Instalación completa todo-en-uno**
- Despliegue básico del coordinador
- Protecciones avanzadas anti-DDoS
- Configuración de producción
- Backups automáticos
- Monitoreo y alertas

```bash
sudo ./install_coordinator_complete.sh [dominio]
```

### 2. `deploy_coordinator_ubuntu.sh`
**Despliegue básico del coordinador**
- Instalación del coordinador FastAPI
- Configuración de Nginx
- Firewall UFW básico
- Certificados SSL con Let's Encrypt
- Servicio systemd

```bash
sudo ./deploy_coordinator_ubuntu.sh
```

### 3. `configure_advanced_protection.sh`
**Protecciones avanzadas (ejecutar después del básico)**
- Validación criptográfica de wallets
- Sistema de blacklist/whitelist
- Monitoreo en tiempo real
- Dashboard de administración
- Protección iptables avanzada

```bash
sudo ./configure_advanced_protection.sh
```

## 🔒 Características de Seguridad

### Protección Anti-DDoS
- **Rate limiting por IP**: Máximo 10 peticiones por minuto por IP
- **Rate limiting por endpoint**: Límites específicos para cada API
- **Fail2ban**: Bloqueo automático de IPs sospechosas
- **iptables avanzado**: Protección a nivel de red
- **Nginx rate limiting**: Protección adicional en el proxy

### Validación de Wallets Legítimos
- **User-Agent obligatorio**: Solo acepta `PlayerGold-Wallet/1.0.0`
- **Validación criptográfica**: Verificación de firmas de wallets
- **Blacklist automática**: IPs sospechosas bloqueadas automáticamente
- **Whitelist**: IPs de confianza siempre permitidas

### Monitoreo y Alertas
- **Monitoreo en tiempo real**: CPU, memoria, tiempos de respuesta
- **Dashboard web**: Visualización de métricas y estadísticas
- **Alertas automáticas**: Notificaciones por email de problemas
- **Logs detallados**: Registro completo de actividad

## 🌐 Configuración de Red

### Puertos Utilizados
- **80 (HTTP)**: Redirige automáticamente a HTTPS
- **443 (HTTPS)**: Acceso principal al coordinador
- **8000**: Puerto interno del coordinador (no expuesto)
- **22 (SSH)**: Administración del servidor

### Firewall (UFW)
```bash
# Ver estado del firewall
sudo ufw status

# Permitir IP específica (si es necesario)
sudo ufw allow from IP_ADDRESS to any port 443

# Bloquear IP específica
sudo ufw deny from IP_ADDRESS
```

## 📊 Administración y Monitoreo

### Comandos Útiles

```bash
# Ver estado del coordinador
sudo systemctl status playergold-coordinator

# Reiniciar coordinador
sudo systemctl restart playergold-coordinator

# Ver logs en tiempo real
sudo journalctl -u playergold-coordinator -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/playergold-access.log
sudo tail -f /var/log/nginx/playergold-error.log

# Ver estadísticas de fail2ban
sudo fail2ban-client status playergold-coordinator
```

### Dashboard Web
Accede al dashboard de monitoreo en:
```
https://tu-dominio.com/dashboard
```

### Archivos de Configuración
- **Coordinador**: `/opt/playergold/.env`
- **Nginx**: `/etc/nginx/sites-available/playergold-coordinator`
- **Fail2ban**: `/etc/fail2ban/jail.d/playergold-coordinator.conf`
- **Logs**: `/opt/playergold/logs/`

## 🔧 Configuración Avanzada

### Variables de Entorno
Edita `/opt/playergold/.env` para configurar:

```bash
# Dominio
DOMAIN=playergold.es

# Seguridad
HMAC_SECRET=tu_secreto_hmac
JWT_SECRET=tu_secreto_jwt

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Alertas
ALERT_EMAIL=admin@playergold.es
```

### Gestión de IPs

```bash
# Añadir IP a whitelist
echo '{"ip": "1.2.3.4", "reason": "Trusted server"}' | \
sudo -u playergold tee -a /opt/playergold/data/ip_whitelist.json

# Añadir IP a blacklist
echo '{"ip": "1.2.3.4", "reason": "Malicious activity"}' | \
sudo -u playergold tee -a /opt/playergold/data/ip_blacklist.json

# Reiniciar para aplicar cambios
sudo systemctl restart playergold-coordinator
```

## 📦 Backups

### Backup Automático
Los backups se ejecutan automáticamente todos los días a las 2:00 AM:
- **Ubicación**: `/opt/playergold/backups/`
- **Retención**: 7 días
- **Contenido**: Datos, configuración, código fuente

### Backup Manual
```bash
sudo -u playergold /opt/playergold/backup.sh
```

### Restaurar Backup
```bash
# Detener servicio
sudo systemctl stop playergold-coordinator

# Restaurar desde backup
sudo tar -xzf /opt/playergold/backups/coordinator_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Reiniciar servicio
sudo systemctl start playergold-coordinator
```

## 🚨 Solución de Problemas

### El coordinador no inicia
```bash
# Ver logs de error
sudo journalctl -u playergold-coordinator -n 50

# Verificar configuración
sudo -u playergold /opt/playergold/venv/bin/python -m py_compile /opt/playergold/src/protected_server.py

# Verificar permisos
sudo chown -R playergold:playergold /opt/playergold
```

### Problemas de SSL
```bash
# Renovar certificado manualmente
sudo certbot renew

# Verificar configuración de Nginx
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### IPs bloqueadas incorrectamente
```bash
# Ver IPs bloqueadas por fail2ban
sudo fail2ban-client status playergold-coordinator

# Desbloquear IP específica
sudo fail2ban-client set playergold-coordinator unbanip IP_ADDRESS

# Ver logs de fail2ban
sudo tail -f /var/log/fail2ban.log
```

### Alto uso de CPU/Memoria
```bash
# Ver procesos del coordinador
sudo ps aux | grep playergold

# Ver métricas del sistema
htop

# Verificar logs de alertas
sudo tail -f /opt/playergold/logs/alerts.log
```

## 🔄 Actualizaciones

### Actualizar código del coordinador
```bash
# Hacer backup
sudo -u playergold /opt/playergold/backup.sh

# Detener servicio
sudo systemctl stop playergold-coordinator

# Actualizar código (desde el repositorio)
sudo cp -r src/network_coordinator/* /opt/playergold/src/

# Establecer permisos
sudo chown -R playergold:playergold /opt/playergold/src

# Reiniciar servicio
sudo systemctl start playergold-coordinator
```

### Actualizar dependencias
```bash
sudo -u playergold /opt/playergold/venv/bin/pip install --upgrade fastapi uvicorn pydantic
sudo systemctl restart playergold-coordinator
```

## 📞 Soporte

### Logs Importantes
- **Coordinador**: `/opt/playergold/logs/coordinator.log`
- **Acceso**: `/opt/playergold/logs/access.log`
- **Alertas**: `/opt/playergold/logs/alerts.log`
- **Nginx**: `/var/log/nginx/playergold-*.log`
- **Sistema**: `journalctl -u playergold-coordinator`

### Métricas de Rendimiento
- **Dashboard**: `https://tu-dominio.com/dashboard`
- **API Stats**: `https://tu-dominio.com/admin/stats`
- **Health Check**: `https://tu-dominio.com/api/v1/health`

### Contacto
Para soporte técnico, incluye en tu reporte:
1. Logs relevantes
2. Configuración del sistema
3. Descripción del problema
4. Pasos para reproducir el error

---

## ⚠️ Notas Importantes

1. **DNS**: Asegúrate de que el dominio apunte al servidor antes de ejecutar los scripts
2. **Firewall**: Los scripts configuran UFW automáticamente
3. **SSL**: Los certificados se renuevan automáticamente
4. **Backups**: Verifica que los backups se ejecuten correctamente
5. **Monitoreo**: Revisa el dashboard regularmente para detectar problemas

El coordinador está diseñado para ser altamente seguro y resistente a ataques DDoS, pero requiere configuración y monitoreo adecuados para un funcionamiento óptimo en producción.
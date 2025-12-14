#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Instalación Completa Ubuntu
# ============================================================================
# 
# Script de instalación completa que incluye:
# - Despliegue básico del coordinador
# - Protecciones avanzadas anti-DDoS
# - Validación de wallets legítimos
# - Monitoreo y alertas
# - Dashboard de administración
#
# Uso: sudo ./install_coordinator_complete.sh [dominio]
# Ejemplo: sudo ./install_coordinator_complete.sh playergold.es
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuración
DOMAIN=${1:-"playergold.es"}
COORDINATOR_USER="playergold"
COORDINATOR_HOME="/opt/playergold"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

header() {
    echo -e "${PURPLE}"
    echo "============================================================================"
    echo " $1"
    echo "============================================================================"
    echo -e "${NC}"
}

# Verificar prerrequisitos
check_prerequisites() {
    header "Verificando Prerrequisitos"
    
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    
    if ! grep -q "Ubuntu" /etc/os-release; then
        error "Este script está diseñado para Ubuntu"
        exit 1
    fi
    
    local version=$(lsb_release -rs)
    log "✅ Ubuntu $version detectado"
    
    # Verificar conectividad a internet
    if ! ping -c 1 google.com &> /dev/null; then
        error "No hay conectividad a internet"
        exit 1
    fi
    
    log "✅ Conectividad a internet verificada"
    
    # Verificar espacio en disco (mínimo 2GB)
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 2097152 ]]; then  # 2GB en KB
        error "Espacio insuficiente en disco (mínimo 2GB requeridos)"
        exit 1
    fi
    
    log "✅ Espacio en disco suficiente"
    
    info "Dominio configurado: $DOMAIN"
    info "Usuario del sistema: $COORDINATOR_USER"
    info "Directorio de instalación: $COORDINATOR_HOME"
}

# Mostrar información de instalación
show_installation_info() {
    header "Información de Instalación"
    
    cat << EOF
🎮 PlayerGold Network Coordinator - Instalación Completa

📋 Componentes que se instalarán:
   • Coordinador de red con API FastAPI
   • Protección anti-DDoS avanzada
   • Validación criptográfica de wallets
   • Firewall UFW + iptables + fail2ban
   • Nginx como proxy reverso
   • Certificados SSL automáticos (Let's Encrypt)
   • Monitoreo en tiempo real
   • Dashboard de administración
   • Logs y alertas automáticas

🔒 Características de seguridad:
   • Solo acepta peticiones de wallets PlayerGold
   • Rate limiting por IP y endpoint
   • Blacklist/whitelist automática
   • Detección de comportamiento sospechoso
   • Protección contra ataques DDoS
   • Validación de User-Agent obligatoria

⚙️ Configuración:
   • Dominio: $DOMAIN
   • Puerto HTTP: 80 (redirige a HTTPS)
   • Puerto HTTPS: 443
   • Puerto coordinador: 8000 (interno)
   • Usuario del sistema: $COORDINATOR_USER

⏱️ Tiempo estimado de instalación: 10-15 minutos

EOF

    read -p "¿Continuar con la instalación? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Instalación cancelada por el usuario"
        exit 0
    fi
}

# Ejecutar instalación básica
run_basic_installation() {
    header "Ejecutando Instalación Básica"
    
    log "Ejecutando script de despliegue básico..."
    
    # Hacer ejecutable el script de despliegue
    chmod +x "$(dirname "$0")/deploy_coordinator_ubuntu.sh"
    
    # Ejecutar con el dominio especificado
    DOMAIN="$DOMAIN" "$(dirname "$0")/deploy_coordinator_ubuntu.sh"
    
    log "✅ Instalación básica completada"
}

# Ejecutar protecciones avanzadas
run_advanced_protection() {
    header "Configurando Protecciones Avanzadas"
    
    log "Ejecutando configuración de protecciones avanzadas..."
    
    # Hacer ejecutable el script de protecciones
    chmod +x "$(dirname "$0")/configure_advanced_protection.sh"
    
    # Ejecutar configuración avanzada
    "$(dirname "$0")/configure_advanced_protection.sh"
    
    log "✅ Protecciones avanzadas configuradas"
}

# Crear configuración de producción
create_production_config() {
    header "Configurando Entorno de Producción"
    
    log "Creando configuración de producción..."
    
    # Configurar variables de entorno
    cat > "$COORDINATOR_HOME/.env" << EOF
# PlayerGold Network Coordinator - Production Configuration
NODE_ENV=production
DOMAIN=$DOMAIN
COORDINATOR_PORT=8000
SSL_PORT=443

# Security
HMAC_SECRET=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Monitoring
ENABLE_MONITORING=true
ENABLE_ALERTS=true
ALERT_EMAIL=admin@$DOMAIN

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30

# Database
DB_PATH=$COORDINATOR_HOME/data/coordinator.db
BACKUP_RETENTION_DAYS=7
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/.env"
    chmod 600 "$COORDINATOR_HOME/.env"
    
    log "✅ Configuración de producción creada"
}

# Configurar backups automáticos
configure_backups() {
    header "Configurando Backups Automáticos"
    
    log "Configurando sistema de backups..."
    
    # Crear script de backup
    cat > "$COORDINATOR_HOME/backup.sh" << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/playergold/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="coordinator_backup_$DATE.tar.gz"

# Crear directorio de backups
mkdir -p "$BACKUP_DIR"

# Crear backup
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude="$COORDINATOR_HOME/logs/*.log" \
    --exclude="$COORDINATOR_HOME/venv" \
    "$COORDINATOR_HOME/data" \
    "$COORDINATOR_HOME/src" \
    "$COORDINATOR_HOME/.env"

# Mantener solo los últimos 7 backups
find "$BACKUP_DIR" -name "coordinator_backup_*.tar.gz" -mtime +7 -delete

echo "$(date): Backup created: $BACKUP_FILE" >> "$COORDINATOR_HOME/logs/backup.log"
EOF

    chmod +x "$COORDINATOR_HOME/backup.sh"
    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/backup.sh"
    
    # Configurar cron para backup diario
    (crontab -u "$COORDINATOR_USER" -l 2>/dev/null; echo "0 2 * * * $COORDINATOR_HOME/backup.sh") | crontab -u "$COORDINATOR_USER" -
    
    log "✅ Backups automáticos configurados (diarios a las 2:00 AM)"
}

# Configurar alertas por email
configure_email_alerts() {
    header "Configurando Alertas por Email"
    
    log "Instalando sistema de alertas por email..."
    
    # Instalar mailutils
    apt install -y mailutils postfix
    
    # Configurar script de alertas
    cat > "$COORDINATOR_HOME/send_alert.sh" << 'EOF'
#!/bin/bash

ALERT_TYPE="$1"
ALERT_MESSAGE="$2"
ALERT_EMAIL="${3:-admin@playergold.es}"

SUBJECT="[PlayerGold Coordinator] Alert: $ALERT_TYPE"

BODY="
PlayerGold Network Coordinator Alert

Type: $ALERT_TYPE
Time: $(date)
Server: $(hostname)
Message: $ALERT_MESSAGE

---
This is an automated alert from the PlayerGold Network Coordinator.
"

echo "$BODY" | mail -s "$SUBJECT" "$ALERT_EMAIL"
EOF

    chmod +x "$COORDINATOR_HOME/send_alert.sh"
    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/send_alert.sh"
    
    log "✅ Sistema de alertas por email configurado"
}

# Verificar instalación
verify_installation() {
    header "Verificando Instalación"
    
    log "Verificando servicios..."
    
    # Verificar servicios activos
    local services=("nginx" "playergold-coordinator" "ufw" "fail2ban")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log "✅ $service está activo"
        else
            error "❌ $service no está activo"
        fi
    done
    
    # Verificar puertos abiertos
    log "Verificando puertos..."
    if netstat -tlnp | grep -q ":80 "; then
        log "✅ Puerto 80 (HTTP) abierto"
    fi
    
    if netstat -tlnp | grep -q ":443 "; then
        log "✅ Puerto 443 (HTTPS) abierto"
    fi
    
    if netstat -tlnp | grep -q ":8000 "; then
        log "✅ Puerto 8000 (Coordinador) abierto"
    fi
    
    # Verificar API
    log "Verificando API del coordinador..."
    sleep 5  # Esperar a que el servicio esté completamente listo
    
    if curl -s -f "http://localhost:8000/api/v1/health" > /dev/null; then
        log "✅ API del coordinador respondiendo"
    else
        warning "⚠️ API del coordinador no responde (puede necesitar unos minutos más)"
    fi
    
    # Verificar SSL (si está configurado)
    if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
        log "✅ Certificado SSL configurado"
    else
        warning "⚠️ Certificado SSL no configurado (configurar manualmente si es necesario)"
    fi
}

# Mostrar resumen final
show_final_summary() {
    header "Instalación Completada"
    
    cat << EOF
🎉 ¡PlayerGold Network Coordinator instalado correctamente!

🌐 URLs de acceso:
   • API Principal: https://$DOMAIN/api/v1/health
   • Dashboard: https://$DOMAIN/dashboard
   • Nginx Status: https://$DOMAIN/nginx_status (si está habilitado)

📊 Monitoreo y administración:
   • Logs del coordinador: journalctl -u playergold-coordinator -f
   • Logs de Nginx: tail -f /var/log/nginx/playergold-*.log
   • Logs de aplicación: tail -f $COORDINATOR_HOME/logs/coordinator.log
   • Estado de servicios: systemctl status playergold-coordinator

🔒 Seguridad configurada:
   • Firewall UFW activo
   • Fail2ban protegiendo contra ataques
   • Rate limiting por IP y endpoint
   • Validación obligatoria de User-Agent
   • Blacklist/whitelist automática

📋 Archivos importantes:
   • Configuración: $COORDINATOR_HOME/.env
   • Datos: $COORDINATOR_HOME/data/
   • Logs: $COORDINATOR_HOME/logs/
   • Backups: $COORDINATOR_HOME/backups/

⚙️ Comandos útiles:
   • Reiniciar coordinador: sudo systemctl restart playergold-coordinator
   • Ver estado: sudo systemctl status playergold-coordinator
   • Ver logs en vivo: sudo journalctl -u playergold-coordinator -f
   • Backup manual: sudo -u $COORDINATOR_USER $COORDINATOR_HOME/backup.sh

🚨 Próximos pasos recomendados:
   1. Configurar DNS para que $DOMAIN apunte a este servidor
   2. Obtener certificado SSL: sudo certbot --nginx -d $DOMAIN
   3. Configurar alertas por email en $COORDINATOR_HOME/.env
   4. Revisar logs regularmente
   5. Configurar monitoreo externo (opcional)

📧 Soporte:
   • Logs de errores: $COORDINATOR_HOME/logs/coordinator.log
   • Alertas: $COORDINATOR_HOME/logs/alerts.log
   • Backups automáticos: Diarios a las 2:00 AM

EOF

    info "La instalación ha sido completada exitosamente."
    info "El coordinador está listo para recibir conexiones de wallets PlayerGold."
    
    warning "IMPORTANTE: Asegúrate de que el dominio $DOMAIN apunte a este servidor"
    warning "y configura el certificado SSL si no se hizo automáticamente."
}

# Función principal
main() {
    clear
    
    header "PlayerGold Network Coordinator - Instalación Completa"
    
    check_prerequisites
    show_installation_info
    
    log "🚀 Iniciando instalación completa..."
    
    # Fase 1: Instalación básica
    run_basic_installation
    
    # Fase 2: Protecciones avanzadas
    run_advanced_protection
    
    # Fase 3: Configuración de producción
    create_production_config
    
    # Fase 4: Backups automáticos
    configure_backups
    
    # Fase 5: Alertas por email
    configure_email_alerts
    
    # Fase 6: Verificación
    verify_installation
    
    # Resumen final
    show_final_summary
    
    log "🎉 ¡Instalación completa finalizada!"
}

# Ejecutar instalación
main "$@"
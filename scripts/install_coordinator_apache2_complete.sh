#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Instalación Completa Ubuntu (Apache2)
# ============================================================================
# 
# Script de instalación completa que usa Apache2 existente:
# - Despliegue básico del coordinador
# - Protecciones avanzadas anti-DDoS
# - Validación de wallets legítimos
# - Usa Apache2 existente como proxy reverso
# - Monitoreo y alertas
# - Dashboard de administración
#
# Uso: sudo ./install_coordinator_apache2_complete.sh [dominio]
# Ejemplo: sudo ./install_coordinator_apache2_complete.sh playergold.es
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
    
    # Verificar Apache2
    if ! systemctl is-active --quiet apache2; then
        error "Apache2 no está corriendo. Este script requiere Apache2 activo."
        error "Por favor, inicia Apache2 primero: sudo systemctl start apache2"
        exit 1
    fi
    
    log "✅ Apache2 está corriendo"
    
    # Verificar SSL
    if [[ -d "/etc/letsencrypt/live/$DOMAIN" ]] || [[ -f "/etc/ssl/certs/$DOMAIN.crt" ]]; then
        log "✅ Certificado SSL encontrado para $DOMAIN"
    else
        warning "No se encontró certificado SSL para $DOMAIN"
        warning "El coordinador funcionará, pero se recomienda SSL para producción"
    fi
    
    # Verificar conectividad a internet
    if ! ping -c 1 google.com &> /dev/null; then
        error "No hay conectividad a internet"
        exit 1
    fi
    
    log "✅ Conectividad a internet verificada"
    
    info "Dominio configurado: $DOMAIN"
    info "Usuario del sistema: $COORDINATOR_USER"
    info "Directorio de instalación: $COORDINATOR_HOME"
    info "Servidor web: Apache2 (existente)"
}

# Mostrar información de instalación
show_installation_info() {
    header "Información de Instalación"
    
    cat << EOF
🎮 PlayerGold Network Coordinator - Instalación Completa (Apache2)

📋 Componentes que se instalarán:
   • Coordinador de red con API FastAPI
   • Protección anti-DDoS avanzada
   • Validación criptográfica de wallets
   • Firewall UFW + iptables + fail2ban
   • Apache2 como proxy reverso (usando existente)
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
   • Puerto HTTP: 80 (Apache2 existente)
   • Puerto HTTPS: 443 (Apache2 existente)
   • Puerto coordinador: 8000 (interno)
   • Usuario del sistema: $COORDINATOR_USER
   • Servidor web: Apache2 (reutiliza configuración existente)

⏱️ Tiempo estimado de instalación: 8-12 minutos

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
    header "Ejecutando Instalación Básica (Apache2)"
    
    log "Ejecutando script de despliegue básico para Apache2..."
    
    # Hacer ejecutable el script de despliegue
    chmod +x "$(dirname "$0")/deploy_coordinator_apache2.sh"
    
    # Ejecutar con el dominio especificado
    DOMAIN="$DOMAIN" "$(dirname "$0")/deploy_coordinator_apache2.sh"
    
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
# PlayerGold Network Coordinator - Production Configuration (Apache2)
NODE_ENV=production
DOMAIN=$DOMAIN
COORDINATOR_PORT=8000
PROXY_SERVER=apache2

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

# Apache2 Integration
APACHE_LOG_PATH=/var/log/apache2/playergold-access.log
APACHE_ERROR_LOG=/var/log/apache2/playergold-error.log
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/.env"
    chmod 600 "$COORDINATOR_HOME/.env"
    
    log "✅ Configuración de producción creada"
}

# Configurar Apache2 adicional
configure_apache2_additional() {
    header "Configuración Adicional de Apache2"
    
    log "Configurando módulos adicionales de Apache2..."
    
    # Instalar y habilitar mod_evasive si está disponible
    if apt list --installed 2>/dev/null | grep -q libapache2-mod-evasive; then
        log "mod_evasive ya está instalado"
    else
        log "Instalando mod_evasive para protección DDoS..."
        apt install -y libapache2-mod-evasive
    fi
    
    # Configurar mod_evasive
    if [[ -f "/etc/apache2/mods-available/evasive.conf" ]]; then
        cat > /etc/apache2/mods-available/evasive.conf << 'EOF'
<IfModule mod_evasive24.c>
    DOSHashTableSize    2048
    DOSPageCount        10
    DOSSiteCount        50
    DOSPageInterval     1
    DOSSiteInterval     1
    DOSBlockingPeriod   600
    DOSLogDir           /var/log/apache2/
    DOSEmailNotify      admin@playergold.es
    DOSWhitelist        127.0.0.1
    DOSWhitelist        ::1
</IfModule>
EOF
        a2enmod evasive
        log "✅ mod_evasive configurado"
    fi
    
    # Habilitar mod_security si está disponible
    if apt list --installed 2>/dev/null | grep -q libapache2-mod-security2; then
        log "mod_security ya está instalado"
        a2enmod security2
    else
        log "Instalando mod_security para protección adicional..."
        apt install -y libapache2-mod-security2
        a2enmod security2
    fi
    
    # Configurar headers de seguridad adicionales
    cat > /etc/apache2/conf-available/playergold-security.conf << 'EOF'
# PlayerGold Security Headers
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

# Ocultar información del servidor
ServerTokens Prod
ServerSignature Off
EOF

    a2enconf playergold-security
    
    # Recargar Apache2
    systemctl reload apache2
    
    log "✅ Configuración adicional de Apache2 completada"
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
    "$COORDINATOR_HOME/.env" \
    /etc/apache2/sites-available/playergold-coordinator.conf \
    /etc/apache2/conf-available/playergold-security.conf

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

# Verificar instalación
verify_installation() {
    header "Verificando Instalación"
    
    log "Verificando servicios..."
    
    # Verificar servicios activos
    local services=("apache2" "playergold-coordinator" "ufw" "fail2ban")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log "✅ $service está activo"
        else
            error "❌ $service no está activo"
        fi
    done
    
    # Verificar puertos abiertos
    log "Verificando puertos..."
    if netstat -tlnp | grep -q ":80.*apache2"; then
        log "✅ Puerto 80 (HTTP) abierto en Apache2"
    fi
    
    if netstat -tlnp | grep -q ":443.*apache2"; then
        log "✅ Puerto 443 (HTTPS) abierto en Apache2"
    fi
    
    if netstat -tlnp | grep -q ":8000.*python"; then
        log "✅ Puerto 8000 (Coordinador) abierto"
    fi
    
    # Verificar API a través de Apache2
    log "Verificando API del coordinador a través de Apache2..."
    sleep 5  # Esperar a que el servicio esté completamente listo
    
    # Test directo al coordinador
    if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" "http://127.0.0.1:8000/api/v1/health" > /dev/null; then
        log "✅ API del coordinador respondiendo directamente"
    else
        warning "⚠️ API del coordinador no responde directamente"
    fi
    
    # Test a través de Apache2
    if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" "https://$DOMAIN/api/v1/health" > /dev/null 2>&1; then
        log "✅ API del coordinador respondiendo a través de Apache2 HTTPS"
    elif curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" "http://$DOMAIN/api/v1/health" > /dev/null 2>&1; then
        log "✅ API del coordinador respondiendo a través de Apache2 HTTP"
    else
        warning "⚠️ API del coordinador no responde a través de Apache2"
    fi
    
    # Verificar configuración de Apache2
    if apache2ctl configtest &>/dev/null; then
        log "✅ Configuración de Apache2 válida"
    else
        warning "⚠️ Problemas en la configuración de Apache2"
    fi
}

# Mostrar resumen final
show_final_summary() {
    header "Instalación Completada"
    
    cat << EOF
🎉 ¡PlayerGold Network Coordinator instalado correctamente con Apache2!

🌐 URLs de acceso:
   • API Principal: https://$DOMAIN/api/v1/health
   • Dashboard: https://$DOMAIN/dashboard
   • Admin Stats: https://$DOMAIN/admin/stats (solo localhost)

📊 Monitoreo y administración:
   • Logs del coordinador: journalctl -u playergold-coordinator -f
   • Logs de Apache2: tail -f /var/log/apache2/playergold-*.log
   • Logs de aplicación: tail -f $COORDINATOR_HOME/logs/coordinator.log
   • Estado de servicios: systemctl status playergold-coordinator apache2

🔒 Seguridad configurada:
   • Firewall UFW activo
   • Fail2ban protegiendo contra ataques
   • Apache2 con mod_evasive y mod_security
   • Rate limiting por IP y endpoint
   • Validación obligatoria de User-Agent
   • Blacklist/whitelist automática

📋 Archivos importantes:
   • Configuración: $COORDINATOR_HOME/.env
   • Datos: $COORDINATOR_HOME/data/
   • Logs: $COORDINATOR_HOME/logs/
   • Backups: $COORDINATOR_HOME/backups/
   • Apache2 config: /etc/apache2/sites-available/playergold-coordinator.conf

⚙️ Comandos útiles:
   • Reiniciar coordinador: sudo systemctl restart playergold-coordinator
   • Reiniciar Apache2: sudo systemctl restart apache2
   • Ver estado: sudo systemctl status playergold-coordinator apache2
   • Ver logs en vivo: sudo journalctl -u playergold-coordinator -f
   • Backup manual: sudo -u $COORDINATOR_USER $COORDINATOR_HOME/backup.sh

🚨 Próximos pasos recomendados:
   1. Verificar que $DOMAIN apunte a este servidor
   2. Probar la API: curl -H "User-Agent: PlayerGold-Wallet/1.0.0" https://$DOMAIN/api/v1/health
   3. Configurar alertas por email en $COORDINATOR_HOME/.env
   4. Revisar logs regularmente
   5. Configurar monitoreo externo (opcional)

📧 Integración con Apache2:
   • El coordinador se ejecuta en puerto 8000 (interno)
   • Apache2 actúa como proxy reverso en puertos 80/443
   • SSL/TLS manejado por Apache2 (configuración existente)
   • Logs integrados con Apache2
   • Protección DDoS en múltiples capas

EOF

    info "La instalación ha sido completada exitosamente."
    info "El coordinador está integrado con tu Apache2 existente."
    
    warning "IMPORTANTE: Verifica que las peticiones lleguen correctamente:"
    warning "curl -H 'User-Agent: PlayerGold-Wallet/1.0.0' https://$DOMAIN/api/v1/health"
}

# Función principal
main() {
    clear
    
    header "PlayerGold Network Coordinator - Instalación Completa (Apache2)"
    
    check_prerequisites
    show_installation_info
    
    log "🚀 Iniciando instalación completa con Apache2..."
    
    # Fase 1: Instalación básica
    run_basic_installation
    
    # Fase 2: Protecciones avanzadas
    run_advanced_protection
    
    # Fase 3: Configuración de producción
    create_production_config
    
    # Fase 4: Configuración adicional de Apache2
    configure_apache2_additional
    
    # Fase 5: Backups automáticos
    configure_backups
    
    # Fase 6: Verificación
    verify_installation
    
    # Resumen final
    show_final_summary
    
    log "🎉 ¡Instalación completa con Apache2 finalizada!"
}

# Ejecutar instalación
main "$@"
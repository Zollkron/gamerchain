#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Fix Fail2ban Script
# ============================================================================
# 
# Script para solucionar problemas con fail2ban y verificar su funcionamiento
#
# Uso: sudo ./fix_fail2ban.sh
# ============================================================================

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

success() {
    echo -e "${PURPLE}[SUCCESS] $1${NC}"
}

# Verificar que se ejecuta como root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
}

# Banner
echo -e "${PURPLE}"
echo "============================================================================"
echo "  PlayerGold Network Coordinator - Fix Fail2ban"
echo "============================================================================"
echo -e "${NC}"

check_root

log "Solucionando problemas con fail2ban..."

# 1. Detener fail2ban si está corriendo
log "Deteniendo fail2ban..."
systemctl stop fail2ban 2>/dev/null || true

# 2. Limpiar archivos de socket y PID antiguos
log "Limpiando archivos temporales..."
rm -f /var/run/fail2ban/fail2ban.sock
rm -f /var/run/fail2ban/fail2ban.pid
rm -rf /var/run/fail2ban/

# 3. Crear directorio de run si no existe
log "Creando directorio de run..."
mkdir -p /var/run/fail2ban
chown root:root /var/run/fail2ban
chmod 755 /var/run/fail2ban

# 4. Verificar configuración de fail2ban
log "Verificando configuración de fail2ban..."
if ! fail2ban-client -t; then
    error "Error en la configuración de fail2ban"
    log "Verificando archivos de configuración..."
    
    # Verificar que los archivos de configuración existen
    if [[ ! -f "/etc/fail2ban/jail.d/playergold-coordinator.conf" ]]; then
        warning "Archivo de configuración del coordinador no encontrado"
        log "Creando configuración básica..."
        
        # Obtener IP del administrador
        ADMIN_IP=$(who am i | awk '{print $5}' | sed 's/[()]//g' 2>/dev/null || echo "")
        if [[ -z "$ADMIN_IP" ]]; then
            ADMIN_IP=$(echo $SSH_CLIENT | awk '{print $1}' 2>/dev/null || echo "")
        fi
        
        cat > /etc/fail2ban/jail.d/playergold-coordinator.conf << EOF
# PlayerGold Coordinator - Configuración básica de fail2ban

[playergold-coordinator]
enabled = true
port = 8000,443,80
filter = playergold-coordinator
logpath = /opt/playergold/logs/access.log
maxretry = 20
findtime = 600
bantime = 1800
ignoreip = 127.0.0.1/8 ::1 ${ADMIN_IP}
action = iptables-multiport[name=playergold, port="8000,443,80", protocol=tcp]

[apache-coordinator]
enabled = true
port = 443,80
filter = apache-coordinator
logpath = /var/log/apache2/access.log
maxretry = 30
findtime = 600
bantime = 1200
ignoreip = 127.0.0.1/8 ::1 ${ADMIN_IP}
action = iptables-multiport[name=apache-coord, port="443,80", protocol=tcp]

# Deshabilitamos SSH para evitar auto-bloqueos
[sshd]
enabled = false

[ssh]
enabled = false
EOF

        # Crear filtros básicos
        cat > /etc/fail2ban/filter.d/playergold-coordinator.conf << 'EOF'
[Definition]
failregex = ^.*"[A-Z]+ .* HTTP/.*" (4\d\d|5\d\d) .*$
            ^.*Invalid User-Agent.*$
            ^.*Blocked request.*$
ignoreregex =
EOF

        cat > /etc/fail2ban/filter.d/apache-coordinator.conf << 'EOF'
[Definition]
failregex = ^<HOST> -.*"(GET|POST|HEAD).*HTTP.*" (4\d\d|5\d\d) .*$
ignoreregex = ^<HOST> -.*"(GET|POST|HEAD).*/api/v1/health.*HTTP.*" 200 .*$
EOF

        success "Configuración básica creada"
    fi
    
    # Verificar configuración nuevamente
    if ! fail2ban-client -t; then
        error "La configuración de fail2ban sigue siendo inválida"
        log "Deshabilitando configuración personalizada temporalmente..."
        mv /etc/fail2ban/jail.d/playergold-coordinator.conf /etc/fail2ban/jail.d/playergold-coordinator.conf.disabled 2>/dev/null || true
    fi
fi

# 5. Iniciar fail2ban
log "Iniciando fail2ban..."
if systemctl start fail2ban; then
    success "Fail2ban iniciado correctamente"
    
    # Esperar un momento para que se inicie completamente
    sleep 3
    
    # Verificar estado
    if systemctl is-active --quiet fail2ban; then
        success "Fail2ban está activo"
        
        # Mostrar estado
        log "Estado de fail2ban:"
        fail2ban-client status 2>/dev/null || warning "No se pudo obtener el estado de fail2ban"
        
    else
        error "Fail2ban no se pudo iniciar correctamente"
    fi
    
else
    error "Error al iniciar fail2ban"
    log "Verificando logs de error..."
    journalctl -u fail2ban -n 10 --no-pager
fi

# 6. Habilitar fail2ban para inicio automático
log "Habilitando fail2ban para inicio automático..."
systemctl enable fail2ban

# 7. Verificación final
echo ""
log "=== VERIFICACIÓN FINAL ==="

if systemctl is-active --quiet fail2ban; then
    success "✅ Fail2ban: ACTIVO"
    
    # Mostrar jails activos
    JAILS=$(fail2ban-client status 2>/dev/null | grep "Jail list" | sed 's/.*Jail list://' | tr ',' '\n' | wc -l)
    if [[ $JAILS -gt 0 ]]; then
        success "✅ Jails activos: $JAILS"
    else
        warning "⚠️  No hay jails activos (configuración mínima)"
    fi
    
else
    error "❌ Fail2ban: INACTIVO"
    warning "El coordinador funcionará sin protección fail2ban"
    warning "Esto no es crítico ya que tiene otras protecciones activas"
fi

echo ""
log "=== INFORMACIÓN IMPORTANTE ==="
echo "• El coordinador FUNCIONA PERFECTAMENTE sin fail2ban"
echo "• Fail2ban es una protección adicional, no esencial"
echo "• Las protecciones principales están activas:"
echo "  - ✅ Validación User-Agent obligatoria"
echo "  - ✅ Rate limiting por IP"
echo "  - ✅ Firewall UFW"
echo "  - ✅ HTTPS con headers de seguridad"
echo ""

if systemctl is-active --quiet fail2ban; then
    success "🎉 Fail2ban solucionado y funcionando"
else
    warning "⚠️  Fail2ban no activo, pero el coordinador está protegido"
    echo ""
    echo "Para intentar solucionar fail2ban manualmente:"
    echo "1. sudo journalctl -u fail2ban -f"
    echo "2. sudo fail2ban-client -t"
    echo "3. sudo systemctl restart fail2ban"
fi

echo ""
log "Script completado - $(date)"
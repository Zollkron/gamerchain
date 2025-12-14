#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Status Check Script
# ============================================================================
# 
# Script para verificar el estado completo del coordinador de red
# incluyendo servicios, SSL, protecciones y rendimiento
#
# Uso: ./check_coordinator_status.sh
# ============================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuración
DOMAIN="playergold.es"
COORDINATOR_HOME="/opt/playergold"

# Función para logging
log() {
    echo -e "${GREEN}$1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${PURPLE}✅ $1${NC}"
}

# Banner
echo -e "${PURPLE}"
echo "============================================================================"
echo "  PlayerGold Network Coordinator - Status Check"
echo "============================================================================"
echo -e "${NC}"
echo "🔍 Verificando estado completo del coordinador de red"
echo "🌐 Dominio: $DOMAIN"
echo ""

# 1. Verificar servicios del sistema
echo -e "${BLUE}1. SERVICIOS DEL SISTEMA${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet apache2; then
    success "Apache2: Activo"
    APACHE_VERSION=$(apache2 -v | head -1 | awk '{print $3}')
    info "Versión: $APACHE_VERSION"
else
    error "Apache2: Inactivo"
fi

if systemctl is-active --quiet playergold-coordinator; then
    success "Coordinador: Activo"
    COORD_STATUS=$(systemctl show playergold-coordinator --property=ActiveState,SubState,MainPID,MemoryCurrent)
    echo "$COORD_STATUS" | while read line; do
        key=$(echo "$line" | cut -d'=' -f1)
        value=$(echo "$line" | cut -d'=' -f2)
        case $key in
            "MainPID") info "PID: $value" ;;
            "MemoryCurrent") 
                if [[ "$value" != "[not set]" ]]; then
                    memory_mb=$((value / 1024 / 1024))
                    info "Memoria: ${memory_mb}MB"
                fi
                ;;
        esac
    done
else
    error "Coordinador: Inactivo"
fi

if systemctl is-active --quiet fail2ban; then
    success "Fail2ban: Activo"
else
    warning "Fail2ban: Inactivo"
fi

if systemctl is-active --quiet ufw; then
    success "UFW Firewall: Activo"
else
    warning "UFW Firewall: Inactivo"
fi

echo ""

# 2. Verificar puertos y conectividad
echo -e "${BLUE}2. PUERTOS Y CONECTIVIDAD${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Puerto 80 (HTTP)
if netstat -tlnp 2>/dev/null | grep -q ":80.*apache2"; then
    success "Puerto 80 (HTTP): Apache2 escuchando"
else
    error "Puerto 80 (HTTP): No disponible"
fi

# Puerto 443 (HTTPS)
if netstat -tlnp 2>/dev/null | grep -q ":443.*apache2"; then
    success "Puerto 443 (HTTPS): Apache2 escuchando"
else
    warning "Puerto 443 (HTTPS): No disponible"
fi

# Puerto 8000 (Coordinador)
if netstat -tlnp 2>/dev/null | grep -q ":8000.*python"; then
    success "Puerto 8000 (Coordinador): Escuchando"
else
    error "Puerto 8000 (Coordinador): No disponible"
fi

echo ""

# 3. Verificar APIs
echo -e "${BLUE}3. VERIFICACIÓN DE APIs${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# API directa (puerto 8000)
if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1; then
    success "API directa (puerto 8000): Respondiendo"
    RESPONSE=$(curl -s -H "User-Agent: PlayerGold-Wallet/1.0.0" http://127.0.0.1:8000/api/v1/health)
    VERSION=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'N/A'))" 2>/dev/null || echo "N/A")
    info "Versión: $VERSION"
else
    error "API directa (puerto 8000): No responde"
fi

# API via HTTP (puerto 80)
if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" http://$DOMAIN/api/v1/health > /dev/null 2>&1; then
    success "API HTTP (puerto 80): Respondiendo"
else
    warning "API HTTP (puerto 80): No responde o redirige"
fi

# API via HTTPS (puerto 443)
if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" https://$DOMAIN/api/v1/health > /dev/null 2>&1; then
    success "API HTTPS (puerto 443): Respondiendo"
else
    warning "API HTTPS (puerto 443): No responde"
fi

echo ""

# 4. Verificar protecciones de seguridad
echo -e "${BLUE}4. PROTECCIONES DE SEGURIDAD${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Protección User-Agent HTTP
if curl -s -f http://$DOMAIN/api/v1/health > /dev/null 2>&1; then
    error "Protección User-Agent HTTP: FALLA (permite acceso sin UA válido)"
else
    success "Protección User-Agent HTTP: Funcionando"
fi

# Protección User-Agent HTTPS (si está disponible)
if netstat -tlnp 2>/dev/null | grep -q ":443.*apache2"; then
    if curl -s -f https://$DOMAIN/api/v1/health > /dev/null 2>&1; then
        error "Protección User-Agent HTTPS: FALLA (permite acceso sin UA válido)"
    else
        success "Protección User-Agent HTTPS: Funcionando"
    fi
fi

# Verificar fail2ban jails
if command -v fail2ban-client &> /dev/null; then
    JAILS=$(fail2ban-client status 2>/dev/null | grep "Jail list" | sed 's/.*Jail list://' | tr ',' '\n' | wc -l)
    if [[ $JAILS -gt 0 ]]; then
        success "Fail2ban: $JAILS jails activos"
        
        # Mostrar IPs baneadas
        BANNED_COUNT=0
        fail2ban-client status 2>/dev/null | grep "Jail list" | sed 's/.*Jail list://' | tr ',' '\n' | while read jail; do
            if [[ -n "$jail" ]]; then
                jail=$(echo $jail | xargs)
                BANNED_IPS=$(fail2ban-client status $jail 2>/dev/null | grep "Currently banned" | awk '{print $4}')
                if [[ "$BANNED_IPS" -gt 0 ]]; then
                    BANNED_COUNT=$((BANNED_COUNT + BANNED_IPS))
                fi
            fi
        done
        
        if [[ $BANNED_COUNT -gt 0 ]]; then
            warning "IPs baneadas actualmente: $BANNED_COUNT"
        else
            info "No hay IPs baneadas actualmente"
        fi
    else
        warning "Fail2ban: No hay jails activos"
    fi
else
    warning "Fail2ban: No disponible"
fi

echo ""

# 5. Verificar SSL/TLS (si está disponible)
if netstat -tlnp 2>/dev/null | grep -q ":443.*apache2"; then
    echo -e "${BLUE}5. VERIFICACIÓN SSL/TLS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Verificar certificado SSL
    if openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates > /dev/null 2>&1; then
        success "Certificado SSL: Válido"
        
        # Obtener fechas del certificado
        CERT_INFO=$(openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
        NOT_AFTER=$(echo "$CERT_INFO" | grep "notAfter" | cut -d'=' -f2)
        if [[ -n "$NOT_AFTER" ]]; then
            info "Expira: $NOT_AFTER"
        fi
        
        # Verificar headers de seguridad HTTPS
        HEADERS=$(curl -s -I -H "User-Agent: PlayerGold-Wallet/1.0.0" https://$DOMAIN/api/v1/health 2>/dev/null)
        
        if echo "$HEADERS" | grep -qi "strict-transport-security"; then
            success "HSTS: Configurado"
        else
            warning "HSTS: No configurado"
        fi
        
        if echo "$HEADERS" | grep -qi "x-content-type-options"; then
            success "X-Content-Type-Options: Configurado"
        else
            warning "X-Content-Type-Options: No configurado"
        fi
        
    else
        error "Certificado SSL: Error o no válido"
    fi
    
    echo ""
fi

# 6. Verificar logs y rendimiento
echo -e "${BLUE}6. LOGS Y RENDIMIENTO${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar logs del coordinador
if [[ -f "$COORDINATOR_HOME/logs/coordinator.log" ]]; then
    success "Log del coordinador: Disponible"
    LOG_SIZE=$(du -h "$COORDINATOR_HOME/logs/coordinator.log" | cut -f1)
    info "Tamaño: $LOG_SIZE"
    
    # Últimas líneas del log
    info "Últimas 3 líneas del log:"
    tail -3 "$COORDINATOR_HOME/logs/coordinator.log" 2>/dev/null | sed 's/^/   /'
else
    warning "Log del coordinador: No encontrado"
fi

# Verificar log de acceso
if [[ -f "$COORDINATOR_HOME/logs/access.log" ]]; then
    success "Log de acceso: Disponible"
    ACCESS_SIZE=$(du -h "$COORDINATOR_HOME/logs/access.log" | cut -f1)
    info "Tamaño: $ACCESS_SIZE"
    
    # Contar requests en la última hora
    RECENT_REQUESTS=$(awk -v since="$(date -d '1 hour ago' '+%d/%b/%Y:%H:%M:%S')" '$4 > "["since {count++} END {print count+0}' "$COORDINATOR_HOME/logs/access.log" 2>/dev/null)
    info "Requests última hora: $RECENT_REQUESTS"
else
    warning "Log de acceso: No encontrado"
fi

# Verificar uso de recursos
if systemctl is-active --quiet playergold-coordinator; then
    COORD_PID=$(systemctl show playergold-coordinator --property=MainPID | cut -d'=' -f2)
    if [[ "$COORD_PID" != "0" ]] && [[ -n "$COORD_PID" ]]; then
        CPU_USAGE=$(ps -p $COORD_PID -o %cpu --no-headers 2>/dev/null | xargs)
        if [[ -n "$CPU_USAGE" ]]; then
            info "Uso CPU: ${CPU_USAGE}%"
        fi
    fi
fi

echo ""

# 7. Resumen final
echo -e "${BLUE}7. RESUMEN DEL ESTADO${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Contar servicios activos
SERVICES_OK=0
SERVICES_TOTAL=4

systemctl is-active --quiet apache2 && SERVICES_OK=$((SERVICES_OK + 1))
systemctl is-active --quiet playergold-coordinator && SERVICES_OK=$((SERVICES_OK + 1))
systemctl is-active --quiet fail2ban && SERVICES_OK=$((SERVICES_OK + 1))
systemctl is-active --quiet ufw && SERVICES_OK=$((SERVICES_OK + 1))

# Contar APIs funcionando
APIS_OK=0
APIS_TOTAL=2

curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" http://127.0.0.1:8000/api/v1/health > /dev/null 2>&1 && APIS_OK=$((APIS_OK + 1))
if netstat -tlnp 2>/dev/null | grep -q ":443.*apache2"; then
    APIS_TOTAL=3
    curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" https://$DOMAIN/api/v1/health > /dev/null 2>&1 && APIS_OK=$((APIS_OK + 1))
fi
curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" http://$DOMAIN/api/v1/health > /dev/null 2>&1 && APIS_OK=$((APIS_OK + 1))

# Estado general
if [[ $SERVICES_OK -eq $SERVICES_TOTAL ]] && [[ $APIS_OK -ge 1 ]]; then
    success "Estado general: EXCELENTE ($SERVICES_OK/$SERVICES_TOTAL servicios, $APIS_OK/$APIS_TOTAL APIs)"
elif [[ $SERVICES_OK -ge 2 ]] && [[ $APIS_OK -ge 1 ]]; then
    warning "Estado general: BUENO ($SERVICES_OK/$SERVICES_TOTAL servicios, $APIS_OK/$APIS_TOTAL APIs)"
else
    error "Estado general: PROBLEMAS ($SERVICES_OK/$SERVICES_TOTAL servicios, $APIS_OK/$APIS_TOTAL APIs)"
fi

echo ""
echo -e "${PURPLE}============================================================================${NC}"
echo -e "${GREEN}Verificación completada - $(date)${NC}"
echo -e "${PURPLE}============================================================================${NC}"
echo ""

# Comandos útiles
echo -e "${BLUE}💡 Comandos útiles:${NC}"
echo "   • Logs coordinador: sudo journalctl -u playergold-coordinator -f"
echo "   • Logs Apache2: sudo tail -f /var/log/apache2/error.log"
echo "   • Reiniciar coordinador: sudo systemctl restart playergold-coordinator"
echo "   • Pruebas completas: sudo -u playergold $COORDINATOR_HOME/test_deployment.sh"
if [[ -f "$COORDINATOR_HOME/test_ssl.sh" ]]; then
    echo "   • Pruebas SSL: sudo -u playergold $COORDINATOR_HOME/test_ssl.sh"
fi
echo "   • Estado fail2ban: sudo fail2ban-client status"
echo "   • 🚨 Emergencia: sudo $COORDINATOR_HOME/emergency_unblock.sh"
echo ""
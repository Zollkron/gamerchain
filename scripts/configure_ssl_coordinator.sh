#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - SSL/HTTPS Configuration Script
# ============================================================================
# 
# Script para configurar SSL/HTTPS en el coordinador de red usando el
# certificado SSL existente de Apache2 en playergold.es
#
# Requisitos previos:
# - Coordinador ya desplegado y funcionando
# - Apache2 con SSL ya configurado para playergold.es
# - Certificados SSL existentes en el sistema
#
# Uso: sudo ./configure_ssl_coordinator.sh
# ============================================================================

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuración
DOMAIN="playergold.es"
COORDINATOR_USER="playergold"
COORDINATOR_HOME="/opt/playergold"
COORDINATOR_PORT="8000"

# Función para logging con timestamp
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR $(date +'%H:%M:%S')] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING $(date +'%H:%M:%S')] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO $(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${PURPLE}[SUCCESS $(date +'%H:%M:%S')] $1${NC}"
}

# Banner de inicio
show_banner() {
    echo -e "${PURPLE}"
    echo "============================================================================"
    echo "  PlayerGold Network Coordinator - SSL/HTTPS Configuration"
    echo "============================================================================"
    echo -e "${NC}"
    echo "🔒 Configurando SSL/HTTPS para el coordinador de red"
    echo "🌐 Dominio: $DOMAIN"
    echo "🔐 Usando certificados SSL existentes de Apache2"
    echo ""
}

# Verificar que se ejecuta como root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
}

# Verificar que el coordinador está funcionando
check_coordinator() {
    log "Verificando estado del coordinador..."
    
    if ! systemctl is-active --quiet playergold-coordinator; then
        error "El coordinador no está corriendo. Por favor, inicia el coordinador primero:"
        error "sudo systemctl start playergold-coordinator"
        exit 1
    fi
    
    if ! curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" http://127.0.0.1:8000/api/v1/health > /dev/null; then
        error "El coordinador no responde en el puerto 8000"
        exit 1
    fi
    
    success "Coordinador verificado correctamente"
}

# Verificar Apache2 y SSL existente
check_apache_ssl() {
    log "Verificando Apache2 y SSL existente..."
    
    if ! systemctl is-active --quiet apache2; then
        error "Apache2 no está corriendo"
        exit 1
    fi
    
    # Verificar que Apache2 está escuchando en puerto 443
    if ! netstat -tlnp | grep -q ":443.*apache2"; then
        error "Apache2 no está escuchando en puerto 443 (HTTPS)"
        error "Por favor, configura SSL en Apache2 primero"
        exit 1
    fi
    
    # Buscar certificados SSL existentes
    SSL_CERT_PATH=""
    SSL_KEY_PATH=""
    
    # Buscar en ubicaciones comunes de Let's Encrypt
    if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
        SSL_CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
        SSL_KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
        info "Encontrados certificados Let's Encrypt para $DOMAIN"
    elif [[ -f "/etc/ssl/certs/$DOMAIN.crt" ]]; then
        SSL_CERT_PATH="/etc/ssl/certs/$DOMAIN.crt"
        SSL_KEY_PATH="/etc/ssl/private/$DOMAIN.key"
        info "Encontrados certificados SSL personalizados para $DOMAIN"
    else
        # Buscar certificados en configuración de Apache2
        APACHE_SSL_CONF=$(grep -r "SSLCertificateFile" /etc/apache2/sites-enabled/ 2>/dev/null | head -1)
        if [[ -n "$APACHE_SSL_CONF" ]]; then
            SSL_CERT_PATH=$(echo "$APACHE_SSL_CONF" | awk '{print $2}')
            SSL_KEY_CONF=$(grep -r "SSLCertificateKeyFile" /etc/apache2/sites-enabled/ 2>/dev/null | head -1)
            SSL_KEY_PATH=$(echo "$SSL_KEY_CONF" | awk '{print $2}')
            info "Encontrados certificados SSL en configuración de Apache2"
        else
            error "No se encontraron certificados SSL válidos"
            error "Por favor, configura SSL en Apache2 primero o instala certificados Let's Encrypt"
            exit 1
        fi
    fi
    
    # Verificar que los archivos de certificados existen
    if [[ ! -f "$SSL_CERT_PATH" ]] || [[ ! -f "$SSL_KEY_PATH" ]]; then
        error "Los archivos de certificados SSL no existen:"
        error "Certificado: $SSL_CERT_PATH"
        error "Clave privada: $SSL_KEY_PATH"
        exit 1
    fi
    
    success "Certificados SSL encontrados:"
    info "Certificado: $SSL_CERT_PATH"
    info "Clave privada: $SSL_KEY_PATH"
}

# Actualizar configuración de Apache2 para HTTPS
configure_apache_https() {
    log "Configurando Apache2 para HTTPS del coordinador..."
    
    # Backup de la configuración actual
    cp /etc/apache2/sites-available/playergold-coordinator.conf /etc/apache2/sites-available/playergold-coordinator.conf.backup
    
    # Crear nueva configuración con HTTPS
    cat > /etc/apache2/sites-available/playergold-coordinator-ssl.conf << EOF
# PlayerGold Network Coordinator - HTTPS Configuration
# Configuración SSL para el coordinador de red

<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName $DOMAIN
    
    # Configuración SSL
    SSLEngine on
    SSLCertificateFile $SSL_CERT_PATH
    SSLCertificateKeyFile $SSL_KEY_PATH
    
    # Configuración SSL moderna y segura
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
    SSLHonorCipherOrder off
    SSLSessionTickets off
    
    # Headers de seguridad HTTPS
    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    
    # Configuración del coordinador con validación User-Agent
    <Location "/api/">
        # Validación de User-Agent obligatoria para wallets
        RewriteEngine On
        RewriteCond %{HTTP_USER_AGENT} !PlayerGold-Wallet [NC]
        RewriteRule .* - [F,L]
        
        # Proxy al coordinador
        ProxyPass http://127.0.0.1:8000/api/
        ProxyPassReverse http://127.0.0.1:8000/api/
        
        # Headers para el proxy
        ProxyPreserveHost On
        ProxyAddHeaders On
        
        # Pasar información SSL al backend
        RequestHeader set X-Forwarded-Proto "https"
        RequestHeader set X-Forwarded-Port "443"
        
        # Rate limiting básico
        <IfModule mod_limitipconn.c>
            MaxConnPerIP 10
        </IfModule>
    </Location>
    
    # Dashboard del coordinador (acceso más permisivo)
    <Location "/dashboard">
        # Validación básica (no bots)
        RewriteEngine On
        RewriteCond %{HTTP_USER_AGENT} ^$ [OR]
        RewriteCond %{HTTP_USER_AGENT} "bot|crawler|spider" [NC]
        RewriteRule .* - [F,L]
        
        ProxyPass http://127.0.0.1:8000/dashboard
        ProxyPassReverse http://127.0.0.1:8000/dashboard
        
        ProxyPreserveHost On
        ProxyAddHeaders On
        RequestHeader set X-Forwarded-Proto "https"
        RequestHeader set X-Forwarded-Port "443"
    </Location>
    
    # Admin endpoints (solo localhost y IPs específicas)
    <Location "/admin/">
        # Restricción de acceso por IP
        Require ip 127.0.0.1
        Require ip ::1
        # Añadir IPs de administración aquí si es necesario:
        # Require ip 192.168.1.100
        
        ProxyPass http://127.0.0.1:8000/admin/
        ProxyPassReverse http://127.0.0.1:8000/admin/
        
        ProxyPreserveHost On
        ProxyAddHeaders On
        RequestHeader set X-Forwarded-Proto "https"
        RequestHeader set X-Forwarded-Port "443"
    </Location>
    
    # Logs específicos para el coordinador
    ErrorLog \${APACHE_LOG_DIR}/playergold-coordinator-ssl-error.log
    CustomLog \${APACHE_LOG_DIR}/playergold-coordinator-ssl-access.log combined
    
</VirtualHost>
</IfModule>

# Redirección HTTP a HTTPS para el coordinador
<VirtualHost *:80>
    ServerName $DOMAIN
    
    # Solo redirigir rutas del coordinador, no toda la web
    RewriteEngine On
    RewriteCond %{REQUEST_URI} ^/api/ [OR]
    RewriteCond %{REQUEST_URI} ^/dashboard [OR]
    RewriteCond %{REQUEST_URI} ^/admin/
    RewriteRule ^(.*)$ https://%{HTTP_HOST}\$1 [R=301,L]
</VirtualHost>
EOF

    # Habilitar el sitio SSL
    a2ensite playergold-coordinator-ssl
    
    # Verificar configuración
    if ! apache2ctl configtest; then
        error "Error en la configuración SSL de Apache2"
        error "Restaurando configuración anterior..."
        a2dissite playergold-coordinator-ssl
        exit 1
    fi
    
    success "Configuración HTTPS de Apache2 creada"
}

# Configurar renovación automática de certificados (si es Let's Encrypt)
configure_cert_renewal() {
    if [[ "$SSL_CERT_PATH" == *"letsencrypt"* ]]; then
        log "Configurando renovación automática de certificados Let's Encrypt..."
        
        # Crear script de post-renovación para recargar Apache2
        cat > /etc/letsencrypt/renewal-hooks/post/reload-apache-coordinator.sh << 'EOF'
#!/bin/bash
# Script de post-renovación para recargar Apache2 después de renovar certificados

# Recargar Apache2
systemctl reload apache2

# Log de la renovación
echo "$(date): Certificados SSL renovados - Apache2 recargado" >> /opt/playergold/logs/ssl-renewal.log
EOF

        chmod +x /etc/letsencrypt/renewal-hooks/post/reload-apache-coordinator.sh
        
        # Verificar que certbot está configurado para renovación automática
        if systemctl is-enabled certbot.timer &>/dev/null; then
            success "Renovación automática de certificados configurada"
        else
            warning "certbot.timer no está habilitado. Habilitando renovación automática..."
            systemctl enable certbot.timer
            systemctl start certbot.timer
        fi
    else
        info "Certificados personalizados detectados - renovación automática no configurada"
        warning "Recuerda renovar manualmente los certificados SSL cuando expiren"
    fi
}

# Actualizar fail2ban para HTTPS
update_fail2ban_https() {
    log "Actualizando fail2ban para protección HTTPS..."
    
    # Actualizar configuración de fail2ban para incluir logs HTTPS
    cat >> /etc/fail2ban/jail.d/playergold-coordinator.conf << 'EOF'

# Protección adicional para HTTPS
[playergold-coordinator-ssl]
enabled = true
port = 443
filter = playergold-coordinator-ssl
logpath = /var/log/apache2/playergold-coordinator-ssl-access.log
maxretry = 15
findtime = 600
bantime = 1800
action = iptables-multiport[name=playergold-ssl, port="443", protocol=tcp]

[playergold-ddos-ssl]
enabled = true
port = 443
filter = playergold-ddos-ssl
logpath = /var/log/apache2/playergold-coordinator-ssl-access.log
maxretry = 100
findtime = 300
bantime = 3600
action = iptables-multiport[name=playergold-ddos-ssl, port="443", protocol=tcp]
EOF

    # Crear filtros para logs HTTPS
    cat > /etc/fail2ban/filter.d/playergold-coordinator-ssl.conf << 'EOF'
[Definition]
failregex = ^<HOST> -.*"[A-Z]+ .* HTTPS/.*" (4\d\d|5\d\d) .*$
            ^<HOST> -.*"[A-Z]+ .* HTTP/.*" (4\d\d|5\d\d) .*$
ignoreregex = ^<HOST> -.*"[A-Z]+ /api/v1/health .*" 200 .*$
EOF

    cat > /etc/fail2ban/filter.d/playergold-ddos-ssl.conf << 'EOF'
[Definition]
failregex = ^<HOST> -.*"(GET|POST|HEAD).*HTTP.*" (200|404|301|302) .*$
ignoreregex = ^<HOST> -.*"(GET|POST|HEAD).*/api/v1/health.*HTTP.*" 200 .*$
EOF

    # Reiniciar fail2ban
    systemctl restart fail2ban
    
    success "Fail2ban actualizado para protección HTTPS"
}

# Crear script de pruebas SSL
create_ssl_test_script() {
    log "Creando script de pruebas SSL..."
    
    cat > "$COORDINATOR_HOME/test_ssl.sh" << 'EOF'
#!/bin/bash

echo "🔒 Probando configuración SSL del PlayerGold Network Coordinator"
echo "=============================================================="

DOMAIN="playergold.es"

# Test 1: Verificar certificado SSL
echo "1. Verificando certificado SSL..."
if openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates; then
    echo "   ✅ Certificado SSL: Válido"
    echo "   📅 Fechas del certificado:"
    openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates | sed 's/^/      /'
else
    echo "   ❌ Certificado SSL: Error"
fi

# Test 2: Probar HTTPS API con wallet válido
echo ""
echo "2. Probando HTTPS API con wallet válido..."
if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" https://$DOMAIN/api/v1/health > /dev/null; then
    echo "   ✅ HTTPS API: Respondiendo"
    echo "   📄 Respuesta:"
    curl -s -H "User-Agent: PlayerGold-Wallet/1.0.0" https://$DOMAIN/api/v1/health | python3 -m json.tool | sed 's/^/      /'
else
    echo "   ❌ HTTPS API: No responde"
fi

# Test 3: Verificar redirección HTTP a HTTPS
echo ""
echo "3. Verificando redirección HTTP a HTTPS..."
HTTP_RESPONSE=$(curl -s -I -H "User-Agent: PlayerGold-Wallet/1.0.0" http://$DOMAIN/api/v1/health)
if echo "$HTTP_RESPONSE" | grep -q "301\|302"; then
    echo "   ✅ Redirección HTTP→HTTPS: Funcionando"
    REDIRECT_URL=$(echo "$HTTP_RESPONSE" | grep -i "location:" | awk '{print $2}' | tr -d '\r')
    echo "      Redirige a: $REDIRECT_URL"
else
    echo "   ❌ Redirección HTTP→HTTPS: No configurada"
fi

# Test 4: Verificar protección User-Agent en HTTPS
echo ""
echo "4. Verificando protección User-Agent en HTTPS..."
if curl -s -f https://$DOMAIN/api/v1/health > /dev/null 2>&1; then
    echo "   ❌ Protección User-Agent HTTPS: FALLA (permite acceso sin UA válido)"
else
    echo "   ✅ Protección User-Agent HTTPS: Funcionando"
fi

# Test 5: Verificar headers de seguridad
echo ""
echo "5. Verificando headers de seguridad HTTPS..."
HEADERS=$(curl -s -I -H "User-Agent: PlayerGold-Wallet/1.0.0" https://$DOMAIN/api/v1/health)

if echo "$HEADERS" | grep -qi "strict-transport-security"; then
    echo "   ✅ HSTS: Configurado"
else
    echo "   ❌ HSTS: No configurado"
fi

if echo "$HEADERS" | grep -qi "x-content-type-options"; then
    echo "   ✅ X-Content-Type-Options: Configurado"
else
    echo "   ❌ X-Content-Type-Options: No configurado"
fi

if echo "$HEADERS" | grep -qi "x-frame-options"; then
    echo "   ✅ X-Frame-Options: Configurado"
else
    echo "   ❌ X-Frame-Options: No configurado"
fi

# Test 6: Verificar grado SSL (requiere ssllabs-scan o similar)
echo ""
echo "6. Verificando configuración SSL..."
if command -v nmap &> /dev/null; then
    echo "   🔍 Escaneando puertos SSL con nmap..."
    nmap --script ssl-enum-ciphers -p 443 $DOMAIN | grep -E "(TLS|SSL)" | head -5 | sed 's/^/      /'
else
    echo "   ℹ️  nmap no disponible - instalar con: apt install nmap"
fi

echo ""
echo "🏁 Pruebas SSL completadas"
echo "=============================================================="
echo ""
echo "💡 Para pruebas más detalladas:"
echo "   • SSL Labs: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
echo "   • Verificar certificado: openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
echo "   • Headers de seguridad: curl -I https://$DOMAIN/api/v1/health"
EOF

    chmod +x "$COORDINATOR_HOME/test_ssl.sh"
    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/test_ssl.sh"
    
    success "Script de pruebas SSL creado en $COORDINATOR_HOME/test_ssl.sh"
}

# Función principal
main() {
    show_banner
    
    check_root
    check_coordinator
    check_apache_ssl
    
    log "=== Fase 1: Configuración HTTPS de Apache2 ==="
    configure_apache_https
    
    log "=== Fase 2: Configuración de renovación de certificados ==="
    configure_cert_renewal
    
    log "=== Fase 3: Actualización de protección anti-DDoS ==="
    update_fail2ban_https
    
    log "=== Fase 4: Creación de herramientas de prueba ==="
    create_ssl_test_script
    
    log "=== Fase 5: Aplicación de configuración ==="
    systemctl reload apache2
    
    # Esperar un momento para que Apache2 se recargue
    sleep 3
    
    # Verificar que HTTPS funciona
    if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" https://$DOMAIN/api/v1/health > /dev/null; then
        success "🎉 ¡SSL/HTTPS configurado correctamente!"
        echo ""
        echo -e "${PURPLE}============================================================================${NC}"
        echo -e "${GREEN}  PlayerGold Network Coordinator - SSL/HTTPS Configurado${NC}"
        echo -e "${PURPLE}============================================================================${NC}"
        echo ""
        echo -e "${GREEN}🔒 URLs HTTPS del coordinador:${NC}"
        echo "   • Health check: https://$DOMAIN/api/v1/health"
        echo "   • Registro: https://$DOMAIN/api/v1/register"
        echo "   • Network map: https://$DOMAIN/api/v1/network-map"
        echo "   • Admin: https://$DOMAIN/admin/stats"
        echo ""
        echo -e "${GREEN}🛡️ Protecciones SSL activas:${NC}"
        echo "   • ✅ Certificados SSL válidos"
        echo "   • ✅ Redirección HTTP → HTTPS"
        echo "   • ✅ Headers de seguridad HTTPS"
        echo "   • ✅ Protocolos SSL/TLS modernos"
        echo "   • ✅ Validación User-Agent en HTTPS"
        echo "   • ✅ Fail2ban protegiendo HTTPS"
        echo ""
        echo -e "${GREEN}🧪 Comandos de prueba:${NC}"
        echo "   • Pruebas SSL: sudo -u playergold $COORDINATOR_HOME/test_ssl.sh"
        echo "   • Verificar certificado: openssl s_client -connect $DOMAIN:443 -servername $DOMAIN"
        echo "   • Test completo: sudo -u playergold $COORDINATOR_HOME/test_deployment.sh"
        echo ""
        echo -e "${GREEN}📊 Información de certificados:${NC}"
        echo "   • Certificado: $SSL_CERT_PATH"
        echo "   • Clave privada: $SSL_KEY_PATH"
        if [[ "$SSL_CERT_PATH" == *"letsencrypt"* ]]; then
            echo "   • Renovación automática: ✅ Configurada (Let's Encrypt)"
        else
            echo "   • Renovación automática: ⚠️  Manual (certificados personalizados)"
        fi
        echo ""
        
        # Ejecutar pruebas SSL automáticamente
        info "Ejecutando pruebas SSL de verificación..."
        sudo -u playergold "$COORDINATOR_HOME/test_ssl.sh"
        
    else
        error "❌ Error en la configuración SSL. Verificar:"
        error "• Certificados SSL: $SSL_CERT_PATH"
        error "• Configuración Apache2: /etc/apache2/sites-available/playergold-coordinator-ssl.conf"
        error "• Logs Apache2: tail -f /var/log/apache2/error.log"
        exit 1
    fi
}

# Ejecutar configuración SSL
main "$@"
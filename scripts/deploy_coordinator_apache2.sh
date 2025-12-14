#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Ubuntu Deployment Script (Apache2 Version)
# ============================================================================
# 
# Este script despliega el coordinador de red en Ubuntu usando Apache2 existente:
# - Configuración de Apache2 como proxy reverso
# - Protección anti-DDoS
# - Validación de User-Agent para wallets legítimos
# - Usa SSL existente de Apache2
# - Monitoreo y logs
# - Servicio systemd para auto-inicio
#
# Uso: sudo ./deploy_coordinator_apache2.sh
# ============================================================================

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
COORDINATOR_USER="playergold"
COORDINATOR_HOME="/opt/playergold"
COORDINATOR_PORT="8000"
DOMAIN="playergold.es"
WALLET_USER_AGENT="PlayerGold-Wallet/1.0.0"

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

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Verificar que se ejecuta como root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
}

# Detectar distribución de Ubuntu
detect_ubuntu() {
    if ! grep -q "Ubuntu" /etc/os-release; then
        error "Este script está diseñado para Ubuntu"
        exit 1
    fi
    
    local version=$(lsb_release -rs)
    log "Detectado Ubuntu $version"
}

# Verificar Apache2 existente
check_apache2() {
    log "Verificando Apache2 existente..."
    
    if ! systemctl is-active --quiet apache2; then
        error "Apache2 no está corriendo. Por favor, inicia Apache2 primero."
        exit 1
    fi
    
    if ! apache2ctl -t; then
        error "Configuración de Apache2 inválida. Por favor, corrige los errores primero."
        exit 1
    fi
    
    # Verificar que los puertos 80 y 443 están en uso por Apache2
    if ! netstat -tlnp | grep -q ":80.*apache2" || ! netstat -tlnp | grep -q ":443.*apache2"; then
        warning "Apache2 no parece estar usando los puertos 80 y 443"
        read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log "✅ Apache2 verificado correctamente"
}

# Actualizar sistema
update_system() {
    log "Actualizando sistema Ubuntu..."
    apt update
    apt upgrade -y
    apt install -y curl wget git python3 python3-pip python3-venv ufw fail2ban htop
}

# Crear usuario del sistema
create_user() {
    log "Creando usuario del sistema: $COORDINATOR_USER"
    
    if ! id "$COORDINATOR_USER" &>/dev/null; then
        useradd --system --home-dir "$COORDINATOR_HOME" --create-home --shell /bin/bash "$COORDINATOR_USER"
        log "Usuario $COORDINATOR_USER creado"
    else
        info "Usuario $COORDINATOR_USER ya existe"
    fi
}

# Instalar Python y dependencias
install_python_deps() {
    log "Instalando dependencias de Python..."
    
    # Crear entorno virtual
    sudo -u "$COORDINATOR_USER" python3 -m venv "$COORDINATOR_HOME/venv"
    
    # Instalar dependencias
    sudo -u "$COORDINATOR_USER" "$COORDINATOR_HOME/venv/bin/pip" install --upgrade pip
    sudo -u "$COORDINATOR_USER" "$COORDINATOR_HOME/venv/bin/pip" install \
        fastapi \
        uvicorn[standard] \
        pydantic \
        cryptography \
        aiofiles \
        python-multipart \
        slowapi \
        python-jose[cryptography]
}

# Copiar código del coordinador
deploy_coordinator_code() {
    log "Desplegando código del coordinador..."
    
    # Crear estructura de directorios
    mkdir -p "$COORDINATOR_HOME/src"
    mkdir -p "$COORDINATOR_HOME/logs"
    mkdir -p "$COORDINATOR_HOME/data"
    
    # Copiar código fuente
    cp -r "$(pwd)/src/network_coordinator" "$COORDINATOR_HOME/src/"
    
    # Establecer permisos
    chown -R "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME"
    chmod -R 755 "$COORDINATOR_HOME"
    chmod -R 700 "$COORDINATOR_HOME/data"
}

# Configurar firewall UFW (sin tocar puertos de Apache2)
configure_firewall() {
    log "Configurando firewall UFW..."
    
    # No resetear UFW para no afectar configuración existente
    
    # Permitir puerto del coordinador (solo localmente)
    ufw allow from 127.0.0.1 to any port $COORDINATOR_PORT
    
    # Si UFW no está habilitado, habilitarlo
    if ! ufw status | grep -q "Status: active"; then
        warning "UFW no está activo. ¿Quieres habilitarlo? (Esto podría afectar conexiones SSH existentes)"
        read -p "Habilitar UFW? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ufw --force enable
        fi
    fi
    
    log "Firewall configurado correctamente"
}

# Configurar fail2ban para protección anti-DDoS
configure_fail2ban() {
    log "Configurando fail2ban para protección anti-DDoS..."
    
    # Configuración personalizada para el coordinador
    cat > /etc/fail2ban/jail.d/playergold-coordinator.conf << 'EOF'
[playergold-coordinator]
enabled = true
port = 8000,443,80
filter = playergold-coordinator
logpath = /opt/playergold/logs/access.log
maxretry = 10
findtime = 300
bantime = 3600
action = iptables-multiport[name=playergold, port="8000,443,80", protocol=tcp]

[playergold-ddos]
enabled = true
port = 8000,443,80
filter = playergold-ddos
logpath = /opt/playergold/logs/access.log
maxretry = 50
findtime = 60
bantime = 7200
action = iptables-multiport[name=playergold-ddos, port="8000,443,80", protocol=tcp]

[apache-coordinator]
enabled = true
port = 443,80
filter = apache-coordinator
logpath = /var/log/apache2/access.log
maxretry = 20
findtime = 300
bantime = 1800
action = iptables-multiport[name=apache-coord, port="443,80", protocol=tcp]
EOF

    # Filtro para detectar ataques
    cat > /etc/fail2ban/filter.d/playergold-coordinator.conf << 'EOF'
[Definition]
failregex = ^.*"[A-Z]+ .* HTTP/.*" (4\d\d|5\d\d) .*$
            ^.*Invalid User-Agent.*$
            ^.*Blocked request.*$
ignoreregex =
EOF

    # Filtro para DDoS
    cat > /etc/fail2ban/filter.d/playergold-ddos.conf << 'EOF'
[Definition]
failregex = ^<HOST> -.*"(GET|POST|HEAD).*HTTP.*" (200|404|301|302) .*$
ignoreregex =
EOF

    # Filtro para Apache2
    cat > /etc/fail2ban/filter.d/apache-coordinator.conf << 'EOF'
[Definition]
failregex = ^<HOST> -.*"(GET|POST|HEAD).*HTTP.*" (4\d\d|5\d\d) .*$
ignoreregex = ^<HOST> -.*"(GET|POST|HEAD).*/api/v1/health.*HTTP.*" 200 .*$
EOF

    # Reiniciar fail2ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log "Fail2ban configurado para protección anti-DDoS"
}

# Crear servidor con protección anti-DDoS mejorado
create_protected_server() {
    log "Creando servidor con protección anti-DDoS..."
    
    cat > "$COORDINATOR_HOME/src/protected_server.py" << 'EOF'
"""
Protected Network Coordinator Server with Anti-DDoS for Apache2
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Set
from ipaddress import ip_address, ip_network

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# Importar el servidor original
from network_coordinator.server import app as original_app

# Configuración de protección
VALID_USER_AGENTS = [
    "PlayerGold-Wallet/1.0.0",
    "PlayerGold-Wallet/1.0.1", 
    "PlayerGold-Wallet/1.1.0"
]

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Tracking de conexiones por IP
connection_tracker = defaultdict(lambda: deque(maxlen=100))
blocked_ips: Set[str] = set()
suspicious_ips: Dict[str, int] = defaultdict(int)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/playergold/logs/coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Crear nueva app con protecciones
app = FastAPI(
    title="PlayerGold Network Coordinator (Protected - Apache2)",
    description="Protected network coordinator with anti-DDoS for Apache2",
    version="1.0.0"
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def get_real_ip(request: Request) -> str:
    """Obtener IP real desde Apache2 proxy"""
    # Apache2 pasa la IP real en estos headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Tomar la primera IP (la del cliente original)
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback a la IP de conexión directa
    return request.client.host if request.client else "unknown"

async def validate_request(request: Request):
    """Validar que la petición proviene de un wallet legítimo"""
    client_ip = get_real_ip(request)
    user_agent = request.headers.get("user-agent", "")
    
    # Log de la petición
    logger.info(f"Request from {client_ip}: {request.method} {request.url.path} - UA: {user_agent}")
    
    # Verificar IP bloqueada
    if client_ip in blocked_ips:
        logger.warning(f"Blocked IP attempted access: {client_ip}")
        raise HTTPException(status_code=403, detail="IP blocked")
    
    # Verificar User-Agent válido
    if not any(valid_ua in user_agent for valid_ua in VALID_USER_AGENTS):
        suspicious_ips[client_ip] += 1
        logger.warning(f"Invalid User-Agent from {client_ip}: {user_agent}")
        
        # Bloquear después de muchos intentos sospechosos
        if suspicious_ips[client_ip] > 5:
            blocked_ips.add(client_ip)
            logger.error(f"IP {client_ip} blocked for suspicious activity")
        
        raise HTTPException(status_code=403, detail="Invalid client")
    
    # Tracking de conexiones
    now = time.time()
    connection_tracker[client_ip].append(now)
    
    # Verificar rate limiting manual (además del automático)
    recent_connections = [t for t in connection_tracker[client_ip] if now - t < 60]
    if len(recent_connections) > 30:  # Máximo 30 peticiones por minuto
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return True

# Middleware de protección
@app.middleware("http")
async def protection_middleware(request: Request, call_next):
    """Middleware de protección anti-DDoS"""
    start_time = time.time()
    
    try:
        # Validar petición
        await validate_request(request)
        
        # Procesar petición
        response = await call_next(request)
        
        # Log de respuesta exitosa
        process_time = time.time() - start_time
        client_ip = get_real_ip(request)
        
        # Log en formato Apache2 compatible
        log_entry = f'{client_ip} - - [{datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")}] "{request.method} {request.url.path} HTTP/1.1" {response.status_code} - "{request.headers.get("user-agent", "-")}" {process_time:.3f}'
        
        # Escribir a log de acceso
        with open('/opt/playergold/logs/access.log', 'a') as f:
            f.write(log_entry + '\n')
        
        logger.info(f"Request processed in {process_time:.3f}s - Status: {response.status_code}")
        
        return response
        
    except HTTPException as e:
        # Log de petición rechazada
        client_ip = get_real_ip(request)
        logger.warning(f"Request rejected from {client_ip}: {e.detail}")
        raise e
    except Exception as e:
        # Log de error interno
        client_ip = get_real_ip(request)
        logger.error(f"Internal error processing request from {client_ip}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Endpoints de administración
@app.get("/admin/stats")
@limiter.limit("5/minute")
async def get_protection_stats(request: Request):
    """Estadísticas de protección (solo para administradores)"""
    return {
        "blocked_ips": len(blocked_ips),
        "suspicious_ips": len(suspicious_ips),
        "active_connections": len(connection_tracker),
        "total_requests_last_hour": sum(
            len([t for t in times if time.time() - t < 3600])
            for times in connection_tracker.values()
        )
    }

@app.post("/admin/unblock/{ip}")
@limiter.limit("1/minute")
async def unblock_ip(ip: str, request: Request):
    """Desbloquear IP (solo para administradores)"""
    if ip in blocked_ips:
        blocked_ips.remove(ip)
        if ip in suspicious_ips:
            del suspicious_ips[ip]
        logger.info(f"IP {ip} unblocked by admin")
        return {"message": f"IP {ip} unblocked"}
    return {"message": f"IP {ip} was not blocked"}

# Montar las rutas originales con protección
@app.get("/api/v1/health")
@limiter.limit("10/minute")
async def protected_health(request: Request):
    """Health check protegido"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-protected-apache2",
        "proxy": "apache2"
    }

# Aplicar rate limiting a las rutas del servidor original
for route in original_app.routes:
    if hasattr(route, 'path') and route.path.startswith('/api/'):
        if route.path == '/api/v1/register':
            limiter.limit("5/minute")(route.endpoint)
        elif route.path == '/api/v1/keepalive':
            limiter.limit("60/minute")(route.endpoint)
        elif route.path == '/api/v1/network-map':
            limiter.limit("10/minute")(route.endpoint)
        else:
            limiter.limit("20/minute")(route.endpoint)

# Montar el servidor original
app.mount("/", original_app)

if __name__ == "__main__":
    uvicorn.run(
        "protected_server:app",
        host="127.0.0.1",  # Solo localhost para Apache2 proxy
        port=8000,
        log_level="info",
        access_log=False,  # Manejamos logs manualmente
    )
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/src/protected_server.py"
}

# Configurar Apache2 como proxy reverso
configure_apache2_proxy() {
    log "Configurando Apache2 como proxy reverso..."
    
    # Habilitar módulos necesarios
    a2enmod proxy
    a2enmod proxy_http
    a2enmod headers
    a2enmod rewrite
    a2enmod ssl
    
    # Crear configuración del coordinador (simplificada)
    cat > /etc/apache2/sites-available/playergold-coordinator.conf << 'EOF'
# PlayerGold Network Coordinator - Apache2 Configuration (Simplificada)

# Configuración para el coordinador
<Location "/api/">
    # Validación de User-Agent obligatoria
    RewriteEngine On
    RewriteCond %{HTTP_USER_AGENT} !PlayerGold-Wallet [NC]
    RewriteRule .* - [F,L]
    
    # Proxy al coordinador
    ProxyPass http://127.0.0.1:8000/api/
    ProxyPassReverse http://127.0.0.1:8000/api/
    
    # Headers de seguridad
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    
    # Headers para el proxy
    ProxyPreserveHost On
    ProxyAddHeaders On
    
    # Rate limiting básico con mod_limitipconn (si está disponible)
    <IfModule mod_limitipconn.c>
        MaxConnPerIP 10
    </IfModule>
</Location>

# Dashboard del coordinador (si existe)
<Location "/dashboard">
    # Validación de User-Agent más permisiva para dashboard
    RewriteEngine On
    RewriteCond %{HTTP_USER_AGENT} ^$ [OR]
    RewriteCond %{HTTP_USER_AGENT} "bot|crawler|spider" [NC]
    RewriteRule .* - [F,L]
    
    ProxyPass http://127.0.0.1:8000/dashboard
    ProxyPassReverse http://127.0.0.1:8000/dashboard
    
    ProxyPreserveHost On
    ProxyAddHeaders On
</Location>

# Admin endpoints (acceso restringido)
<Location "/admin/">
    # Solo desde localhost o IPs específicas
    Require ip 127.0.0.1
    Require ip ::1
    # Añadir IPs de administración aquí:
    # Require ip 192.168.1.100
    
    ProxyPass http://127.0.0.1:8000/admin/
    ProxyPassReverse http://127.0.0.1:8000/admin/
    
    ProxyPreserveHost On
    ProxyAddHeaders On
</Location>
EOF

    # Habilitar el sitio
    a2ensite playergold-coordinator
    
    # Verificar configuración
    apache2ctl configtest
    
    # Recargar Apache2
    systemctl reload apache2
    
    log "Apache2 configurado como proxy reverso"
}

# Crear servicio systemd
create_systemd_service() {
    log "Creando servicio systemd..."
    
    cat > /etc/systemd/system/playergold-coordinator.service << EOF
[Unit]
Description=PlayerGold Network Coordinator
After=network.target apache2.service
Wants=network.target
Requires=apache2.service

[Service]
Type=exec
User=$COORDINATOR_USER
Group=$COORDINATOR_USER
WorkingDirectory=$COORDINATOR_HOME
Environment=PATH=$COORDINATOR_HOME/venv/bin
ExecStart=$COORDINATOR_HOME/venv/bin/python $COORDINATOR_HOME/src/protected_server.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=playergold-coordinator

# Límites de seguridad
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$COORDINATOR_HOME

[Install]
WantedBy=multi-user.target
EOF

    # Recargar systemd y habilitar servicio
    systemctl daemon-reload
    systemctl enable playergold-coordinator
    
    log "Servicio systemd creado y habilitado"
}

# Configurar monitoreo y logs
configure_monitoring() {
    log "Configurando monitoreo y logs..."
    
    # Crear script de monitoreo
    cat > "$COORDINATOR_HOME/monitor.sh" << 'EOF'
#!/bin/bash

# Script de monitoreo del coordinador
LOG_FILE="/opt/playergold/logs/monitor.log"
COORDINATOR_URL="http://127.0.0.1:8000/api/v1/health"

check_service() {
    if systemctl is-active --quiet playergold-coordinator; then
        echo "$(date): Servicio activo" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): ERROR - Servicio inactivo" >> "$LOG_FILE"
        return 1
    fi
}

check_api() {
    if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" "$COORDINATOR_URL" > /dev/null; then
        echo "$(date): API respondiendo" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): ERROR - API no responde" >> "$LOG_FILE"
        return 1
    fi
}

check_apache() {
    if systemctl is-active --quiet apache2; then
        echo "$(date): Apache2 activo" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): ERROR - Apache2 inactivo" >> "$LOG_FILE"
        return 1
    fi
}

# Verificar todos los servicios
if ! check_apache; then
    echo "$(date): Reiniciando Apache2..." >> "$LOG_FILE"
    systemctl restart apache2
fi

if ! check_service || ! check_api; then
    echo "$(date): Reiniciando coordinador..." >> "$LOG_FILE"
    systemctl restart playergold-coordinator
    sleep 10
    
    if check_service && check_api; then
        echo "$(date): Coordinador reiniciado correctamente" >> "$LOG_FILE"
    else
        echo "$(date): ERROR CRÍTICO - No se pudo reiniciar el coordinador" >> "$LOG_FILE"
    fi
fi
EOF

    chmod +x "$COORDINATOR_HOME/monitor.sh"
    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/monitor.sh"
    
    # Configurar cron para monitoreo cada 5 minutos
    (crontab -u "$COORDINATOR_USER" -l 2>/dev/null; echo "*/5 * * * * $COORDINATOR_HOME/monitor.sh") | crontab -u "$COORDINATOR_USER" -
    
    # Configurar logrotate
    cat > /etc/logrotate.d/playergold-coordinator << EOF
$COORDINATOR_HOME/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $COORDINATOR_USER $COORDINATOR_USER
    postrotate
        systemctl reload playergold-coordinator
    endscript
}
EOF

    log "Monitoreo y logs configurados"
}

# Función principal de despliegue
main() {
    log "Iniciando despliegue del PlayerGold Network Coordinator (Apache2)"
    
    check_root
    detect_ubuntu
    check_apache2
    
    log "=== Fase 1: Preparación del sistema ==="
    update_system
    create_user
    
    log "=== Fase 2: Instalación de dependencias ==="
    install_python_deps
    
    log "=== Fase 3: Despliegue del código ==="
    deploy_coordinator_code
    create_protected_server
    
    log "=== Fase 4: Configuración de seguridad ==="
    configure_firewall
    configure_fail2ban
    
    log "=== Fase 5: Configuración de Apache2 ==="
    configure_apache2_proxy
    
    log "=== Fase 6: Configuración de servicios ==="
    create_systemd_service
    configure_monitoring
    
    log "=== Fase 7: Inicio de servicios ==="
    systemctl start playergold-coordinator
    
    # Verificar estado
    sleep 5
    if systemctl is-active --quiet playergold-coordinator; then
        log "✅ Coordinador desplegado correctamente con Apache2"
        log "🌐 URL: https://$DOMAIN/api/v1/health"
        log "📊 Estado: systemctl status playergold-coordinator"
        log "📋 Logs: journalctl -u playergold-coordinator -f"
        
        info "=== Información importante ==="
        info "• El coordinador está protegido contra DDoS"
        info "• Solo acepta peticiones de wallets con User-Agent válido"
        info "• Apache2 actúa como proxy reverso con SSL existente"
        info "• Rate limiting configurado por endpoint"
        info "• Logs en $COORDINATOR_HOME/logs/ y /var/log/apache2/"
        info "• Monitoreo automático cada 5 minutos"
        
        warning "=== Configuración adicional recomendada ==="
        warning "• Instalar mod_evasive para Apache2: apt install libapache2-mod-evasive"
        warning "• Configurar backup automático de la base de datos"
        warning "• Configurar alertas de monitoreo (email/Slack)"
        warning "• Revisar logs regularmente"
        
    else
        error "❌ Error en el despliegue. Revisar logs:"
        error "journalctl -u playergold-coordinator -n 50"
        exit 1
    fi
}

# Ejecutar despliegue
main "$@"
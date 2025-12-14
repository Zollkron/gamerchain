#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Ubuntu 24.04 Clean Installation
# ============================================================================
# 
# Script completo para desplegar el coordinador de red en Ubuntu 24.04 limpio
# con Apache2 como proxy reverso y protección anti-DDoS
#
# Requisitos previos:
# - Ubuntu 24.04 Server con Apache2 instalado
# - Usuario con permisos sudo (zollkron)
# - Acceso SSH configurado
#
# Uso: sudo ./deploy_coordinator_ubuntu24_clean.sh
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
COORDINATOR_USER="playergold"
COORDINATOR_HOME="/opt/playergold"
COORDINATOR_PORT="8000"
DOMAIN="playergold.es"
WALLET_USER_AGENT="PlayerGold-Wallet/1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
    echo "  PlayerGold Network Coordinator - Ubuntu 24.04 Clean Deployment"
    echo "============================================================================"
    echo -e "${NC}"
    echo "🚀 Desplegando coordinador de red con protección anti-DDoS"
    echo "🌐 Dominio: $DOMAIN"
    echo "🔒 Arquitectura: Apache2 + uvicorn + fail2ban"
    echo "📁 Directorio: $COORDINATOR_HOME"
    echo ""
}

# Verificar que se ejecuta como root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
}

# Detectar Ubuntu 24.04
detect_ubuntu() {
    if ! grep -q "Ubuntu" /etc/os-release; then
        error "Este script está diseñado para Ubuntu"
        exit 1
    fi
    
    local version=$(lsb_release -rs)
    if [[ "$version" != "24.04" ]]; then
        warning "Detectado Ubuntu $version (recomendado: 24.04)"
        read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log "✅ Detectado Ubuntu $version"
    fi
}

# Verificar Apache2 existente
check_apache2() {
    log "Verificando Apache2 existente..."
    
    if ! command -v apache2 &> /dev/null; then
        error "Apache2 no está instalado. Por favor, instala Apache2 primero:"
        error "sudo apt update && sudo apt install apache2"
        exit 1
    fi
    
    if ! systemctl is-active --quiet apache2; then
        warning "Apache2 no está corriendo. Iniciando Apache2..."
        systemctl start apache2
        systemctl enable apache2
    fi
    
    if ! apache2ctl -t; then
        error "Configuración de Apache2 inválida. Por favor, corrige los errores primero."
        exit 1
    fi
    
    success "Apache2 verificado correctamente"
}

# Verificar código fuente
check_source_code() {
    log "Verificando código fuente del coordinador..."
    
    if [[ ! -d "$PROJECT_ROOT/src/network_coordinator" ]]; then
        error "No se encuentra el código fuente en: $PROJECT_ROOT/src/network_coordinator"
        error "Por favor, ejecuta este script desde el directorio del proyecto PlayerGold"
        exit 1
    fi
    
    success "Código fuente encontrado"
}

# Actualizar sistema
update_system() {
    log "Actualizando sistema Ubuntu 24.04..."
    
    # Actualizar repositorios
    apt update
    
    # Actualizar paquetes existentes
    apt upgrade -y
    
    # Instalar paquetes esenciales
    apt install -y \
        curl \
        wget \
        git \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        ufw \
        fail2ban \
        htop \
        net-tools \
        lsb-release \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsof
    
    success "Sistema actualizado correctamente"
}

# Crear usuario del sistema
create_user() {
    log "Creando usuario del sistema: $COORDINATOR_USER"
    
    if ! id "$COORDINATOR_USER" &>/dev/null; then
        useradd --system --home-dir "$COORDINATOR_HOME" --create-home --shell /bin/bash "$COORDINATOR_USER"
        success "Usuario $COORDINATOR_USER creado"
    else
        info "Usuario $COORDINATOR_USER ya existe"
    fi
    
    # Crear directorios necesarios
    mkdir -p "$COORDINATOR_HOME"/{src,logs,data,backup}
    chown -R "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME"
    chmod -R 755 "$COORDINATOR_HOME"
    chmod -R 700 "$COORDINATOR_HOME/data"
}

# Instalar Python y dependencias
install_python_deps() {
    log "Instalando dependencias de Python..."
    
    # Crear entorno virtual
    sudo -u "$COORDINATOR_USER" python3 -m venv "$COORDINATOR_HOME/venv"
    
    # Actualizar pip
    sudo -u "$COORDINATOR_USER" "$COORDINATOR_HOME/venv/bin/pip" install --upgrade pip
    
    # Instalar dependencias del coordinador
    sudo -u "$COORDINATOR_USER" "$COORDINATOR_HOME/venv/bin/pip" install \
        fastapi==0.104.1 \
        uvicorn[standard]==0.24.0 \
        pydantic==2.5.0 \
        cryptography==41.0.7 \
        aiofiles==23.2.1 \
        python-multipart==0.0.6 \
        slowapi==0.1.9 \
        python-jose[cryptography]==3.3.0 \
        requests==2.31.0
    
    success "Dependencias de Python instaladas"
}

# Copiar código del coordinador
deploy_coordinator_code() {
    log "Desplegando código del coordinador..."
    
    # Copiar código fuente
    cp -r "$PROJECT_ROOT/src/network_coordinator" "$COORDINATOR_HOME/src/"
    
    # Establecer permisos
    chown -R "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/src"
    chmod -R 755 "$COORDINATOR_HOME/src"
    
    success "Código del coordinador desplegado"
}

# Crear servidor protegido con todas las correcciones
create_protected_server() {
    log "Creando servidor protegido con anti-DDoS..."
    
    cat > "$COORDINATOR_HOME/src/protected_server.py" << 'EOF'
"""
Protected Network Coordinator Server with Anti-DDoS for Apache2
Versión corregida para Ubuntu 24.04
"""

import asyncio
import logging
import time
import os
import sys
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from ipaddress import ip_address, ip_network

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# Añadir el directorio src al path para importar el coordinador
sys.path.insert(0, '/opt/playergold/src')

try:
    from network_coordinator.server import app as original_app
except ImportError as e:
    print(f"Error importing network_coordinator: {e}")
    print("Creating minimal fallback app...")
    original_app = FastAPI(title="Fallback App")

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

# Configurar logging
os.makedirs('/opt/playergold/logs', exist_ok=True)
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
    description="Protected network coordinator with anti-DDoS for Apache2 on Ubuntu 24.04",
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
        
        raise HTTPException(status_code=403, detail="Invalid client - PlayerGold wallet required")
    
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
        try:
            with open('/opt/playergold/logs/access.log', 'a') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            logger.error(f"Failed to write access log: {e}")
        
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

# Health check principal
@app.get("/api/v1/health")
@limiter.limit("10/minute")
async def protected_health(request: Request):
    """Health check protegido"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-protected-apache2-ubuntu24",
        "proxy": "apache2",
        "python_version": sys.version,
        "server": "uvicorn"
    }

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
        ),
        "server_info": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "timestamp": datetime.utcnow().isoformat()
        }
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

# Aplicar rate limiting a las rutas del servidor original si existe
try:
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
    logger.info("Original network coordinator app mounted successfully")
except Exception as e:
    logger.warning(f"Could not mount original app: {e}")
    logger.info("Running with minimal protected server only")

if __name__ == "__main__":
    logger.info("Starting PlayerGold Network Coordinator (Protected)")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    uvicorn.run(
        "protected_server:app",
        host="127.0.0.1",  # Solo localhost para Apache2 proxy
        port=8000,
        log_level="info",
        access_log=False,  # Manejamos logs manualmente
        reload=False
    )
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/src/protected_server.py"
    chmod 755 "$COORDINATOR_HOME/src/protected_server.py"
    
    success "Servidor protegido creado"
}

# Configurar firewall UFW
configure_firewall() {
    log "Configurando firewall UFW..."
    
    # Resetear UFW a configuración por defecto
    ufw --force reset
    
    # Configuración básica
    ufw default deny incoming
    ufw default allow outgoing
    
    # Permitir SSH (puerto 22)
    ufw allow ssh
    
    # Permitir HTTP y HTTPS para Apache2
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Permitir puerto del coordinador solo desde localhost
    ufw allow from 127.0.0.1 to any port $COORDINATOR_PORT
    
    # Habilitar UFW
    ufw --force enable
    
    success "Firewall UFW configurado"
}

# Configurar fail2ban para protección anti-DDoS (SEGURO)
configure_fail2ban() {
    log "Configurando fail2ban para protección anti-DDoS (modo seguro)..."
    
    # Backup de configuración original
    cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.conf.backup 2>/dev/null || true
    
    # Obtener IP actual del administrador para whitelist
    ADMIN_IP=$(who am i | awk '{print $5}' | sed 's/[()]//g')
    if [[ -z "$ADMIN_IP" ]]; then
        ADMIN_IP=$(echo $SSH_CLIENT | awk '{print $1}')
    fi
    
    warning "IP del administrador detectada: $ADMIN_IP"
    warning "Esta IP será añadida a la whitelist para evitar auto-bloqueos"
    
    # Configuración SEGURA para el coordinador (solo HTTP/HTTPS, NO SSH)
    cat > /etc/fail2ban/jail.d/playergold-coordinator.conf << EOF
# PlayerGold Coordinator - Configuración SEGURA de fail2ban
# IMPORTANTE: Solo protege HTTP/HTTPS, NO interfiere con SSH

[playergold-coordinator]
enabled = true
port = 8000,443,80
filter = playergold-coordinator
logpath = /opt/playergold/logs/access.log
maxretry = 15
findtime = 600
bantime = 1800
ignoreip = 127.0.0.1/8 ::1 ${ADMIN_IP}
action = iptables-multiport[name=playergold, port="8000,443,80", protocol=tcp]

[playergold-ddos]
enabled = true
port = 443,80
filter = playergold-ddos
logpath = /opt/playergold/logs/access.log
maxretry = 100
findtime = 300
bantime = 3600
ignoreip = 127.0.0.1/8 ::1 ${ADMIN_IP}
action = iptables-multiport[name=playergold-ddos, port="443,80", protocol=tcp]

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

# IMPORTANTE: Deshabilitamos la protección SSH de fail2ban por defecto
# para evitar auto-bloqueos del administrador
[sshd]
enabled = false

[ssh]
enabled = false
EOF

    # Filtro para detectar ataques al coordinador
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
    
    success "Fail2ban configurado para protección anti-DDoS"
}

# Configurar Apache2 como proxy reverso (versión corregida)
configure_apache2_proxy() {
    log "Configurando Apache2 como proxy reverso..."
    
    # Habilitar módulos necesarios
    a2enmod proxy
    a2enmod proxy_http
    a2enmod headers
    a2enmod rewrite
    a2enmod ssl
    
    # Crear configuración del coordinador (simplificada y funcional)
    cat > /etc/apache2/sites-available/playergold-coordinator.conf << 'EOF'
# PlayerGold Network Coordinator - Apache2 Configuration (Ubuntu 24.04)

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
    if ! apache2ctl configtest; then
        error "Error en la configuración de Apache2"
        exit 1
    fi
    
    # Recargar Apache2
    systemctl reload apache2
    
    success "Apache2 configurado como proxy reverso"
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
Environment=PYTHONPATH=$COORDINATOR_HOME/src
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
    
    success "Servicio systemd creado y habilitado"
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

    success "Monitoreo y logs configurados"
}

# Crear script de emergencia para desbloquear IPs
create_emergency_script() {
    log "Creando script de emergencia para desbloquear IPs..."
    
    cat > "$COORDINATOR_HOME/emergency_unblock.sh" << 'EOF'
#!/bin/bash

# Script de emergencia para desbloquear IPs de fail2ban
# Uso: sudo /opt/playergold/emergency_unblock.sh [IP_ADDRESS]

echo "🚨 PlayerGold Network Coordinator - Script de Emergencia"
echo "======================================================"

if [[ $EUID -ne 0 ]]; then
    echo "❌ Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Función para desbloquear una IP específica
unblock_ip() {
    local ip=$1
    echo "🔓 Desbloqueando IP: $ip"
    
    # Desbloquear de fail2ban
    fail2ban-client unban $ip 2>/dev/null || echo "   ℹ️  IP no estaba baneada en fail2ban"
    
    # Desbloquear de iptables directamente
    iptables -D INPUT -s $ip -j DROP 2>/dev/null || echo "   ℹ️  IP no estaba bloqueada en iptables"
    iptables -D INPUT -s $ip -j REJECT 2>/dev/null || echo "   ℹ️  IP no estaba rechazada en iptables"
    
    echo "   ✅ IP $ip desbloqueada"
}

# Función para mostrar IPs bloqueadas
show_blocked_ips() {
    echo "📋 IPs actualmente bloqueadas:"
    echo ""
    
    echo "🔒 fail2ban:"
    fail2ban-client status | grep "Jail list" | sed 's/.*Jail list://' | tr ',' '\n' | while read jail; do
        if [[ -n "$jail" ]]; then
            jail=$(echo $jail | xargs)  # trim whitespace
            echo "   Jail: $jail"
            fail2ban-client status $jail 2>/dev/null | grep "Banned IP list" | sed 's/.*Banned IP list://' | tr ' ' '\n' | while read ip; do
                if [[ -n "$ip" ]]; then
                    echo "      - $ip"
                fi
            done
        fi
    done
    
    echo ""
    echo "🔒 iptables (reglas DROP/REJECT):"
    iptables -L INPUT -n | grep -E "(DROP|REJECT)" | head -10
}

# Función para desbloquear todas las IPs
unblock_all() {
    echo "🔓 Desbloqueando TODAS las IPs..."
    
    # Desbloquear todas las IPs de fail2ban
    fail2ban-client unban --all 2>/dev/null || echo "   ℹ️  No hay IPs baneadas en fail2ban"
    
    # Limpiar reglas de iptables relacionadas con fail2ban
    iptables -F fail2ban-playergold 2>/dev/null || true
    iptables -F fail2ban-playergold-ddos 2>/dev/null || true
    iptables -F fail2ban-apache-coord 2>/dev/null || true
    
    echo "   ✅ Todas las IPs desbloqueadas"
}

# Menú principal
if [[ -n "$1" ]]; then
    # IP específica proporcionada como argumento
    unblock_ip "$1"
else
    # Menú interactivo
    echo "Selecciona una opción:"
    echo "1) Ver IPs bloqueadas"
    echo "2) Desbloquear IP específica"
    echo "3) Desbloquear TODAS las IPs (EMERGENCIA)"
    echo "4) Reiniciar fail2ban"
    echo "5) Salir"
    echo ""
    read -p "Opción (1-5): " choice
    
    case $choice in
        1)
            show_blocked_ips
            ;;
        2)
            read -p "Introduce la IP a desbloquear: " ip
            if [[ -n "$ip" ]]; then
                unblock_ip "$ip"
            else
                echo "❌ IP no válida"
            fi
            ;;
        3)
            read -p "¿Estás seguro de desbloquear TODAS las IPs? (y/N): " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                unblock_all
            else
                echo "Operación cancelada"
            fi
            ;;
        4)
            echo "🔄 Reiniciando fail2ban..."
            systemctl restart fail2ban
            echo "   ✅ fail2ban reiniciado"
            ;;
        5)
            echo "👋 Saliendo..."
            exit 0
            ;;
        *)
            echo "❌ Opción no válida"
            exit 1
            ;;
    esac
fi

echo ""
echo "🏁 Operación completada"
echo "💡 Para uso futuro: sudo /opt/playergold/emergency_unblock.sh [IP]"
EOF

    chmod +x "$COORDINATOR_HOME/emergency_unblock.sh"
    
    success "Script de emergencia creado en $COORDINATOR_HOME/emergency_unblock.sh"
}

# Crear script de pruebas
create_test_script() {
    log "Creando script de pruebas..."
    
    cat > "$COORDINATOR_HOME/test_deployment.sh" << 'EOF'
#!/bin/bash

echo "🧪 Probando despliegue del PlayerGold Network Coordinator"
echo "========================================================"

# Test 1: Verificar servicios
echo "1. Verificando servicios..."
if systemctl is-active --quiet apache2; then
    echo "   ✅ Apache2: Activo"
else
    echo "   ❌ Apache2: Inactivo"
fi

if systemctl is-active --quiet playergold-coordinator; then
    echo "   ✅ Coordinador: Activo"
else
    echo "   ❌ Coordinador: Inactivo"
fi

if systemctl is-active --quiet fail2ban; then
    echo "   ✅ Fail2ban: Activo"
else
    echo "   ❌ Fail2ban: Inactivo"
fi

# Test 2: Verificar puertos
echo ""
echo "2. Verificando puertos..."
if netstat -tlnp | grep -q ":80.*apache2"; then
    echo "   ✅ Puerto 80 (HTTP): Apache2 escuchando"
else
    echo "   ❌ Puerto 80: No disponible"
fi

if netstat -tlnp | grep -q ":443.*apache2"; then
    echo "   ✅ Puerto 443 (HTTPS): Apache2 escuchando"
else
    echo "   ⚠️  Puerto 443: No disponible (normal si no hay SSL configurado)"
fi

if netstat -tlnp | grep -q ":8000.*python"; then
    echo "   ✅ Puerto 8000: Coordinador escuchando"
else
    echo "   ❌ Puerto 8000: No disponible"
fi

# Test 3: Probar API directamente
echo ""
echo "3. Probando API directamente (puerto 8000)..."
if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" http://127.0.0.1:8000/api/v1/health > /dev/null; then
    echo "   ✅ API directa: Respondiendo"
    curl -s -H "User-Agent: PlayerGold-Wallet/1.0.0" http://127.0.0.1:8000/api/v1/health | python3 -m json.tool
else
    echo "   ❌ API directa: No responde"
fi

# Test 4: Probar API a través de Apache2
echo ""
echo "4. Probando API a través de Apache2..."
if curl -s -f -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost/api/v1/health > /dev/null; then
    echo "   ✅ API via Apache2: Respondiendo"
    curl -s -H "User-Agent: PlayerGold-Wallet/1.0.0" http://localhost/api/v1/health | python3 -m json.tool
else
    echo "   ❌ API via Apache2: No responde"
fi

# Test 5: Probar protección User-Agent
echo ""
echo "5. Probando protección User-Agent..."
if curl -s -f http://localhost/api/v1/health > /dev/null 2>&1; then
    echo "   ❌ Protección User-Agent: FALLA (permite acceso sin UA válido)"
else
    echo "   ✅ Protección User-Agent: Funcionando (bloquea acceso sin UA válido)"
fi

# Test 6: Verificar logs
echo ""
echo "6. Verificando logs..."
if [[ -f "/opt/playergold/logs/coordinator.log" ]]; then
    echo "   ✅ Log del coordinador: Existe"
    echo "   📄 Últimas líneas:"
    tail -3 /opt/playergold/logs/coordinator.log | sed 's/^/      /'
else
    echo "   ❌ Log del coordinador: No existe"
fi

echo ""
echo "🏁 Pruebas completadas"
echo "========================================================"
EOF

    chmod +x "$COORDINATOR_HOME/test_deployment.sh"
    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/test_deployment.sh"
    
    success "Script de pruebas creado en $COORDINATOR_HOME/test_deployment.sh"
}

# Función principal de despliegue
main() {
    show_banner
    
    check_root
    detect_ubuntu
    check_apache2
    check_source_code
    
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
    create_emergency_script
    create_test_script
    
    log "=== Fase 7: Inicio de servicios ==="
    systemctl start playergold-coordinator
    
    # Esperar un momento para que el servicio se inicie
    sleep 5
    
    # Verificar estado final
    if systemctl is-active --quiet playergold-coordinator; then
        success "🎉 ¡Coordinador desplegado correctamente!"
        echo ""
        echo -e "${PURPLE}============================================================================${NC}"
        echo -e "${GREEN}  PlayerGold Network Coordinator - Despliegue Completado${NC}"
        echo -e "${PURPLE}============================================================================${NC}"
        echo ""
        echo -e "${GREEN}🌐 URLs de acceso:${NC}"
        echo "   • Health check: https://$DOMAIN/api/v1/health"
        echo "   • Registro: https://$DOMAIN/api/v1/register"
        echo "   • Network map: https://$DOMAIN/api/v1/network-map"
        echo "   • Admin (localhost): https://$DOMAIN/admin/stats"
        echo ""
        echo -e "${GREEN}📊 Comandos útiles:${NC}"
        echo "   • Estado: sudo systemctl status playergold-coordinator"
        echo "   • Logs: sudo journalctl -u playergold-coordinator -f"
        echo "   • Pruebas: sudo -u playergold $COORDINATOR_HOME/test_deployment.sh"
        echo "   • 🚨 Emergencia: sudo $COORDINATOR_HOME/emergency_unblock.sh"
        echo ""
        echo -e "${GREEN}🔒 Protecciones activas:${NC}"
        echo "   • ✅ Validación User-Agent obligatoria"
        echo "   • ✅ Rate limiting por IP (30 req/min)"
        echo "   • ✅ Blacklist automática de IPs sospechosas"
        echo "   • ✅ Fail2ban con protección DDoS"
        echo "   • ✅ Firewall UFW configurado"
        echo "   • ✅ Monitoreo automático cada 5 minutos"
        echo ""
        echo -e "${YELLOW}⚠️  Configuración adicional recomendada:${NC}"
        echo "   • Configurar SSL/HTTPS con Let's Encrypt"
        echo "   • Configurar backup automático de la base de datos"
        echo "   • Configurar alertas de monitoreo (email/Slack)"
        echo "   • Revisar logs regularmente"
        echo ""
        
        # Ejecutar pruebas automáticamente
        info "Ejecutando pruebas de verificación..."
        sudo -u playergold "$COORDINATOR_HOME/test_deployment.sh"
        
    else
        error "❌ Error en el despliegue. Revisar logs:"
        error "sudo journalctl -u playergold-coordinator -n 50"
        exit 1
    fi
}

# Ejecutar despliegue
main "$@"
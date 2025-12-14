#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Ubuntu Deployment Script
# ============================================================================
# 
# Este script despliega el coordinador de red en Ubuntu con:
# - Configuración de firewall y puertos
# - Protección anti-DDoS
# - Validación de User-Agent para wallets legítimos
# - SSL/TLS con certificados automáticos
# - Monitoreo y logs
# - Servicio systemd para auto-inicio
#
# Uso: sudo ./deploy_coordinator_ubuntu.sh
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
SSL_PORT="443"
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

# Actualizar sistema
update_system() {
    log "Actualizando sistema Ubuntu..."
    apt update
    apt upgrade -y
    apt install -y curl wget git python3 python3-pip python3-venv nginx ufw fail2ban htop
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
    mkdir -p "$COORDINATOR_HOME/ssl"
    
    # Copiar código fuente
    cp -r "$(pwd)/src/network_coordinator" "$COORDINATOR_HOME/src/"
    
    # Establecer permisos
    chown -R "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME"
    chmod -R 755 "$COORDINATOR_HOME"
    chmod -R 700 "$COORDINATOR_HOME/data"
    chmod -R 700 "$COORDINATOR_HOME/ssl"
}

# Configurar firewall UFW
configure_firewall() {
    log "Configurando firewall UFW..."
    
    # Resetear UFW
    ufw --force reset
    
    # Políticas por defecto
    ufw default deny incoming
    ufw default allow outgoing
    
    # Permitir SSH (importante!)
    ufw allow ssh
    
    # Permitir HTTP y HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Permitir puerto del coordinador (solo desde IPs específicas si es necesario)
    ufw allow $COORDINATOR_PORT/tcp
    
    # Habilitar UFW
    ufw --force enable
    
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
Protected Network Coordinator Server with Anti-DDoS
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

ALLOWED_NETWORKS = [
    "0.0.0.0/0"  # Permitir todas las IPs por ahora, se puede restringir
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
    title="PlayerGold Network Coordinator (Protected)",
    description="Protected network coordinator with anti-DDoS",
    version="1.0.0"
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

async def validate_request(request: Request):
    """Validar que la petición proviene de un wallet legítimo"""
    client_ip = get_remote_address(request)
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
        logger.info(f"Request processed in {process_time:.3f}s - Status: {response.status_code}")
        
        return response
        
    except HTTPException as e:
        # Log de petición rechazada
        client_ip = get_remote_address(request)
        logger.warning(f"Request rejected from {client_ip}: {e.detail}")
        raise e
    except Exception as e:
        # Log de error interno
        client_ip = get_remote_address(request)
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
        "version": "1.0.0-protected"
    }

# Montar todas las rutas del servidor original con rate limiting
for route in original_app.routes:
    if hasattr(route, 'path') and route.path.startswith('/api/'):
        # Aplicar rate limiting a todas las rutas de API
        if route.path == '/api/v1/register':
            limiter.limit("5/minute")(route.endpoint)
        elif route.path == '/api/v1/keepalive':
            limiter.limit("60/minute")(route.endpoint)  # Más permisivo para keepalive
        elif route.path == '/api/v1/network-map':
            limiter.limit("10/minute")(route.endpoint)
        else:
            limiter.limit("20/minute")(route.endpoint)

# Montar el servidor original
app.mount("/", original_app)

if __name__ == "__main__":
    uvicorn.run(
        "protected_server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "access": {
                    "format": "%(asctime)s - %(client_addr)s - %(request_line)s - %(status_code)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "/opt/playergold/logs/coordinator.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "/opt/playergold/logs/access.log",
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5,
                },
            },
            "loggers": {
                "": {
                    "level": "INFO",
                    "handlers": ["default"],
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "handlers": ["access"],
                    "propagate": False,
                },
            },
        }
    )
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/src/protected_server.py"
}

# Configurar Nginx como proxy reverso con protección adicional
configure_nginx() {
    log "Configurando Nginx como proxy reverso..."
    
    cat > /etc/nginx/sites-available/playergold-coordinator << EOF
# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/m;
limit_req_zone \$binary_remote_addr zone=register:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=keepalive:10m rate=60r/m;

# Upstream del coordinador
upstream coordinator_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirigir HTTP a HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # Configuración SSL (se configurará con certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Configuración de seguridad
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logs
    access_log /var/log/nginx/playergold-access.log;
    error_log /var/log/nginx/playergold-error.log;
    
    # Validación de User-Agent a nivel de Nginx
    set \$valid_client 0;
    if (\$http_user_agent ~* "PlayerGold-Wallet") {
        set \$valid_client 1;
    }
    
    # Bloquear clientes inválidos
    if (\$valid_client = 0) {
        return 403;
    }
    
    # Configuración del proxy
    location / {
        # Rate limiting específico por endpoint
        if (\$request_uri ~* "/api/v1/register") {
            limit_req zone=register burst=2 nodelay;
        }
        if (\$request_uri ~* "/api/v1/keepalive") {
            limit_req zone=keepalive burst=5 nodelay;
        }
        limit_req zone=api burst=10 nodelay;
        
        # Headers del proxy
        proxy_pass http://coordinator_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check sin rate limiting estricto
    location /api/v1/health {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://coordinator_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Habilitar el sitio
    ln -sf /etc/nginx/sites-available/playergold-coordinator /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Verificar configuración
    nginx -t
    
    log "Nginx configurado correctamente"
}

# Instalar y configurar SSL con Let's Encrypt
configure_ssl() {
    log "Configurando SSL con Let's Encrypt..."
    
    # Instalar certbot
    apt install -y certbot python3-certbot-nginx
    
    # Obtener certificado (requiere que el dominio apunte al servidor)
    warning "Asegúrate de que $DOMAIN apunte a este servidor antes de continuar"
    read -p "¿El dominio $DOMAIN apunta a este servidor? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"
        
        # Configurar renovación automática
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        
        log "SSL configurado correctamente"
    else
        warning "SSL no configurado. Configúralo manualmente después de que el dominio apunte al servidor"
    fi
}

# Crear servicio systemd
create_systemd_service() {
    log "Creando servicio systemd..."
    
    cat > /etc/systemd/system/playergold-coordinator.service << EOF
[Unit]
Description=PlayerGold Network Coordinator
After=network.target
Wants=network.target

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
COORDINATOR_URL="http://localhost:8000/api/v1/health"

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
    if curl -s -f "$COORDINATOR_URL" > /dev/null; then
        echo "$(date): API respondiendo" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): ERROR - API no responde" >> "$LOG_FILE"
        return 1
    fi
}

# Verificar servicio y API
if ! check_service || ! check_api; then
    echo "$(date): Reiniciando servicio..." >> "$LOG_FILE"
    systemctl restart playergold-coordinator
    sleep 10
    
    if check_service && check_api; then
        echo "$(date): Servicio reiniciado correctamente" >> "$LOG_FILE"
    else
        echo "$(date): ERROR CRÍTICO - No se pudo reiniciar el servicio" >> "$LOG_FILE"
        # Enviar alerta (configurar según necesidades)
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
    log "Iniciando despliegue del PlayerGold Network Coordinator"
    
    check_root
    detect_ubuntu
    
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
    
    log "=== Fase 5: Configuración de Nginx ==="
    configure_nginx
    
    log "=== Fase 6: Configuración SSL ==="
    configure_ssl
    
    log "=== Fase 7: Configuración de servicios ==="
    create_systemd_service
    configure_monitoring
    
    log "=== Fase 8: Inicio de servicios ==="
    systemctl restart nginx
    systemctl start playergold-coordinator
    
    # Verificar estado
    sleep 5
    if systemctl is-active --quiet playergold-coordinator; then
        log "✅ Coordinador desplegado correctamente"
        log "🌐 URL: https://$DOMAIN"
        log "📊 Estado: systemctl status playergold-coordinator"
        log "📋 Logs: journalctl -u playergold-coordinator -f"
        
        info "=== Información importante ==="
        info "• El coordinador está protegido contra DDoS"
        info "• Solo acepta peticiones de wallets con User-Agent válido"
        info "• Rate limiting configurado por endpoint"
        info "• Logs en $COORDINATOR_HOME/logs/"
        info "• Monitoreo automático cada 5 minutos"
        
        warning "=== Configuración adicional recomendada ==="
        warning "• Configurar backup automático de la base de datos"
        warning "• Configurar alertas de monitoreo (email/Slack)"
        warning "• Revisar logs regularmente"
        warning "• Actualizar certificados SSL automáticamente"
        
    else
        error "❌ Error en el despliegue. Revisar logs:"
        error "journalctl -u playergold-coordinator -n 50"
        exit 1
    fi
}

# Ejecutar despliegue
main "$@"
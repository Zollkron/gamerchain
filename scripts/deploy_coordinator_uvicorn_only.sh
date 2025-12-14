#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Solo uvicorn (Sin Apache2)
# ============================================================================
# 
# Este script despliega el coordinador usando SOLO uvicorn en puerto 8443
# SIN Apache2 como proxy reverso
#
# Uso: sudo ./deploy_coordinator_uvicorn_only.sh
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración
COORDINATOR_USER="playergold"
COORDINATOR_HOME="/opt/playergold"
COORDINATOR_PORT="8443"  # Puerto diferente para no conflictar con Apache2
DOMAIN="playergold.es"

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

# Instalar dependencias
install_dependencies() {
    log "Instalando dependencias..."
    
    apt update
    apt install -y python3 python3-pip python3-venv ufw fail2ban htop openssl
    
    # Crear entorno virtual
    sudo -u "$COORDINATOR_USER" python3 -m venv "$COORDINATOR_HOME/venv"
    
    # Instalar dependencias Python
    sudo -u "$COORDINATOR_USER" "$COORDINATOR_HOME/venv/bin/pip" install --upgrade pip
    sudo -u "$COORDINATOR_USER" "$COORDINATOR_HOME/venv/bin/pip" install \
        fastapi \
        uvicorn[standard] \
        pydantic \
        cryptography \
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

# Generar certificado SSL para uvicorn
generate_ssl_certificate() {
    log "Generando certificado SSL para uvicorn..."
    
    # Verificar si ya existe certificado de Let's Encrypt
    if [[ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
        log "Usando certificado existente de Let's Encrypt"
        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$COORDINATOR_HOME/ssl/cert.pem"
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$COORDINATOR_HOME/ssl/key.pem"
    else
        log "Generando certificado auto-firmado para desarrollo"
        openssl req -x509 -newkey rsa:4096 -keyout "$COORDINATOR_HOME/ssl/key.pem" \
            -out "$COORDINATOR_HOME/ssl/cert.pem" -days 365 -nodes \
            -subj "/C=ES/ST=Madrid/L=Madrid/O=PlayerGold/CN=$DOMAIN"
    fi
    
    chown -R "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/ssl"
    chmod 600 "$COORDINATOR_HOME/ssl/key.pem"
    chmod 644 "$COORDINATOR_HOME/ssl/cert.pem"
}

# Crear servidor uvicorn con SSL
create_uvicorn_server() {
    log "Creando servidor uvicorn con SSL..."
    
    cat > "$COORDINATOR_HOME/src/uvicorn_server.py" << 'EOF'
"""
PlayerGold Network Coordinator - Servidor uvicorn directo con SSL
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, Set

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# Importar el servidor original
from network_coordinator.server import app as original_app

# Configuración
VALID_USER_AGENTS = [
    "PlayerGold-Wallet/1.0.0",
    "PlayerGold-Wallet/1.0.1", 
    "PlayerGold-Wallet/1.1.0"
]

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Tracking de conexiones
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

# Crear app con protecciones
app = FastAPI(
    title="PlayerGold Network Coordinator (uvicorn SSL)",
    description="Direct uvicorn server with SSL and anti-DDoS protection",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

async def validate_request(request: Request):
    """Validar petición"""
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
        
        if suspicious_ips[client_ip] > 5:
            blocked_ips.add(client_ip)
            logger.error(f"IP {client_ip} blocked for suspicious activity")
        
        raise HTTPException(status_code=403, detail="Invalid client - PlayerGold wallet required")
    
    # Rate limiting manual
    now = time.time()
    connection_tracker[client_ip].append(now)
    
    recent_connections = [t for t in connection_tracker[client_ip] if now - t < 60]
    if len(recent_connections) > 30:
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return True

@app.middleware("http")
async def protection_middleware(request: Request, call_next):
    """Middleware de protección"""
    start_time = time.time()
    
    try:
        await validate_request(request)
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Request processed in {process_time:.3f}s - Status: {response.status_code}")
        
        return response
        
    except HTTPException as e:
        client_ip = get_remote_address(request)
        logger.warning(f"Request rejected from {client_ip}: {e.detail}")
        raise e
    except Exception as e:
        client_ip = get_remote_address(request)
        logger.error(f"Internal error processing request from {client_ip}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check personalizado
@app.get("/api/v1/health")
@limiter.limit("10/minute")
async def protected_health(request: Request):
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-uvicorn-ssl",
        "server": "uvicorn-direct"
    }

# Aplicar rate limiting a rutas originales
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

# Montar servidor original
app.mount("/", original_app)

if __name__ == "__main__":
    uvicorn.run(
        "uvicorn_server:app",
        host="0.0.0.0",
        port=8443,
        ssl_keyfile="/opt/playergold/ssl/key.pem",
        ssl_certfile="/opt/playergold/ssl/cert.pem",
        log_level="info",
        access_log=True
    )
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/src/uvicorn_server.py"
}

# Configurar firewall
configure_firewall() {
    log "Configurando firewall..."
    
    # Permitir puerto del coordinador
    ufw allow $COORDINATOR_PORT/tcp
    
    # Habilitar UFW si no está activo
    if ! ufw status | grep -q "Status: active"; then
        ufw --force enable
    fi
    
    log "Firewall configurado - Puerto $COORDINATOR_PORT abierto"
}

# Crear servicio systemd
create_systemd_service() {
    log "Creando servicio systemd..."
    
    cat > /etc/systemd/system/playergold-coordinator.service << EOF
[Unit]
Description=PlayerGold Network Coordinator (uvicorn SSL)
After=network.target
Wants=network.target

[Service]
Type=exec
User=$COORDINATOR_USER
Group=$COORDINATOR_USER
WorkingDirectory=$COORDINATOR_HOME
Environment=PATH=$COORDINATOR_HOME/venv/bin
ExecStart=$COORDINATOR_HOME/venv/bin/python $COORDINATOR_HOME/src/uvicorn_server.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=playergold-coordinator

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable playergold-coordinator
    
    log "Servicio systemd creado"
}

# Función principal
main() {
    log "Desplegando PlayerGold Coordinator con uvicorn directo"
    
    check_root
    create_user
    install_dependencies
    deploy_coordinator_code
    generate_ssl_certificate
    create_uvicorn_server
    configure_firewall
    create_systemd_service
    
    # Iniciar servicio
    systemctl start playergold-coordinator
    
    sleep 5
    if systemctl is-active --quiet playergold-coordinator; then
        log "✅ Coordinador desplegado correctamente"
        log "🌐 URL: https://$DOMAIN:$COORDINATOR_PORT/api/v1/health"
        log "📊 Puerto: $COORDINATOR_PORT"
        log "🔒 SSL: Habilitado"
        
        info "=== Información importante ==="
        info "• El coordinador corre directamente en uvicorn"
        info "• Puerto: $COORDINATOR_PORT (diferente de Apache2)"
        info "• SSL manejado por uvicorn"
        info "• No hay proxy reverso"
        
        warning "=== Configuración de wallets ==="
        warning "• Las wallets deben conectar a: https://$DOMAIN:$COORDINATOR_PORT"
        warning "• Actualizar NetworkValidator.js para usar puerto $COORDINATOR_PORT"
        
    else
        error "❌ Error en el despliegue"
        exit 1
    fi
}

main "$@"
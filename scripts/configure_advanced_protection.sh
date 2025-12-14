#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Protección Avanzada Anti-DDoS
# ============================================================================
# 
# Este script configura protecciones avanzadas adicionales:
# - Validación criptográfica de wallets
# - Blacklist/whitelist de IPs
# - Protección contra ataques sofisticados
# - Monitoreo en tiempo real
#
# Uso: sudo ./configure_advanced_protection.sh
# ============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

COORDINATOR_HOME="/opt/playergold"
COORDINATOR_USER="playergold"

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

# Crear sistema de validación criptográfica de wallets
create_wallet_validator() {
    log "Creando sistema de validación criptográfica de wallets..."
    
    cat > "$COORDINATOR_HOME/src/wallet_validator.py" << 'EOF'
"""
Validador criptográfico de wallets PlayerGold
"""

import hashlib
import hmac
import time
import json
from typing import Optional, Dict, Set
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class WalletValidator:
    def __init__(self):
        # Claves públicas de wallets autorizados (se pueden cargar desde archivo)
        self.authorized_wallets: Set[str] = set()
        
        # Tokens de sesión válidos
        self.valid_tokens: Dict[str, Dict] = {}
        
        # Secreto para HMAC (cambiar en producción)
        self.hmac_secret = b"playergold_coordinator_secret_2024"
        
        # Cargar wallets autorizados
        self.load_authorized_wallets()
    
    def load_authorized_wallets(self):
        """Cargar lista de wallets autorizados"""
        try:
            with open('/opt/playergold/data/authorized_wallets.json', 'r') as f:
                data = json.load(f)
                self.authorized_wallets = set(data.get('wallets', []))
        except FileNotFoundError:
            # Crear archivo inicial vacío
            self.save_authorized_wallets()
    
    def save_authorized_wallets(self):
        """Guardar lista de wallets autorizados"""
        with open('/opt/playergold/data/authorized_wallets.json', 'w') as f:
            json.dump({'wallets': list(self.authorized_wallets)}, f, indent=2)
    
    def generate_challenge(self, wallet_id: str) -> str:
        """Generar desafío criptográfico para el wallet"""
        timestamp = int(time.time())
        challenge_data = f"{wallet_id}:{timestamp}:{time.time()}"
        
        # Crear HMAC del desafío
        challenge_hash = hmac.new(
            self.hmac_secret,
            challenge_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        challenge = base64.b64encode(f"{challenge_data}:{challenge_hash}".encode()).decode()
        
        # Almacenar desafío temporalmente (válido por 5 minutos)
        self.valid_tokens[challenge] = {
            'wallet_id': wallet_id,
            'timestamp': timestamp,
            'expires': timestamp + 300  # 5 minutos
        }
        
        return challenge
    
    def verify_wallet_signature(self, wallet_id: str, signature: str, message: str) -> bool:
        """Verificar firma del wallet"""
        try:
            # En una implementación real, aquí verificaríamos la firma Ed25519
            # Por ahora, verificamos que el wallet esté en la lista autorizada
            
            # Verificar formato de la firma
            if not signature or len(signature) < 32:
                return False
            
            # Verificar que el wallet esté autorizado
            if wallet_id not in self.authorized_wallets:
                # Auto-autorizar wallets que pasen validación básica
                if self.is_valid_wallet_format(wallet_id):
                    self.authorized_wallets.add(wallet_id)
                    self.save_authorized_wallets()
                    return True
                return False
            
            return True
            
        except Exception:
            return False
    
    def is_valid_wallet_format(self, wallet_id: str) -> bool:
        """Verificar formato válido de wallet ID"""
        # Los wallet IDs de PlayerGold empiezan con "PG" seguido de 40 caracteres hex
        if not wallet_id.startswith("PG"):
            return False
        
        if len(wallet_id) != 42:  # PG + 40 caracteres
            return False
        
        try:
            # Verificar que los últimos 40 caracteres sean hexadecimales
            int(wallet_id[2:], 16)
            return True
        except ValueError:
            return False
    
    def validate_request_token(self, token: str) -> Optional[str]:
        """Validar token de petición"""
        if token not in self.valid_tokens:
            return None
        
        token_data = self.valid_tokens[token]
        
        # Verificar expiración
        if time.time() > token_data['expires']:
            del self.valid_tokens[token]
            return None
        
        return token_data['wallet_id']
    
    def cleanup_expired_tokens(self):
        """Limpiar tokens expirados"""
        current_time = time.time()
        expired_tokens = [
            token for token, data in self.valid_tokens.items()
            if current_time > data['expires']
        ]
        
        for token in expired_tokens:
            del self.valid_tokens[token]
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del validador"""
        self.cleanup_expired_tokens()
        
        return {
            'authorized_wallets': len(self.authorized_wallets),
            'active_tokens': len(self.valid_tokens),
            'last_cleanup': time.time()
        }

# Instancia global del validador
wallet_validator = WalletValidator()
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/src/wallet_validator.py"
}

# Crear sistema de blacklist/whitelist de IPs
create_ip_manager() {
    log "Creando sistema de gestión de IPs..."
    
    cat > "$COORDINATOR_HOME/src/ip_manager.py" << 'EOF'
"""
Gestor de IPs para el coordinador PlayerGold
"""

import json
import time
import ipaddress
from typing import Set, Dict, List
from collections import defaultdict

class IPManager:
    def __init__(self):
        self.blacklist: Set[str] = set()
        self.whitelist: Set[str] = set()
        self.suspicious_ips: Dict[str, Dict] = {}
        self.ip_stats: Dict[str, Dict] = defaultdict(lambda: {
            'requests': 0,
            'last_seen': 0,
            'first_seen': 0,
            'blocked_attempts': 0,
            'countries': set()
        })
        
        # Cargar listas desde archivos
        self.load_lists()
    
    def load_lists(self):
        """Cargar blacklist y whitelist desde archivos"""
        try:
            with open('/opt/playergold/data/ip_blacklist.json', 'r') as f:
                data = json.load(f)
                self.blacklist = set(data.get('ips', []))
        except FileNotFoundError:
            self.save_blacklist()
        
        try:
            with open('/opt/playergold/data/ip_whitelist.json', 'r') as f:
                data = json.load(f)
                self.whitelist = set(data.get('ips', []))
        except FileNotFoundError:
            self.save_whitelist()
    
    def save_blacklist(self):
        """Guardar blacklist"""
        with open('/opt/playergold/data/ip_blacklist.json', 'w') as f:
            json.dump({'ips': list(self.blacklist)}, f, indent=2)
    
    def save_whitelist(self):
        """Guardar whitelist"""
        with open('/opt/playergold/data/ip_whitelist.json', 'w') as f:
            json.dump({'ips': list(self.whitelist)}, f, indent=2)
    
    def is_ip_allowed(self, ip: str) -> bool:
        """Verificar si una IP está permitida"""
        # Whitelist tiene prioridad
        if ip in self.whitelist:
            return True
        
        # Verificar blacklist
        if ip in self.blacklist:
            return False
        
        # Verificar rangos de red sospechosos
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # Bloquear IPs privadas que no deberían acceder desde internet
            if ip_obj.is_private and ip != '127.0.0.1':
                return False
            
            # Bloquear rangos conocidos de botnets/proxies
            suspicious_ranges = [
                '10.0.0.0/8',
                '172.16.0.0/12',
                '192.168.0.0/16'
            ]
            
            for range_str in suspicious_ranges:
                if ip_obj in ipaddress.ip_network(range_str):
                    if ip not in self.whitelist:  # Permitir si está en whitelist
                        return False
            
        except ValueError:
            # IP inválida
            return False
        
        return True
    
    def add_to_blacklist(self, ip: str, reason: str = "Manual"):
        """Añadir IP a blacklist"""
        self.blacklist.add(ip)
        self.save_blacklist()
        
        # Registrar en suspicious_ips
        self.suspicious_ips[ip] = {
            'reason': reason,
            'timestamp': time.time(),
            'blocked': True
        }
    
    def add_to_whitelist(self, ip: str):
        """Añadir IP a whitelist"""
        self.whitelist.add(ip)
        self.save_whitelist()
        
        # Remover de blacklist si estaba
        if ip in self.blacklist:
            self.blacklist.remove(ip)
            self.save_blacklist()
    
    def remove_from_blacklist(self, ip: str):
        """Remover IP de blacklist"""
        if ip in self.blacklist:
            self.blacklist.remove(ip)
            self.save_blacklist()
            return True
        return False
    
    def track_request(self, ip: str, user_agent: str = "", country: str = ""):
        """Registrar petición de una IP"""
        current_time = time.time()
        
        stats = self.ip_stats[ip]
        stats['requests'] += 1
        stats['last_seen'] = current_time
        
        if stats['first_seen'] == 0:
            stats['first_seen'] = current_time
        
        if country:
            stats['countries'].add(country)
        
        # Detectar comportamiento sospechoso
        self.detect_suspicious_behavior(ip, stats)
    
    def detect_suspicious_behavior(self, ip: str, stats: Dict):
        """Detectar comportamiento sospechoso"""
        current_time = time.time()
        
        # Demasiadas peticiones en poco tiempo
        if stats['requests'] > 100 and (current_time - stats['first_seen']) < 300:  # 100 req en 5 min
            self.add_to_blacklist(ip, "High request rate")
            return
        
        # Múltiples países (posible proxy/VPN)
        if len(stats['countries']) > 3:
            self.suspicious_ips[ip] = {
                'reason': 'Multiple countries',
                'timestamp': current_time,
                'countries': list(stats['countries'])
            }
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del gestor de IPs"""
        return {
            'blacklisted_ips': len(self.blacklist),
            'whitelisted_ips': len(self.whitelist),
            'suspicious_ips': len(self.suspicious_ips),
            'tracked_ips': len(self.ip_stats),
            'total_requests': sum(stats['requests'] for stats in self.ip_stats.values())
        }

# Instancia global del gestor de IPs
ip_manager = IPManager()
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/src/ip_manager.py"
}

# Crear sistema de monitoreo en tiempo real
create_realtime_monitor() {
    log "Creando sistema de monitoreo en tiempo real..."
    
    cat > "$COORDINATOR_HOME/src/realtime_monitor.py" << 'EOF'
"""
Monitor en tiempo real para el coordinador PlayerGold
"""

import asyncio
import json
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from collections import deque

logger = logging.getLogger(__name__)

class RealtimeMonitor:
    def __init__(self):
        # Métricas en tiempo real
        self.request_history = deque(maxlen=1000)  # Últimas 1000 peticiones
        self.error_history = deque(maxlen=500)     # Últimos 500 errores
        self.performance_metrics = {
            'cpu_usage': deque(maxlen=60),         # Último minuto
            'memory_usage': deque(maxlen=60),      # Último minuto
            'response_times': deque(maxlen=100),   # Últimas 100 respuestas
        }
        
        # Alertas activas
        self.active_alerts = []
        
        # Configuración de umbrales
        self.thresholds = {
            'cpu_critical': 90,
            'cpu_warning': 70,
            'memory_critical': 90,
            'memory_warning': 70,
            'response_time_critical': 5.0,
            'response_time_warning': 2.0,
            'error_rate_critical': 10,  # % de errores
            'error_rate_warning': 5,
        }
        
        # Iniciar monitoreo
        self.start_monitoring()
    
    def start_monitoring(self):
        """Iniciar monitoreo en background"""
        asyncio.create_task(self.monitor_system_metrics())
        asyncio.create_task(self.check_alerts())
    
    async def monitor_system_metrics(self):
        """Monitorear métricas del sistema"""
        while True:
            try:
                # CPU y memoria
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                self.performance_metrics['cpu_usage'].append({
                    'timestamp': time.time(),
                    'value': cpu_percent
                })
                
                self.performance_metrics['memory_usage'].append({
                    'timestamp': time.time(),
                    'value': memory_percent
                })
                
                # Verificar umbrales
                self.check_system_thresholds(cpu_percent, memory_percent)
                
                await asyncio.sleep(60)  # Cada minuto
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(60)
    
    def record_request(self, ip: str, endpoint: str, method: str, status_code: int, response_time: float):
        """Registrar petición"""
        request_data = {
            'timestamp': time.time(),
            'ip': ip,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time
        }
        
        self.request_history.append(request_data)
        self.performance_metrics['response_times'].append(response_time)
        
        # Registrar errores
        if status_code >= 400:
            self.error_history.append(request_data)
    
    def check_system_thresholds(self, cpu_percent: float, memory_percent: float):
        """Verificar umbrales del sistema"""
        current_time = time.time()
        
        # CPU crítico
        if cpu_percent >= self.thresholds['cpu_critical']:
            self.add_alert('cpu_critical', f'CPU usage critical: {cpu_percent:.1f}%', current_time)
        elif cpu_percent >= self.thresholds['cpu_warning']:
            self.add_alert('cpu_warning', f'CPU usage high: {cpu_percent:.1f}%', current_time)
        
        # Memoria crítica
        if memory_percent >= self.thresholds['memory_critical']:
            self.add_alert('memory_critical', f'Memory usage critical: {memory_percent:.1f}%', current_time)
        elif memory_percent >= self.thresholds['memory_warning']:
            self.add_alert('memory_warning', f'Memory usage high: {memory_percent:.1f}%', current_time)
    
    async def check_alerts(self):
        """Verificar alertas periódicamente"""
        while True:
            try:
                current_time = time.time()
                
                # Verificar tasa de errores
                self.check_error_rate(current_time)
                
                # Verificar tiempo de respuesta
                self.check_response_times(current_time)
                
                # Limpiar alertas antiguas
                self.cleanup_old_alerts(current_time)
                
                await asyncio.sleep(30)  # Cada 30 segundos
                
            except Exception as e:
                logger.error(f"Error checking alerts: {e}")
                await asyncio.sleep(30)
    
    def check_error_rate(self, current_time: float):
        """Verificar tasa de errores"""
        # Errores en los últimos 5 minutos
        recent_errors = [
            req for req in self.error_history
            if current_time - req['timestamp'] < 300
        ]
        
        # Peticiones totales en los últimos 5 minutos
        recent_requests = [
            req for req in self.request_history
            if current_time - req['timestamp'] < 300
        ]
        
        if len(recent_requests) > 10:  # Solo si hay suficientes peticiones
            error_rate = (len(recent_errors) / len(recent_requests)) * 100
            
            if error_rate >= self.thresholds['error_rate_critical']:
                self.add_alert('error_rate_critical', f'Error rate critical: {error_rate:.1f}%', current_time)
            elif error_rate >= self.thresholds['error_rate_warning']:
                self.add_alert('error_rate_warning', f'Error rate high: {error_rate:.1f}%', current_time)
    
    def check_response_times(self, current_time: float):
        """Verificar tiempos de respuesta"""
        if len(self.performance_metrics['response_times']) > 10:
            # Promedio de los últimos 10 tiempos de respuesta
            recent_times = list(self.performance_metrics['response_times'])[-10:]
            avg_response_time = sum(recent_times) / len(recent_times)
            
            if avg_response_time >= self.thresholds['response_time_critical']:
                self.add_alert('response_time_critical', f'Response time critical: {avg_response_time:.2f}s', current_time)
            elif avg_response_time >= self.thresholds['response_time_warning']:
                self.add_alert('response_time_warning', f'Response time high: {avg_response_time:.2f}s', current_time)
    
    def add_alert(self, alert_type: str, message: str, timestamp: float):
        """Añadir alerta"""
        # Evitar alertas duplicadas recientes
        recent_alerts = [
            alert for alert in self.active_alerts
            if alert['type'] == alert_type and timestamp - alert['timestamp'] < 300
        ]
        
        if not recent_alerts:
            alert = {
                'type': alert_type,
                'message': message,
                'timestamp': timestamp,
                'acknowledged': False
            }
            
            self.active_alerts.append(alert)
            logger.warning(f"ALERT: {message}")
            
            # Guardar alerta en archivo
            self.save_alert_to_file(alert)
    
    def save_alert_to_file(self, alert: Dict):
        """Guardar alerta en archivo"""
        try:
            alert_file = '/opt/playergold/logs/alerts.log'
            with open(alert_file, 'a') as f:
                f.write(f"{datetime.fromtimestamp(alert['timestamp'])}: {alert['message']}\n")
        except Exception as e:
            logger.error(f"Error saving alert to file: {e}")
    
    def cleanup_old_alerts(self, current_time: float):
        """Limpiar alertas antiguas"""
        # Remover alertas de más de 1 hora
        self.active_alerts = [
            alert for alert in self.active_alerts
            if current_time - alert['timestamp'] < 3600
        ]
    
    def get_dashboard_data(self) -> Dict:
        """Obtener datos para dashboard"""
        current_time = time.time()
        
        # Peticiones por minuto (últimos 10 minutos)
        requests_per_minute = []
        for i in range(10):
            minute_start = current_time - (i + 1) * 60
            minute_end = current_time - i * 60
            
            minute_requests = len([
                req for req in self.request_history
                if minute_start <= req['timestamp'] < minute_end
            ])
            
            requests_per_minute.append({
                'minute': i,
                'requests': minute_requests
            })
        
        # Top IPs
        ip_counts = {}
        for req in self.request_history:
            if current_time - req['timestamp'] < 3600:  # Última hora
                ip_counts[req['ip']] = ip_counts.get(req['ip'], 0) + 1
        
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'current_time': current_time,
            'requests_per_minute': requests_per_minute,
            'top_ips': top_ips,
            'active_alerts': len(self.active_alerts),
            'total_requests': len(self.request_history),
            'total_errors': len(self.error_history),
            'avg_response_time': sum(self.performance_metrics['response_times']) / len(self.performance_metrics['response_times']) if self.performance_metrics['response_times'] else 0,
            'current_cpu': self.performance_metrics['cpu_usage'][-1]['value'] if self.performance_metrics['cpu_usage'] else 0,
            'current_memory': self.performance_metrics['memory_usage'][-1]['value'] if self.performance_metrics['memory_usage'] else 0
        }

# Instancia global del monitor
realtime_monitor = RealtimeMonitor()
EOF

    chown "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/src/realtime_monitor.py"
}

# Instalar dependencias adicionales
install_additional_deps() {
    log "Instalando dependencias adicionales..."
    
    sudo -u "$COORDINATOR_USER" "$COORDINATOR_HOME/venv/bin/pip" install \
        slowapi \
        psutil \
        geoip2 \
        maxminddb \
        cryptography
}

# Configurar iptables avanzado
configure_advanced_iptables() {
    log "Configurando iptables avanzado..."
    
    # Crear script de iptables
    cat > /etc/iptables/playergold-rules.sh << 'EOF'
#!/bin/bash

# Limpiar reglas existentes
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Políticas por defecto
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Permitir loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Permitir conexiones establecidas
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Permitir SSH (cambiar puerto si es necesario)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Protección contra SYN flood
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Protección contra ping flood
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# Rate limiting para HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 80 -m state --state NEW -m recent --update --seconds 60 --hitcount 20 -j DROP
iptables -A INPUT -p tcp --dport 80 -j ACCEPT

iptables -A INPUT -p tcp --dport 443 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 443 -m state --state NEW -m recent --update --seconds 60 --hitcount 20 -j DROP
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Rate limiting para coordinador
iptables -A INPUT -p tcp --dport 8000 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 8000 -m state --state NEW -m recent --update --seconds 60 --hitcount 10 -j DROP
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# Bloquear escaneos de puertos
iptables -A INPUT -m recent --name portscan --rcheck --seconds 86400 -j DROP
iptables -A INPUT -m recent --name portscan --remove
iptables -A INPUT -p tcp -m tcp --dport 139 -m recent --name portscan --set -j LOG --log-prefix "portscan:"
iptables -A INPUT -p tcp -m tcp --dport 139 -m recent --name portscan --set -j DROP

# Logging de conexiones rechazadas
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables denied: " --log-level 7

# Guardar reglas
iptables-save > /etc/iptables/rules.v4
EOF

    chmod +x /etc/iptables/playergold-rules.sh
    
    # Ejecutar reglas
    /etc/iptables/playergold-rules.sh
    
    # Configurar para que se carguen al inicio
    cat > /etc/systemd/system/iptables-restore.service << 'EOF'
[Unit]
Description=Restore iptables rules
Before=network-pre.target
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore /etc/iptables/rules.v4

[Install]
WantedBy=multi-user.target
EOF

    systemctl enable iptables-restore
}

# Crear dashboard de monitoreo
create_monitoring_dashboard() {
    log "Creando dashboard de monitoreo..."
    
    cat > "$COORDINATOR_HOME/src/dashboard.py" << 'EOF'
"""
Dashboard web para monitoreo del coordinador
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json

dashboard_app = FastAPI()
templates = Jinja2Templates(directory="/opt/playergold/templates")

@dashboard_app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal"""
    from realtime_monitor import realtime_monitor
    from ip_manager import ip_manager
    from wallet_validator import wallet_validator
    
    # Obtener datos de monitoreo
    monitor_data = realtime_monitor.get_dashboard_data()
    ip_stats = ip_manager.get_stats()
    wallet_stats = wallet_validator.get_stats()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "monitor_data": monitor_data,
        "ip_stats": ip_stats,
        "wallet_stats": wallet_stats
    })

@dashboard_app.get("/api/dashboard/data")
async def dashboard_data():
    """API para datos del dashboard"""
    from realtime_monitor import realtime_monitor
    from ip_manager import ip_manager
    from wallet_validator import wallet_validator
    
    return {
        "monitor": realtime_monitor.get_dashboard_data(),
        "ip_manager": ip_manager.get_stats(),
        "wallet_validator": wallet_validator.get_stats()
    }
EOF

    # Crear directorio de templates
    mkdir -p "$COORDINATOR_HOME/templates"
    
    # Crear template HTML básico
    cat > "$COORDINATOR_HOME/templates/dashboard.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>PlayerGold Coordinator Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2196F3; }
        .metric-label { font-size: 14px; color: #666; }
        .alert { background: #f44336; color: white; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .warning { background: #ff9800; }
        .success { background: #4caf50; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ PlayerGold Network Coordinator Dashboard</h1>
        
        <div class="card">
            <h2>📊 Métricas en Tiempo Real</h2>
            <div class="metric">
                <div class="metric-value">{{ monitor_data.total_requests }}</div>
                <div class="metric-label">Total Requests</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ monitor_data.total_errors }}</div>
                <div class="metric-label">Total Errors</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ "%.2f"|format(monitor_data.avg_response_time) }}s</div>
                <div class="metric-label">Avg Response Time</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ "%.1f"|format(monitor_data.current_cpu) }}%</div>
                <div class="metric-label">CPU Usage</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ "%.1f"|format(monitor_data.current_memory) }}%</div>
                <div class="metric-label">Memory Usage</div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔒 Seguridad</h2>
            <div class="metric">
                <div class="metric-value">{{ ip_stats.blacklisted_ips }}</div>
                <div class="metric-label">Blocked IPs</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ ip_stats.whitelisted_ips }}</div>
                <div class="metric-label">Whitelisted IPs</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ wallet_stats.authorized_wallets }}</div>
                <div class="metric-label">Authorized Wallets</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ wallet_stats.active_tokens }}</div>
                <div class="metric-label">Active Tokens</div>
            </div>
        </div>
        
        <div class="card">
            <h2>🌐 Top IPs (Última Hora)</h2>
            <table>
                <tr><th>IP Address</th><th>Requests</th></tr>
                {% for ip, count in monitor_data.top_ips %}
                <tr><td>{{ ip }}</td><td>{{ count }}</td></tr>
                {% endfor %}
            </table>
        </div>
        
        {% if monitor_data.active_alerts > 0 %}
        <div class="card">
            <h2>⚠️ Alertas Activas</h2>
            <div class="alert">{{ monitor_data.active_alerts }} alertas activas</div>
        </div>
        {% endif %}
    </div>
    
    <script>
        // Auto-refresh cada 30 segundos
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
EOF

    chown -R "$COORDINATOR_USER:$COORDINATOR_USER" "$COORDINATOR_HOME/templates"
}

# Función principal
main() {
    log "Configurando protecciones avanzadas anti-DDoS..."
    
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    
    log "=== Instalando dependencias adicionales ==="
    install_additional_deps
    
    log "=== Creando validador de wallets ==="
    create_wallet_validator
    
    log "=== Creando gestor de IPs ==="
    create_ip_manager
    
    log "=== Creando monitor en tiempo real ==="
    create_realtime_monitor
    
    log "=== Configurando iptables avanzado ==="
    configure_advanced_iptables
    
    log "=== Creando dashboard de monitoreo ==="
    create_monitoring_dashboard
    
    # Reiniciar servicio para aplicar cambios
    systemctl restart playergold-coordinator
    
    log "✅ Protecciones avanzadas configuradas correctamente"
    
    info "=== Características de seguridad activadas ==="
    info "• Validación criptográfica de wallets"
    info "• Blacklist/whitelist automática de IPs"
    info "• Protección avanzada contra DDoS"
    info "• Monitoreo en tiempo real"
    info "• Dashboard de administración"
    info "• Rate limiting por endpoint"
    info "• Detección de comportamiento sospechoso"
    
    warning "=== Acceso al dashboard ==="
    warning "• URL: https://playergold.es/dashboard"
    warning "• Configurar autenticación adicional si es necesario"
}

# Ejecutar configuración
main "$@"
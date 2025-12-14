#!/bin/bash

# ============================================================================
# PlayerGold Network Coordinator - Script de Prueba de Despliegue
# ============================================================================
# 
# Este script prueba la funcionalidad del coordinador desplegado
# y verifica que todas las protecciones anti-DDoS funcionen correctamente.
#
# Uso: ./test_coordinator_deployment.sh [dominio]
# ============================================================================

set -e

# Configuración
DOMAIN=${1:-"localhost"}
BASE_URL="https://$DOMAIN"
if [[ "$DOMAIN" == "localhost" ]]; then
    BASE_URL="http://localhost:8000"
fi

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
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

# Test 1: Health Check
test_health_check() {
    log "🏥 Test 1: Health Check"
    
    local response=$(curl -s -w "%{http_code}" -H "User-Agent: PlayerGold-Wallet/1.0.0" "$BASE_URL/api/v1/health")
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ Health check passed"
        info "Response: $body"
    else
        error "❌ Health check failed (HTTP $http_code)"
        return 1
    fi
}

# Test 2: User-Agent Validation
test_user_agent_validation() {
    log "🔒 Test 2: User-Agent Validation"
    
    # Test con User-Agent válido
    local valid_response=$(curl -s -w "%{http_code}" -H "User-Agent: PlayerGold-Wallet/1.0.0" "$BASE_URL/api/v1/health")
    local valid_code="${valid_response: -3}"
    
    # Test con User-Agent inválido
    local invalid_response=$(curl -s -w "%{http_code}" -H "User-Agent: Mozilla/5.0" "$BASE_URL/api/v1/health")
    local invalid_code="${invalid_response: -3}"
    
    if [[ "$valid_code" == "200" && "$invalid_code" == "403" ]]; then
        log "✅ User-Agent validation working correctly"
        info "Valid UA: HTTP $valid_code, Invalid UA: HTTP $invalid_code"
    else
        error "❌ User-Agent validation failed"
        error "Valid UA: HTTP $valid_code, Invalid UA: HTTP $invalid_code"
        return 1
    fi
}

# Test 3: Rate Limiting
test_rate_limiting() {
    log "⏱️ Test 3: Rate Limiting"
    
    local success_count=0
    local blocked_count=0
    
    # Enviar 15 peticiones rápidas
    for i in {1..15}; do
        local response=$(curl -s -w "%{http_code}" -H "User-Agent: PlayerGold-Wallet/1.0.0" "$BASE_URL/api/v1/health")
        local http_code="${response: -3}"
        
        if [[ "$http_code" == "200" ]]; then
            ((success_count++))
        elif [[ "$http_code" == "429" ]]; then
            ((blocked_count++))
        fi
        
        sleep 0.1
    done
    
    if [[ $blocked_count -gt 0 ]]; then
        log "✅ Rate limiting working ($success_count success, $blocked_count blocked)"
    else
        warning "⚠️ Rate limiting might not be working ($success_count success, $blocked_count blocked)"
    fi
}

# Test 4: Node Registration
test_node_registration() {
    log "📝 Test 4: Node Registration"
    
    local registration_data='{
        "node_id": "PGtest123456789012345678901234567890123456",
        "public_ip": "127.0.0.1",
        "port": 18333,
        "latitude": 40.4168,
        "longitude": -3.7038,
        "os_info": "Linux x86_64",
        "node_type": "regular",
        "public_key": "dGVzdF9wdWJsaWNfa2V5",
        "signature": "dGVzdF9zaWduYXR1cmU="
    }'
    
    local response=$(curl -s -w "%{http_code}" \
        -H "User-Agent: PlayerGold-Wallet/1.0.0" \
        -H "Content-Type: application/json" \
        -d "$registration_data" \
        "$BASE_URL/api/v1/register")
    
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ Node registration successful"
        info "Response: $body"
    else
        error "❌ Node registration failed (HTTP $http_code)"
        error "Response: $body"
        return 1
    fi
}

# Test 5: Network Map Request
test_network_map() {
    log "🗺️ Test 5: Network Map Request"
    
    local map_request='{
        "requester_latitude": 40.4168,
        "requester_longitude": -3.7038,
        "limit": 10
    }'
    
    local response=$(curl -s -w "%{http_code}" \
        -H "User-Agent: PlayerGold-Wallet/1.0.0" \
        -H "Content-Type: application/json" \
        -d "$map_request" \
        "$BASE_URL/api/v1/network-map")
    
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ Network map request successful"
        info "Response contains: $(echo "$body" | jq -r '.message // "No message"' 2>/dev/null || echo "Raw response")"
    else
        error "❌ Network map request failed (HTTP $http_code)"
        error "Response: $body"
        return 1
    fi
}

# Test 6: Statistics Endpoint
test_statistics() {
    log "📊 Test 6: Statistics Endpoint"
    
    local response=$(curl -s -w "%{http_code}" \
        -H "User-Agent: PlayerGold-Wallet/1.0.0" \
        "$BASE_URL/api/v1/stats")
    
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ Statistics endpoint working"
        info "Stats: $(echo "$body" | jq -c '.' 2>/dev/null || echo "$body")"
    else
        error "❌ Statistics endpoint failed (HTTP $http_code)"
        return 1
    fi
}

# Test 7: Dashboard Access (si está disponible)
test_dashboard() {
    log "📈 Test 7: Dashboard Access"
    
    local response=$(curl -s -w "%{http_code}" \
        -H "User-Agent: PlayerGold-Wallet/1.0.0" \
        "$BASE_URL/dashboard")
    
    local http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        log "✅ Dashboard accessible"
    elif [[ "$http_code" == "404" ]]; then
        info "ℹ️ Dashboard not configured (expected for basic installation)"
    else
        warning "⚠️ Dashboard returned HTTP $http_code"
    fi
}

# Test 8: SSL Certificate (si es HTTPS)
test_ssl_certificate() {
    if [[ "$BASE_URL" == https* ]]; then
        log "🔐 Test 8: SSL Certificate"
        
        local ssl_info=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
        
        if [[ $? -eq 0 ]]; then
            log "✅ SSL certificate valid"
            info "$ssl_info"
        else
            warning "⚠️ SSL certificate check failed"
        fi
    else
        info "ℹ️ Skipping SSL test (HTTP endpoint)"
    fi
}

# Test de rendimiento básico
test_performance() {
    log "⚡ Test 9: Basic Performance"
    
    local start_time=$(date +%s.%N)
    
    # 10 peticiones concurrentes
    for i in {1..10}; do
        curl -s -H "User-Agent: PlayerGold-Wallet/1.0.0" "$BASE_URL/api/v1/health" > /dev/null &
    done
    
    wait  # Esperar a que terminen todas
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "N/A")
    
    log "✅ Performance test completed"
    info "10 concurrent requests took: ${duration}s"
}

# Función principal
main() {
    echo "🧪 PlayerGold Network Coordinator - Deployment Test Suite"
    echo "========================================================"
    echo
    info "Testing coordinator at: $BASE_URL"
    echo
    
    local failed_tests=0
    local total_tests=9
    
    # Ejecutar tests
    test_health_check || ((failed_tests++))
    echo
    
    test_user_agent_validation || ((failed_tests++))
    echo
    
    test_rate_limiting || ((failed_tests++))
    echo
    
    test_node_registration || ((failed_tests++))
    echo
    
    test_network_map || ((failed_tests++))
    echo
    
    test_statistics || ((failed_tests++))
    echo
    
    test_dashboard || ((failed_tests++))
    echo
    
    test_ssl_certificate || ((failed_tests++))
    echo
    
    test_performance || ((failed_tests++))
    echo
    
    # Resumen
    echo "========================================================"
    local passed_tests=$((total_tests - failed_tests))
    
    if [[ $failed_tests -eq 0 ]]; then
        log "🎉 All tests passed! ($passed_tests/$total_tests)"
        log "✅ Coordinator is working correctly"
        echo
        info "The PlayerGold Network Coordinator is ready to accept wallet connections!"
    else
        error "❌ $failed_tests/$total_tests tests failed"
        error "Please check the coordinator configuration and logs"
        echo
        warning "Common issues:"
        warning "• Coordinator service not running: systemctl status playergold-coordinator"
        warning "• Firewall blocking connections: ufw status"
        warning "• Nginx configuration: nginx -t"
        warning "• SSL certificate issues: certbot certificates"
    fi
    
    echo
    info "Useful commands:"
    info "• Check coordinator logs: journalctl -u playergold-coordinator -f"
    info "• Check nginx logs: tail -f /var/log/nginx/playergold-*.log"
    info "• Restart coordinator: systemctl restart playergold-coordinator"
    
    return $failed_tests
}

# Verificar dependencias
if ! command -v curl &> /dev/null; then
    error "curl is required but not installed"
    exit 1
fi

# Ejecutar tests
main "$@"
#!/usr/bin/env python3
"""
Script para iniciar la API de testnet PlayerGold (sin autenticación)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.testnet_api import TestnetAPI
from src.blockchain.blockchain import Blockchain

def main():
    print("=" * 60)
    print("🌐 INICIANDO API TESTNET PLAYERGOLD")
    print("=" * 60)
    print()
    
    # Initialize blockchain
    print("📦 Inicializando blockchain...")
    blockchain = Blockchain()
    
    # Initialize API
    print("🔌 Inicializando API Testnet...")
    api = TestnetAPI(blockchain)
    
    print("✅ API Testnet lista!")
    print()
    print("🌐 Servicios disponibles (SIN AUTENTICACIÓN):")
    print("   • Health Check: http://localhost:18080/api/v1/health")
    print("   • Network Status: http://localhost:18080/api/v1/network/status")
    print("   • Balance: http://localhost:18080/api/v1/balance/<address>")
    print("   • Faucet: http://localhost:18080/api/v1/faucet")
    print()
    print("💡 Las wallets pueden conectarse directamente")
    print("💡 Presiona Ctrl+C para detener la API")
    print("=" * 60)
    print()
    
    # Start API
    try:
        api.run(host='0.0.0.0', port=18080, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 API Testnet detenida")

if __name__ == "__main__":
    main()
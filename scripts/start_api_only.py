#!/usr/bin/env python3
"""
Script para iniciar solo la API REST de PlayerGold
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.game_api import GameAPI
from src.blockchain.blockchain import Blockchain

def main():
    print("=" * 60)
    print("🌐 INICIANDO API REST PLAYERGOLD")
    print("=" * 60)
    print()
    
    # Initialize blockchain
    print("📦 Inicializando blockchain...")
    blockchain = Blockchain()
    
    # Initialize API
    print("🔌 Inicializando API REST...")
    api = GameAPI(blockchain)
    
    print("✅ API REST lista!")
    print()
    print("🌐 Servicios disponibles:")
    print("   • Health Check: http://localhost:18080/api/v1/health")
    print("   • Network Status: http://localhost:18080/api/v1/network/status")
    print()
    print("💡 Las wallets ahora pueden conectarse a http://localhost:18080")
    print("💡 Presiona Ctrl+C para detener la API")
    print("=" * 60)
    print()
    
    # Start API
    try:
        api.run(host='0.0.0.0', port=18080, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 API REST detenida")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script para iniciar un nodo PlayerGold en MAINNET

⚠️  ADVERTENCIA: MAINNET USA TOKENS REALES
- Los tokens $PRGLD tienen valor real
- Las transacciones son PERMANENTES e IRREVERSIBLES
- Asegúrate de saber lo que estás haciendo

Uso:
    python scripts/start_mainnet_node.py [--node-id NODE_ID] [--port PORT] [--confirm]
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.network.network_manager import NetworkManager, NetworkType
from src.p2p.network import P2PNetwork

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_mainnet_warning():
    """Show warning about mainnet usage"""
    print("")
    print("=" * 70)
    print("⚠️  ADVERTENCIA IMPORTANTE - MAINNET")
    print("=" * 70)
    print("")
    print("Estás a punto de iniciar un nodo en la RED PRINCIPAL (MAINNET).")
    print("")
    print("IMPORTANTE:")
    print("  • Los tokens $PRGLD tienen VALOR REAL")
    print("  • Las transacciones son PERMANENTES e IRREVERSIBLES")
    print("  • Los errores pueden resultar en PÉRDIDA DE FONDOS")
    print("  • Asegúrate de tener backups de tus claves privadas")
    print("  • Lee la documentación antes de proceder")
    print("")
    print("RESPONSABILIDAD:")
    print("  • El desarrollador NO se hace responsable de pérdidas")
    print("  • Usas este software BAJO TU PROPIA RESPONSABILIDAD")
    print("  • Consulta PROJECT_INFO.md para más información")
    print("")
    print("=" * 70)
    print("")


async def start_mainnet_node(node_id: str, port: int = None):
    """
    Start a mainnet node
    
    Args:
        node_id: Unique identifier for this node
        port: Optional custom port (uses 8333 by default)
    """
    logger.info("=" * 60)
    logger.info("PlayerGold Mainnet Node")
    logger.info("=" * 60)
    logger.info("")
    
    # Configure for mainnet
    network_manager = NetworkManager()
    
    # Switch to mainnet
    if not network_manager.is_mainnet():
        logger.info("Switching to mainnet...")
        network_manager.switch_network(NetworkType.MAINNET)
    
    # Get network info
    network_info = network_manager.get_network_info()
    
    logger.info("Network Configuration:")
    logger.info(f"  Type: MAINNET")
    logger.info(f"  Network ID: {network_info['network_id']}")
    logger.info(f"  Default Port: {network_info['p2p_port']}")
    logger.info(f"  Bootstrap Nodes: {network_info['bootstrap_nodes']}")
    logger.info("")
    
    logger.warning("⚠️  Mainnet Information:")
    logger.warning("  • Tokens have REAL value")
    logger.warning("  • Transactions are PERMANENT")
    logger.warning("  • Data stored in: ./data/mainnet")
    logger.warning("  • Use with CAUTION")
    logger.info("")
    
    # Initialize P2P network
    logger.info(f"Initializing node: {node_id}")
    p2p = P2PNetwork(
        node_id=node_id,
        listen_port=port,
        network_manager=network_manager
    )
    
    # Start P2P network
    logger.info("Starting P2P network...")
    await p2p.start()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ Mainnet node started successfully!")
    logger.info("=" * 60)
    logger.info(f"  Node ID: {node_id}")
    logger.info(f"  Network: {p2p.network_id}")
    logger.info(f"  Listening on port: {p2p.listen_port}")
    logger.info("")
    logger.info("Press Ctrl+C to stop the node")
    logger.info("=" * 60)
    logger.info("")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
            
            # Periodically log stats
            if int(asyncio.get_event_loop().time()) % 60 == 0:
                stats = p2p.get_network_stats()
                logger.info(f"Stats: {stats['peer_count']} peers, "
                          f"{stats['active_connections']} connections")
    
    except KeyboardInterrupt:
        logger.info("")
        logger.info("Shutting down mainnet node...")
        await p2p.stop()
        logger.info("✓ Node stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Start a PlayerGold mainnet node',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  WARNING: This starts a MAINNET node with REAL tokens!

Examples:
  python scripts/start_mainnet_node.py --confirm
  python scripts/start_mainnet_node.py --node-id my_node --confirm
  python scripts/start_mainnet_node.py --node-id node1 --port 9000 --confirm
        """
    )
    
    parser.add_argument(
        '--node-id',
        type=str,
        default='mainnet_node_1',
        help='Unique identifier for this node (default: mainnet_node_1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to listen on (default: 8333 for mainnet)'
    )
    
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm that you understand mainnet risks'
    )
    
    args = parser.parse_args()
    
    # Show warning
    show_mainnet_warning()
    
    # Require confirmation
    if not args.confirm:
        print("ERROR: Debes usar --confirm para iniciar un nodo mainnet")
        print("Esto confirma que entiendes los riesgos y responsabilidades.")
        print("")
        print("Ejemplo: python scripts/start_mainnet_node.py --confirm")
        print("")
        sys.exit(1)
    
    # Ask for final confirmation
    try:
        response = input("¿Estás seguro de que quieres iniciar un nodo MAINNET? (escribe 'SI' para confirmar): ")
        if response.strip().upper() != 'SI':
            print("Operación cancelada.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nOperación cancelada.")
        sys.exit(0)
    
    print("")
    print("Iniciando nodo mainnet...")
    print("")
    
    try:
        asyncio.run(start_mainnet_node(args.node_id, args.port))
    except Exception as e:
        logger.error(f"Error starting mainnet node: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Parche para agregar conexión automática a bootstrap nodes en P2P network
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def patch_p2p_network():
    """Aplicar parche al archivo P2P network para agregar conexión automática"""
    
    p2p_file = Path("src/p2p/network.py")
    
    if not p2p_file.exists():
        print(f"❌ Archivo {p2p_file} no encontrado")
        return False
    
    print(f"🔧 Aplicando parche a {p2p_file}...")
    
    # Leer archivo original
    with open(p2p_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya está parcheado
    if "connect_to_bootstrap_nodes" in content:
        print("✅ El archivo ya está parcheado")
        return True
    
    # Encontrar el método start() y agregar conexión a bootstrap nodes
    start_method_pattern = "        self.running = True\n        logger.info(f\"P2P network started successfully on port {self.listen_port}\")"
    
    if start_method_pattern in content:
        # Agregar código para conectar a bootstrap nodes
        bootstrap_connection_code = """        self.running = True
        
        # Connect to bootstrap nodes
        asyncio.create_task(self._connect_to_bootstrap_nodes())
        
        logger.info(f"P2P network started successfully on port {self.listen_port}")"""
        
        content = content.replace(start_method_pattern, bootstrap_connection_code)
        
        # Agregar el método _connect_to_bootstrap_nodes
        bootstrap_method = '''
    async def _connect_to_bootstrap_nodes(self):
        """Connect to bootstrap nodes from network configuration"""
        try:
            # Get bootstrap nodes from network manager
            network_config = self.network_manager.get_network_config()
            bootstrap_nodes = getattr(network_config, 'bootstrap_nodes', [])
            
            if not bootstrap_nodes:
                logger.warning("No bootstrap nodes configured")
                return
            
            logger.info(f"Attempting to connect to {len(bootstrap_nodes)} bootstrap nodes...")
            
            # Wait a bit for server to be fully ready
            await asyncio.sleep(2)
            
            successful_connections = 0
            for node_address in bootstrap_nodes:
                try:
                    # Parse address (format: "ip:port")
                    if ':' in node_address:
                        ip, port_str = node_address.split(':')
                        port = int(port_str)
                    else:
                        ip = node_address
                        port = self.listen_port
                    
                    # Don't connect to ourselves
                    if ip == '127.0.0.1' or ip == 'localhost':
                        # Get our external IP to compare
                        try:
                            import socket
                            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            sock.connect(("8.8.8.8", 80))
                            our_ip = sock.getsockname()[0]
                            sock.close()
                            
                            if ip == our_ip and port == self.listen_port:
                                logger.debug(f"Skipping connection to self: {node_address}")
                                continue
                        except:
                            pass
                    
                    logger.info(f"Attempting to connect to bootstrap node: {ip}:{port}")
                    
                    # Try to connect
                    success = await self.connect_to_peer(ip, port)
                    if success:
                        successful_connections += 1
                        logger.info(f"✅ Connected to bootstrap node {ip}:{port}")
                    else:
                        logger.warning(f"❌ Failed to connect to bootstrap node {ip}:{port}")
                    
                    # Small delay between connection attempts
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error connecting to bootstrap node {node_address}: {e}")
            
            if successful_connections > 0:
                logger.info(f"✅ Successfully connected to {successful_connections} bootstrap nodes")
            else:
                logger.warning("❌ Failed to connect to any bootstrap nodes")
                
                # Schedule retry in 30 seconds
                logger.info("Scheduling bootstrap connection retry in 30 seconds...")
                await asyncio.sleep(30)
                asyncio.create_task(self._connect_to_bootstrap_nodes())
                
        except Exception as e:
            logger.error(f"Error in bootstrap connection process: {e}")
'''
        
        # Encontrar un buen lugar para insertar el método (antes del último método)
        insert_position = content.rfind('\nclass MDNSService:')
        if insert_position != -1:
            content = content[:insert_position] + bootstrap_method + content[insert_position:]
        else:
            # Si no encontramos MDNSService, agregar al final de la clase P2PNetwork
            insert_position = content.rfind('\n\nclass')
            if insert_position != -1:
                content = content[:insert_position] + bootstrap_method + content[insert_position:]
        
        # Escribir archivo parcheado
        with open(p2p_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Parche aplicado exitosamente")
        return True
    else:
        print("❌ No se pudo encontrar el patrón para aplicar el parche")
        return False

def patch_network_manager():
    """Parche para NetworkManager para asegurar que bootstrap_nodes esté disponible"""
    
    network_file = Path("src/network/network_manager.py")
    
    if not network_file.exists():
        print(f"❌ Archivo {network_file} no encontrado")
        return False
    
    print(f"🔧 Verificando {network_file}...")
    
    # Leer archivo
    with open(network_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si bootstrap_nodes está en NetworkConfig
    if "bootstrap_nodes" in content:
        print("✅ NetworkConfig ya tiene bootstrap_nodes")
        return True
    
    # Si no está, agregarlo
    if "@dataclass" in content and "class NetworkConfig:" in content:
        # Encontrar la clase NetworkConfig y agregar bootstrap_nodes
        config_pattern = "class NetworkConfig:"
        config_index = content.find(config_pattern)
        
        if config_index != -1:
            # Encontrar el final de la clase (próxima clase o final del archivo)
            next_class = content.find("\n\nclass", config_index + 1)
            if next_class == -1:
                next_class = len(content)
            
            # Buscar donde agregar bootstrap_nodes
            config_section = content[config_index:next_class]
            
            # Agregar bootstrap_nodes si no existe
            if "bootstrap_nodes" not in config_section:
                # Encontrar un buen lugar para insertar (después de p2p_port)
                insert_pattern = "p2p_port: int"
                insert_index = content.find(insert_pattern, config_index)
                
                if insert_index != -1:
                    # Encontrar el final de esa línea
                    line_end = content.find('\n', insert_index)
                    if line_end != -1:
                        # Insertar bootstrap_nodes
                        bootstrap_line = "\n    bootstrap_nodes: List[str] = field(default_factory=list)"
                        content = content[:line_end] + bootstrap_line + content[line_end:]
                        
                        # También necesitamos importar List y field si no están
                        if "from typing import" in content and "List" not in content[:content.find("from typing import") + 100]:
                            content = content.replace("from typing import", "from typing import List,")
                        
                        if "from dataclasses import" in content and "field" not in content[:content.find("from dataclasses import") + 100]:
                            content = content.replace("from dataclasses import", "from dataclasses import dataclass, field")
                        
                        # Escribir archivo actualizado
                        with open(network_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        print("✅ Agregado bootstrap_nodes a NetworkConfig")
                        return True
    
    print("⚠️  No se pudo agregar bootstrap_nodes automáticamente")
    return False

def main():
    """Aplicar todos los parches necesarios"""
    print("🔧 Aplicando parches para conectividad P2P...")
    print("=" * 50)
    
    success = True
    
    # Parche 1: NetworkManager
    if not patch_network_manager():
        success = False
    
    # Parche 2: P2P Network
    if not patch_p2p_network():
        success = False
    
    print("=" * 50)
    if success:
        print("🎉 ¡Todos los parches aplicados exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Reiniciar ambos nodos testnet")
        print("2. Los nodos deberían conectarse automáticamente")
        print("3. Verificar logs para confirmar conexión")
        print("\n🔍 Para verificar:")
        print("   python scripts/diagnostico_red_testnet.py")
    else:
        print("❌ Algunos parches fallaron")
        print("Revisar manualmente los archivos mencionados")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error aplicando parches: {e}")
        sys.exit(1)
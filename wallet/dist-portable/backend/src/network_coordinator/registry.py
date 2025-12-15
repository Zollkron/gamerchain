"""
Node Registry - Core database operations for network coordinator
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from contextlib import contextmanager
import logging

from .models import NetworkNode, NodeStatus, NodeType, Location
from .encryption import NetworkEncryption, encrypt_ip_address, decrypt_ip_address

logger = logging.getLogger(__name__)


class NodeRegistry:
    """Manages the database of network nodes"""
    
    def __init__(self, db_path: str = "network_nodes.db", encryption: NetworkEncryption = None):
        self.db_path = db_path
        self.encryption = encryption or NetworkEncryption()
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    encrypted_ip BLOB NOT NULL,
                    ip_salt BLOB NOT NULL,
                    port INTEGER NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    os_info TEXT NOT NULL,
                    is_genesis BOOLEAN NOT NULL,
                    last_keepalive TIMESTAMP NOT NULL,
                    blockchain_height INTEGER NOT NULL,
                    connected_peers INTEGER NOT NULL,
                    node_type TEXT NOT NULL,
                    reputation_score REAL NOT NULL DEFAULT 1.0,
                    created_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    public_key TEXT,
                    metadata TEXT
                )
            """)
            
            # Create indexes for efficient queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON nodes(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_last_keepalive ON nodes(last_keepalive)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_location ON nodes(latitude, longitude)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_node_type ON nodes(node_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_is_genesis ON nodes(is_genesis)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup"""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def add_node(self, node: NetworkNode, public_key: str = None) -> bool:
        """Add a new node to the registry with IP deduplication"""
        try:
            # Check if a node with the same IP already exists and is active
            existing_node = self.get_node_by_ip(node.public_ip)
            if existing_node and existing_node.status == NodeStatus.ACTIVE:
                # Update existing node instead of creating duplicate
                logger.info(f"Updating existing node {existing_node.node_id} from IP {node.public_ip}")
                return self.update_existing_node(existing_node.node_id, node, public_key)
            
            # Encrypt IP address
            encrypted_ip, ip_salt = encrypt_ip_address(node.public_ip, self.encryption)
            
            with self._get_connection() as conn:
                # Check if this specific node_id already exists
                cursor = conn.execute("SELECT node_id FROM nodes WHERE node_id = ?", (node.node_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing node
                    conn.execute("""
                        UPDATE nodes SET 
                        encrypted_ip = ?, ip_salt = ?, port = ?, latitude = ?, longitude = ?,
                        os_info = ?, is_genesis = ?, last_keepalive = ?, blockchain_height = ?,
                        connected_peers = ?, node_type = ?, status = ?, public_key = ?
                        WHERE node_id = ?
                    """, (
                        encrypted_ip, ip_salt, node.port, node.latitude, node.longitude,
                        node.os_info, node.is_genesis, node.last_keepalive, node.blockchain_height,
                        node.connected_peers, node.node_type.value, node.status.value, public_key,
                        node.node_id
                    ))
                    logger.info(f"Updated existing node {node.node_id}")
                else:
                    # Insert new node
                    conn.execute("""
                        INSERT INTO nodes (
                            node_id, encrypted_ip, ip_salt, port, latitude, longitude,
                            os_info, is_genesis, last_keepalive, blockchain_height,
                            connected_peers, node_type, reputation_score, created_at,
                            status, public_key, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        node.node_id, encrypted_ip, ip_salt, node.port,
                        node.latitude, node.longitude, node.os_info, node.is_genesis,
                        node.last_keepalive, node.blockchain_height, node.connected_peers,
                        node.node_type.value, node.reputation_score, node.created_at,
                        node.status.value, public_key, json.dumps({})
                    ))
                    logger.info(f"Added new node {node.node_id}")
                
                conn.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to add node {node.node_id}: {e}")
            return False
    
    def update_node_status(self, node_id: str, status: NodeStatus, 
                          blockchain_height: int = None, connected_peers: int = None) -> bool:
        """Update node status and optional metrics"""
        try:
            with self._get_connection() as conn:
                update_fields = ["status = ?", "last_keepalive = ?"]
                params = [status.value, datetime.utcnow()]
                
                if blockchain_height is not None:
                    update_fields.append("blockchain_height = ?")
                    params.append(blockchain_height)
                
                if connected_peers is not None:
                    update_fields.append("connected_peers = ?")
                    params.append(connected_peers)
                
                params.append(node_id)
                
                query = f"UPDATE nodes SET {', '.join(update_fields)} WHERE node_id = ?"
                cursor = conn.execute(query, params)
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.debug(f"Updated status for node {node_id} to {status.value}")
                    return True
                else:
                    logger.warning(f"Node {node_id} not found for status update")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update node {node_id} status: {e}")
            return False
    
    def get_node(self, node_id: str) -> Optional[NetworkNode]:
        """Get a specific node by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_node(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get node {node_id}: {e}")
            return None
    
    def get_node_by_ip(self, ip_address: str) -> Optional[NetworkNode]:
        """Get a node by IP address (for deduplication)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM nodes WHERE status = 'active'")
                
                # We need to decrypt each IP to compare (not ideal for performance, but necessary)
                for row in cursor.fetchall():
                    try:
                        decrypted_ip = decrypt_ip_address(row['encrypted_ip'], row['ip_salt'], self.encryption)
                        if decrypted_ip == ip_address:
                            return self._row_to_node(row)
                    except Exception as decrypt_error:
                        logger.warning(f"Failed to decrypt IP for node {row['node_id']}: {decrypt_error}")
                        continue
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get node by IP {ip_address}: {e}")
            return None
    
    def update_existing_node(self, node_id: str, new_node_data: NetworkNode, public_key: str = None) -> bool:
        """Update an existing node with new data"""
        try:
            # Encrypt IP address
            encrypted_ip, ip_salt = encrypt_ip_address(new_node_data.public_ip, self.encryption)
            
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE nodes SET 
                    encrypted_ip = ?, ip_salt = ?, port = ?, latitude = ?, longitude = ?,
                    os_info = ?, last_keepalive = ?, status = ?, public_key = ?
                    WHERE node_id = ?
                """, (
                    encrypted_ip, ip_salt, new_node_data.port, new_node_data.latitude, 
                    new_node_data.longitude, new_node_data.os_info, new_node_data.last_keepalive,
                    new_node_data.status.value, public_key, node_id
                ))
                conn.commit()
                
                logger.info(f"Updated existing node {node_id} with new data")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update existing node {node_id}: {e}")
            return False
    
    def get_active_nodes(self, max_age_minutes: int = 5) -> List[NetworkNode]:
        """Get all active nodes with recent keepalive"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
            
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM nodes 
                    WHERE status = 'active' AND last_keepalive > ?
                    ORDER BY last_keepalive DESC
                """, (cutoff_time,))
                
                nodes = []
                for row in cursor.fetchall():
                    node = self._row_to_node(row)
                    if node:
                        nodes.append(node)
                
                return nodes
                
        except Exception as e:
            logger.error(f"Failed to get active nodes: {e}")
            return []
    
    def get_nodes_by_proximity(self, location: Location, max_distance_km: float = None, 
                              limit: int = None) -> List[Tuple[NetworkNode, float]]:
        """Get nodes ordered by proximity to a location"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM nodes WHERE status = 'active'
                    ORDER BY last_keepalive DESC
                """)
                
                nodes_with_distance = []
                for row in cursor.fetchall():
                    node = self._row_to_node(row)
                    if node:
                        node_location = Location(node.latitude, node.longitude)
                        distance = location.distance_to(node_location)
                        
                        if max_distance_km is None or distance <= max_distance_km:
                            nodes_with_distance.append((node, distance))
                
                # Sort by distance
                nodes_with_distance.sort(key=lambda x: x[1])
                
                if limit:
                    nodes_with_distance = nodes_with_distance[:limit]
                
                return nodes_with_distance
                
        except Exception as e:
            logger.error(f"Failed to get nodes by proximity: {e}")
            return []
    
    def mark_inactive_nodes(self, timeout_minutes: int = 5) -> int:
        """Mark nodes as inactive if they haven't sent keepalive recently"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE nodes 
                    SET status = 'inactive' 
                    WHERE status = 'active' AND last_keepalive < ?
                """, (cutoff_time,))
                conn.commit()
                
                inactive_count = cursor.rowcount
                if inactive_count > 0:
                    logger.info(f"Marked {inactive_count} nodes as inactive")
                
                return inactive_count
                
        except Exception as e:
            logger.error(f"Failed to mark inactive nodes: {e}")
            return 0
    
    def get_network_statistics(self) -> Dict:
        """Get network statistics"""
        try:
            with self._get_connection() as conn:
                # Total nodes by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM nodes 
                    GROUP BY status
                """)
                status_counts = dict(cursor.fetchall())
                
                # Genesis nodes
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM nodes 
                    WHERE is_genesis = 1 AND status = 'active'
                """)
                genesis_count = cursor.fetchone()[0]
                
                # Node types
                cursor = conn.execute("""
                    SELECT node_type, COUNT(*) as count 
                    FROM nodes 
                    WHERE status = 'active'
                    GROUP BY node_type
                """)
                type_counts = dict(cursor.fetchall())
                
                # Average blockchain height
                cursor = conn.execute("""
                    SELECT AVG(blockchain_height) FROM nodes 
                    WHERE status = 'active'
                """)
                avg_height = cursor.fetchone()[0] or 0
                
                return {
                    'total_nodes': sum(status_counts.values()),
                    'active_nodes': status_counts.get('active', 0),
                    'inactive_nodes': status_counts.get('inactive', 0),
                    'suspicious_nodes': status_counts.get('suspicious', 0),
                    'genesis_nodes': genesis_count,
                    'node_types': type_counts,
                    'average_blockchain_height': round(avg_height, 2),
                    'last_updated': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get network statistics: {e}")
            return {}
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the registry"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Removed node {node_id} from registry")
                    return True
                else:
                    logger.warning(f"Node {node_id} not found for removal")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to remove node {node_id}: {e}")
            return False
    
    def _row_to_node(self, row) -> Optional[NetworkNode]:
        """Convert database row to NetworkNode object"""
        try:
            # Decrypt IP address
            decrypted_ip = decrypt_ip_address(row['encrypted_ip'], row['ip_salt'], self.encryption)
            
            return NetworkNode(
                node_id=row['node_id'],
                public_ip=decrypted_ip,
                port=row['port'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                os_info=row['os_info'],
                is_genesis=bool(row['is_genesis']),
                last_keepalive=row['last_keepalive'],
                blockchain_height=row['blockchain_height'],
                connected_peers=row['connected_peers'],
                node_type=NodeType(row['node_type']),
                reputation_score=row['reputation_score'],
                created_at=row['created_at'],
                status=NodeStatus(row['status'])
            )
            
        except Exception as e:
            logger.error(f"Failed to convert row to node: {e}")
            return None
    
    def cleanup_old_nodes(self, days_old: int = 30) -> int:
        """Remove nodes that have been inactive for a long time"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)
            
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM nodes 
                    WHERE status = 'inactive' AND last_keepalive < ?
                """, (cutoff_time,))
                conn.commit()
                
                removed_count = cursor.rowcount
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old inactive nodes")
                
                return removed_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old nodes: {e}")
            return 0
    
    def cleanup_duplicate_ips(self) -> int:
        """Remove duplicate nodes from the same IP, keeping the most recent"""
        try:
            removed_count = 0
            ip_groups = {}
            
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM nodes ORDER BY last_keepalive DESC")
                
                # Group nodes by IP address
                for row in cursor.fetchall():
                    try:
                        decrypted_ip = decrypt_ip_address(row['encrypted_ip'], row['ip_salt'], self.encryption)
                        
                        if decrypted_ip not in ip_groups:
                            ip_groups[decrypted_ip] = []
                        ip_groups[decrypted_ip].append(row)
                        
                    except Exception as decrypt_error:
                        logger.warning(f"Failed to decrypt IP for node {row['node_id']}: {decrypt_error}")
                        continue
                
                # Remove duplicates (keep the most recent one per IP)
                for ip, nodes in ip_groups.items():
                    if len(nodes) > 1:
                        # Keep the first one (most recent due to ORDER BY), remove the rest
                        nodes_to_remove = nodes[1:]
                        
                        for node_row in nodes_to_remove:
                            conn.execute("DELETE FROM nodes WHERE node_id = ?", (node_row['node_id'],))
                            removed_count += 1
                            logger.info(f"Removed duplicate node {node_row['node_id']} from IP {ip}")
                
                conn.commit()
                
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} duplicate IP nodes")
                
                return removed_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup duplicate IPs: {e}")
            return 0
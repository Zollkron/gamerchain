"""
Backup Manager - Handles distributed backup of network registry
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from .models import NetworkNode, EncryptedNetworkMap, BackupResult, SyncResult
from .registry import NodeRegistry
from .encryption import NetworkEncryption

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages distributed backup of network registry"""
    
    def __init__(self, registry: NodeRegistry, encryption: NetworkEncryption):
        self.registry = registry
        self.encryption = encryption
        self.backup_nodes: List[str] = []  # List of backup node URLs
        self.last_backup_time = datetime.utcnow()
        self.backup_version = 1
    
    async def register_backup_node(self, node_url: str, node_id: str) -> bool:
        """Register a node as a backup provider"""
        try:
            # Verify the node is active and capable of backup
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{node_url}/api/backup/health", timeout=10) as response:
                    if response.status == 200:
                        if node_url not in self.backup_nodes:
                            self.backup_nodes.append(node_url)
                            logger.info(f"Registered backup node: {node_url}")
                        return True
                    else:
                        logger.warning(f"Backup node health check failed: {node_url}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to register backup node {node_url}: {e}")
            return False
    
    async def distribute_update(self) -> List[BackupResult]:
        """Distribute updated network map to backup nodes"""
        try:
            # Get current active nodes
            active_nodes = self.registry.get_active_nodes()
            
            # Create encrypted map
            encrypted_map = self.encryption.encrypt_node_list(active_nodes)
            self.backup_version += 1
            encrypted_map.version = self.backup_version
            
            # Distribute to backup nodes
            results = []
            tasks = []
            
            for backup_url in self.backup_nodes:
                task = self._send_backup_to_node(backup_url, encrypted_map)
                tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_backups = []
            failed_backups = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_backups.append(BackupResult(
                        backup_node_id=self.backup_nodes[i],
                        success=False,
                        timestamp=datetime.utcnow(),
                        error_message=str(result)
                    ))
                else:
                    successful_backups.append(result)
            
            self.last_backup_time = datetime.utcnow()
            
            logger.info(f"Backup distribution: {len(successful_backups)} successful, {len(failed_backups)} failed")
            
            return successful_backups + failed_backups
            
        except Exception as e:
            logger.error(f"Backup distribution failed: {e}")
            return []
    
    async def _send_backup_to_node(self, backup_url: str, encrypted_map: EncryptedNetworkMap) -> BackupResult:
        """Send backup data to a specific node"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "encrypted_map": encrypted_map.to_dict(),
                    "coordinator_id": "main",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                async with session.post(
                    f"{backup_url}/api/backup/update",
                    json=payload,
                    timeout=30
                ) as response:
                    
                    if response.status == 200:
                        return BackupResult(
                            backup_node_id=backup_url,
                            success=True,
                            timestamp=datetime.utcnow()
                        )
                    else:
                        error_text = await response.text()
                        return BackupResult(
                            backup_node_id=backup_url,
                            success=False,
                            timestamp=datetime.utcnow(),
                            error_message=f"HTTP {response.status}: {error_text}"
                        )
                        
        except Exception as e:
            return BackupResult(
                backup_node_id=backup_url,
                success=False,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def get_backup_from_node(self, backup_url: str) -> Optional[EncryptedNetworkMap]:
        """Retrieve backup data from a specific node"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{backup_url}/api/backup/latest", timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return EncryptedNetworkMap.from_dict(data["encrypted_map"])
                    else:
                        logger.warning(f"Failed to get backup from {backup_url}: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Failed to retrieve backup from {backup_url}: {e}")
            return None
    
    async def sync_with_backups(self) -> SyncResult:
        """Synchronize with backup nodes and resolve conflicts"""
        try:
            # Get backups from all nodes
            backup_maps = {}
            tasks = []
            
            for backup_url in self.backup_nodes:
                task = self.get_backup_from_node(backup_url)
                tasks.append((backup_url, task))
            
            if not tasks:
                return SyncResult(
                    success=True,
                    synced_nodes=0,
                    conflicts_resolved=0,
                    timestamp=datetime.utcnow(),
                    error_message="No backup nodes available"
                )
            
            # Gather results
            for backup_url, task in tasks:
                try:
                    backup_map = await task
                    if backup_map:
                        backup_maps[backup_url] = backup_map
                except Exception as e:
                    logger.error(f"Failed to sync with {backup_url}: {e}")
            
            # Find the most recent valid backup
            latest_map = None
            latest_timestamp = datetime.min
            
            for backup_url, backup_map in backup_maps.items():
                if backup_map.timestamp > latest_timestamp:
                    # Verify signature
                    try:
                        nodes = self.encryption.decrypt_node_list(backup_map)
                        latest_map = backup_map
                        latest_timestamp = backup_map.timestamp
                    except Exception as e:
                        logger.warning(f"Invalid backup from {backup_url}: {e}")
            
            conflicts_resolved = 0
            
            # If we found a newer backup, update our registry
            if latest_map and latest_timestamp > self.last_backup_time:
                try:
                    nodes = self.encryption.decrypt_node_list(latest_map)
                    
                    # Update registry with backup data
                    for node in nodes:
                        self.registry.add_node(node)
                    
                    self.backup_version = latest_map.version
                    self.last_backup_time = latest_timestamp
                    conflicts_resolved = 1
                    
                    logger.info(f"Synchronized with backup: {len(nodes)} nodes, version {latest_map.version}")
                    
                except Exception as e:
                    logger.error(f"Failed to apply backup: {e}")
            
            return SyncResult(
                success=True,
                synced_nodes=len(backup_maps),
                conflicts_resolved=conflicts_resolved,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Backup synchronization failed: {e}")
            return SyncResult(
                success=False,
                synced_nodes=0,
                conflicts_resolved=0,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def handle_coordinator_failure(self) -> bool:
        """Handle main coordinator failure by promoting a backup"""
        try:
            # In a real implementation, this would involve:
            # 1. Detecting coordinator failure
            # 2. Electing a new primary from backups
            # 3. Updating DNS/load balancer
            # 4. Notifying all nodes of the change
            
            logger.info("Coordinator failure handling not yet implemented")
            return False
            
        except Exception as e:
            logger.error(f"Coordinator failure handling failed: {e}")
            return False
    
    def remove_backup_node(self, node_url: str) -> bool:
        """Remove a backup node from the list"""
        try:
            if node_url in self.backup_nodes:
                self.backup_nodes.remove(node_url)
                logger.info(f"Removed backup node: {node_url}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove backup node {node_url}: {e}")
            return False
    
    def get_backup_status(self) -> Dict:
        """Get backup system status"""
        return {
            "backup_nodes_count": len(self.backup_nodes),
            "backup_nodes": self.backup_nodes,
            "last_backup_time": self.last_backup_time.isoformat(),
            "backup_version": self.backup_version,
            "status": "healthy" if self.backup_nodes else "no_backups"
        }
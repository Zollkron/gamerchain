"""
Network Coordinator Server - Main FastAPI application
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from .models import (
    NetworkNode, NodeType, NodeStatus, RegistrationRequest, 
    KeepAliveMessage, EncryptedNetworkMap, Location, NodeStatusUpdate
)
from .registry import NodeRegistry
from .encryption import NetworkEncryption, NodeAuthentication
from .backup_manager import BackupManager
from .fork_detector import ForkDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
registry: Optional[NodeRegistry] = None
encryption: Optional[NetworkEncryption] = None
backup_manager: Optional[BackupManager] = None
fork_detector: Optional[ForkDetector] = None
auth = NodeAuthentication()
security = HTTPBearer()


# Pydantic models for API
class NodeRegistrationRequest(BaseModel):
    node_id: str
    public_ip: str
    port: int = Field(ge=1, le=65535)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    os_info: str
    node_type: str
    public_key: str
    signature: str


class KeepAliveRequest(BaseModel):
    node_id: str
    blockchain_height: int = Field(ge=0)
    connected_peers: int = Field(ge=0)
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0, le=100)
    network_latency: float = Field(ge=0)
    ai_model_loaded: bool = False
    mining_active: bool = False
    signature: str


class NetworkMapRequest(BaseModel):
    requester_latitude: Optional[float] = Field(None, ge=-90, le=90)
    requester_longitude: Optional[float] = Field(None, ge=-180, le=180)
    max_distance_km: Optional[float] = Field(None, ge=0)
    limit: Optional[int] = Field(None, ge=1, le=1000)


class NetworkStatsResponse(BaseModel):
    total_nodes: int
    active_nodes: int
    inactive_nodes: int
    genesis_nodes: int
    node_types: Dict[str, int]
    average_blockchain_height: float
    last_updated: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global registry, encryption, backup_manager, fork_detector
    
    # Initialize components
    logger.info("Initializing Network Coordinator...")
    
    encryption = NetworkEncryption()
    registry = NodeRegistry(encryption=encryption)
    backup_manager = BackupManager(registry, encryption)
    fork_detector = ForkDetector(registry)
    
    # Start background tasks
    asyncio.create_task(keepalive_monitor())
    asyncio.create_task(backup_sync_task())
    asyncio.create_task(fork_detection_task())
    
    logger.info("Network Coordinator initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Network Coordinator...")


# Create FastAPI app
app = FastAPI(
    title="PlayerGold Network Coordinator",
    description="Centralized network registry with distributed backup for PlayerGold blockchain",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_node_signature(node_id: str, signature: str, message: str) -> bool:
    """Verify node signature for authentication"""
    try:
        # In a real implementation, we'd look up the public key from the registry
        # For now, we'll implement basic signature verification
        node = registry.get_node(node_id)
        if not node:
            return False
        
        # TODO: Implement proper signature verification with stored public keys
        return True  # Placeholder
        
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


@app.post("/api/v1/register", response_model=Dict[str, str])
async def register_node(request: NodeRegistrationRequest, background_tasks: BackgroundTasks):
    """Register a new node in the network"""
    try:
        # Validate node type
        try:
            node_type = NodeType(request.node_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid node type")
        
        # Verify signature (placeholder implementation)
        # TODO: Implement proper signature verification
        
        # Create network node
        node = NetworkNode(
            node_id=request.node_id,
            public_ip=request.public_ip,
            port=request.port,
            latitude=request.latitude,
            longitude=request.longitude,
            os_info=request.os_info,
            is_genesis=(node_type == NodeType.GENESIS),
            last_keepalive=datetime.utcnow(),
            blockchain_height=0,
            connected_peers=0,
            node_type=node_type,
            status=NodeStatus.ACTIVE
        )
        
        # Add to registry
        success = registry.add_node(node, request.public_key)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to register node")
        
        # Schedule backup distribution
        background_tasks.add_task(backup_manager.distribute_update)
        
        logger.info(f"Registered new node: {request.node_id}")
        
        return {
            "status": "success",
            "message": "Node registered successfully",
            "node_id": request.node_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/keepalive", response_model=Dict[str, str])
async def keepalive(request: KeepAliveRequest):
    """Process keepalive message from node"""
    try:
        # Verify signature
        # TODO: Implement proper signature verification
        
        # Update node status
        success = registry.update_node_status(
            request.node_id,
            NodeStatus.ACTIVE,
            request.blockchain_height,
            request.connected_peers
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return {
            "status": "success",
            "message": "KeepAlive processed",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KeepAlive processing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/network-map", response_model=Dict)
async def get_network_map(request: NetworkMapRequest):
    """Get encrypted network map"""
    try:
        # Get active nodes
        active_nodes = registry.get_active_nodes()
        
        if not active_nodes:
            return {
                "status": "success",
                "message": "No active nodes found",
                "map": None
            }
        
        # Filter by proximity if requested
        if request.requester_latitude is not None and request.requester_longitude is not None:
            requester_location = Location(request.requester_latitude, request.requester_longitude)
            nodes_with_distance = registry.get_nodes_by_proximity(
                requester_location,
                request.max_distance_km,
                request.limit
            )
            active_nodes = [node for node, _ in nodes_with_distance]
        elif request.limit:
            active_nodes = active_nodes[:request.limit]
        
        # Create encrypted map
        encrypted_map = encryption.encrypt_node_list(active_nodes)
        
        return {
            "status": "success",
            "message": "Network map generated",
            "map": encrypted_map.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Network map generation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/stats", response_model=NetworkStatsResponse)
async def get_network_stats():
    """Get network statistics"""
    try:
        stats = registry.get_network_statistics()
        return NetworkStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Stats generation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.delete("/api/v1/nodes/{node_id}")
async def remove_node(node_id: str, background_tasks: BackgroundTasks):
    """Remove a node from the registry (admin only)"""
    try:
        success = registry.remove_node(node_id)
        if not success:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Schedule backup distribution
        background_tasks.add_task(backup_manager.distribute_update)
        
        return {
            "status": "success",
            "message": f"Node {node_id} removed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Node removal failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Background tasks
async def keepalive_monitor():
    """Monitor nodes and mark inactive ones"""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            inactive_count = registry.mark_inactive_nodes(timeout_minutes=5)
            if inactive_count > 0:
                logger.info(f"Marked {inactive_count} nodes as inactive")
                # Trigger backup update if nodes changed status
                await backup_manager.distribute_update()
                
        except Exception as e:
            logger.error(f"KeepAlive monitor error: {e}")


async def backup_sync_task():
    """Periodic backup synchronization"""
    while True:
        try:
            await asyncio.sleep(300)  # Sync every 5 minutes
            await backup_manager.sync_with_backups()
            
        except Exception as e:
            logger.error(f"Backup sync error: {e}")


async def fork_detection_task():
    """Periodic fork detection"""
    while True:
        try:
            await asyncio.sleep(120)  # Check every 2 minutes
            forks = await fork_detector.detect_forks()
            if forks:
                logger.warning(f"Detected {len(forks)} potential forks")
                for fork in forks:
                    await fork_detector.resolve_fork(fork)
                    
        except Exception as e:
            logger.error(f"Fork detection error: {e}")


def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """Run the network coordinator server"""
    uvicorn.run(
        "src.network_coordinator.server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    run_server(debug=True)
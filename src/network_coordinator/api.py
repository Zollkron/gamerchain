#!/usr/bin/env python3
"""
Network Coordinator API

Fixed version that properly handles node registration, keepalive, and genesis detection
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from datetime import datetime, timedelta
import json

from .database import get_db, engine
from .models import Base, NetworkNode, NodeType, NodeStatus
from .encryption import NetworkEncryption
from .utils import calculate_distance, validate_user_agent

# Create tables
Base.metadata.create_all(bind=engine)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PlayerGold Network Coordinator", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Encryption handler
encryption = NetworkEncryption()


class NodeRegistration(BaseModel):
    """Node registration request model"""
    node_id: str = Field(..., min_length=1, max_length=255)
    public_ip: str = Field(..., min_length=7, max_length=45)
    port: int = Field(..., ge=1, le=65535)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    os_info: Optional[str] = Field(None, max_length=255)
    node_type: str = Field(default="genesis", max_length=50)
    public_key: Optional[str] = None
    signature: Optional[str] = None


class KeepaliveRequest(BaseModel):
    """Keepalive request model"""
    node_id: str = Field(..., min_length=1, max_length=255)
    blockchain_height: Optional[int] = Field(default=0, ge=0)
    connected_peers: Optional[int] = Field(default=0, ge=0)
    cpu_usage: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)
    memory_usage: Optional[float] = Field(default=0.0, ge=0.0, le=100.0)
    network_latency: Optional[float] = Field(default=0.0, ge=0.0)
    ai_model_loaded: Optional[bool] = Field(default=False)
    mining_active: Optional[bool] = Field(default=False)
    signature: Optional[str] = None


class NetworkMapRequest(BaseModel):
    """Network map request model"""
    requester_latitude: float = Field(..., ge=-90, le=90)
    requester_longitude: float = Field(..., ge=-180, le=180)
    max_distance_km: Optional[float] = Field(default=1000, ge=0, le=20000)
    limit: Optional[int] = Field(default=50, ge=1, le=1000)


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "PlayerGold Network Coordinator"
    }


@app.post("/api/v1/register")
async def register_node(
    registration: NodeRegistration,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new node in the network
    FIXED: Properly saves nodes to database and handles genesis type
    """
    try:
        # Validate User-Agent
        if not validate_user_agent(request.headers.get("user-agent", "")):
            raise HTTPException(status_code=403, detail="Invalid User-Agent")
        
        logger.info(f"🔍 REGISTRATION REQUEST: {registration.node_id}")
        logger.info(f"   Node type: {registration.node_type}")
        logger.info(f"   IP: {registration.public_ip}:{registration.port}")
        
        # Check if node already exists
        existing_node = db.query(NetworkNode).filter(
            NetworkNode.node_id == registration.node_id
        ).first()
        
        if existing_node:
            logger.info(f"📝 Updating existing node: {registration.node_id}")
            
            # Update existing node
            existing_node.public_ip = registration.public_ip
            existing_node.port = registration.port
            existing_node.latitude = registration.latitude
            existing_node.longitude = registration.longitude
            existing_node.os_info = registration.os_info
            
            # FIXED: Properly handle node_type update
            node_type_str = registration.node_type.lower()
            if node_type_str == 'genesis':
                existing_node.node_type = NodeType.GENESIS
                existing_node.is_genesis = True
            elif node_type_str == 'validator':
                existing_node.node_type = NodeType.VALIDATOR
                existing_node.is_genesis = False
            elif node_type_str == 'miner':
                existing_node.node_type = NodeType.MINER
                existing_node.is_genesis = False
            elif node_type_str == 'relay':
                existing_node.node_type = NodeType.RELAY
                existing_node.is_genesis = False
            elif node_type_str == 'light':
                existing_node.node_type = NodeType.LIGHT
                existing_node.is_genesis = False
            else:
                # Default to genesis
                existing_node.node_type = NodeType.GENESIS
                existing_node.is_genesis = True
            
            existing_node.public_key = registration.public_key
            existing_node.signature = registration.signature
            existing_node.status = NodeStatus.ACTIVE
            existing_node.updated_at = func.now()
            
            node = existing_node
        else:
            logger.info(f"🆕 Creating new node: {registration.node_id}")
            
            # FIXED: Use the corrected from_registration_data method
            node = NetworkNode.from_registration_data(registration.dict())
            db.add(node)
        
        # FIXED: Commit the transaction to ensure data is saved
        try:
            db.commit()
            logger.info(f"✅ Node {registration.node_id} saved to database successfully")
            logger.info(f"   Type: {node.node_type.value}")
            logger.info(f"   Is Genesis: {node.is_genesis}")
        except Exception as commit_error:
            logger.error(f"❌ Database commit failed: {commit_error}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(commit_error)}")
        
        # Verify the node was saved by querying it back
        verification_node = db.query(NetworkNode).filter(
            NetworkNode.node_id == registration.node_id
        ).first()
        
        if verification_node:
            logger.info(f"🔍 Verification: Node {registration.node_id} found in database")
            logger.info(f"   Database ID: {verification_node.id}")
            logger.info(f"   Type: {verification_node.node_type.value}")
            logger.info(f"   Is Genesis: {verification_node.is_genesis}")
        else:
            logger.error(f"❌ Verification failed: Node {registration.node_id} NOT found in database")
            raise HTTPException(status_code=500, detail="Node registration verification failed")
        
        return {
            "status": "success",
            "message": "Node registered successfully",
            "node_id": registration.node_id,
            "node_type": node.node_type.value,
            "is_genesis": node.is_genesis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error for {registration.node_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/api/v1/keepalive")
async def keepalive(
    keepalive_data: KeepaliveRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Process keepalive from a node
    FIXED: Properly finds nodes in database
    """
    try:
        # Validate User-Agent
        if not validate_user_agent(request.headers.get("user-agent", "")):
            raise HTTPException(status_code=403, detail="Invalid User-Agent")
        
        logger.debug(f"💓 KEEPALIVE REQUEST: {keepalive_data.node_id}")
        
        # FIXED: Find the node in database
        node = db.query(NetworkNode).filter(
            NetworkNode.node_id == keepalive_data.node_id
        ).first()
        
        if not node:
            logger.warning(f"❌ Keepalive failed: Node {keepalive_data.node_id} not found in database")
            
            # Debug: List all nodes in database
            all_nodes = db.query(NetworkNode).all()
            logger.warning(f"🔍 Database contains {len(all_nodes)} nodes:")
            for db_node in all_nodes:
                logger.warning(f"   - {db_node.node_id} (ID: {db_node.id})")
            
            raise HTTPException(status_code=404, detail="Node not found")
        
        logger.debug(f"✅ Node found: {node.node_id} (ID: {node.id})")
        
        # Update keepalive data
        node.update_keepalive(keepalive_data.dict())
        node.last_seen = func.now()
        
        # FIXED: Commit the keepalive update
        try:
            db.commit()
            logger.debug(f"✅ Keepalive updated for {keepalive_data.node_id}")
        except Exception as commit_error:
            logger.error(f"❌ Keepalive commit failed: {commit_error}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Keepalive update failed: {str(commit_error)}")
        
        return {
            "status": "success",
            "message": "Keepalive processed",
            "node_id": keepalive_data.node_id,
            "last_seen": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Keepalive error for {keepalive_data.node_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Keepalive failed: {str(e)}")


@app.post("/api/v1/network-map")
async def get_network_map(
    map_request: NetworkMapRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get encrypted network map with proper genesis node counting
    FIXED: Correctly counts and includes genesis nodes
    """
    try:
        # Validate User-Agent
        if not validate_user_agent(request.headers.get("user-agent", "")):
            raise HTTPException(status_code=403, detail="Invalid User-Agent")
        
        logger.info(f"🗺️ NETWORK MAP REQUEST")
        logger.info(f"   Location: {map_request.requester_latitude}, {map_request.requester_longitude}")
        logger.info(f"   Max distance: {map_request.max_distance_km} km")
        logger.info(f"   Limit: {map_request.limit}")
        
        # Get active nodes within distance
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)  # 5 minute timeout
        
        active_nodes = db.query(NetworkNode).filter(
            and_(
                NetworkNode.status == NodeStatus.ACTIVE,
                NetworkNode.last_seen >= cutoff_time
            )
        ).limit(map_request.limit).all()
        
        logger.info(f"📊 Found {len(active_nodes)} active nodes in database")
        
        # FIXED: Properly count genesis nodes
        genesis_nodes = [node for node in active_nodes if node.is_genesis]
        genesis_count = len(genesis_nodes)
        
        logger.info(f"🎯 Genesis nodes found: {genesis_count}")
        for genesis_node in genesis_nodes:
            logger.info(f"   - {genesis_node.node_id} (Type: {genesis_node.node_type.value})")
        
        # Filter by distance if coordinates are available
        filtered_nodes = []
        for node in active_nodes:
            if node.latitude is not None and node.longitude is not None:
                distance = calculate_distance(
                    map_request.requester_latitude,
                    map_request.requester_longitude,
                    node.latitude,
                    node.longitude
                )
                if distance <= map_request.max_distance_km:
                    filtered_nodes.append(node)
            else:
                # Include nodes without coordinates
                filtered_nodes.append(node)
        
        logger.info(f"📍 Nodes within distance: {len(filtered_nodes)}")
        
        # Convert to dict format
        nodes_data = [node.to_dict() for node in filtered_nodes]
        
        # Create network map
        network_map = {
            "total_nodes": len(filtered_nodes),
            "active_nodes": len(filtered_nodes),
            "genesis_nodes": genesis_count,  # FIXED: Correct genesis count
            "nodes": nodes_data,
            "timestamp": datetime.utcnow().isoformat(),
            "requester_location": {
                "latitude": map_request.requester_latitude,
                "longitude": map_request.requester_longitude
            }
        }
        
        logger.info(f"📋 Network map summary:")
        logger.info(f"   Total nodes: {network_map['total_nodes']}")
        logger.info(f"   Active nodes: {network_map['active_nodes']}")
        logger.info(f"   Genesis nodes: {network_map['genesis_nodes']}")
        
        # Encrypt the network map
        encrypted_map = encryption.encrypt_node_list(filtered_nodes)
        
        return {
            "status": "success",
            "message": "Network map generated",
            "map": encrypted_map
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Network map error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Network map generation failed: {str(e)}")


@app.get("/api/v1/nodes/stats")
async def get_node_stats(db: Session = Depends(get_db)):
    """Get network statistics"""
    try:
        total_nodes = db.query(NetworkNode).count()
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        active_nodes = db.query(NetworkNode).filter(
            and_(
                NetworkNode.status == NodeStatus.ACTIVE,
                NetworkNode.last_seen >= cutoff_time
            )
        ).count()
        
        # FIXED: Properly count genesis nodes
        genesis_nodes = db.query(NetworkNode).filter(
            and_(
                NetworkNode.is_genesis == True,
                NetworkNode.status == NodeStatus.ACTIVE,
                NetworkNode.last_seen >= cutoff_time
            )
        ).count()
        
        return {
            "total_nodes": total_nodes,
            "active_nodes": active_nodes,
            "genesis_nodes": genesis_nodes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
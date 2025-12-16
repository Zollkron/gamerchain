#!/usr/bin/env python3
"""
Network Coordinator Utilities

Helper functions for the network coordinator
"""

import math
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    Returns distance in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return c * r


def validate_user_agent(user_agent: Optional[str]) -> bool:
    """
    Validate User-Agent header for PlayerGold wallet access
    """
    if not user_agent:
        return False
    
    # Check for PlayerGold wallet User-Agent
    valid_patterns = [
        r"PlayerGold-Wallet/\d+\.\d+\.\d+",
        r"PlayerGold-Wallet/\d+\.\d+\.\d+ \(Electron\)",
        r"PlayerGold-Node/\d+\.\d+\.\d+",
    ]
    
    for pattern in valid_patterns:
        if re.search(pattern, user_agent):
            return True
    
    logger.warning(f"Invalid User-Agent: {user_agent}")
    return False


def validate_node_id(node_id: str) -> bool:
    """
    Validate node ID format
    """
    if not node_id or len(node_id) < 1 or len(node_id) > 255:
        return False
    
    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', node_id):
        return False
    
    return True


def validate_ip_address(ip: str) -> bool:
    """
    Validate IP address (IPv4 or IPv6)
    """
    import ipaddress
    
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_port(port: int) -> bool:
    """
    Validate port number
    """
    return 1 <= port <= 65535


def validate_coordinates(latitude: Optional[float], longitude: Optional[float]) -> bool:
    """
    Validate latitude and longitude coordinates
    """
    if latitude is None or longitude is None:
        return True  # Optional coordinates
    
    if not (-90 <= latitude <= 90):
        return False
    
    if not (-180 <= longitude <= 180):
        return False
    
    return True


def sanitize_string(value: str, max_length: int = 255) -> str:
    """
    Sanitize string input
    """
    if not value:
        return ""
    
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(value))
    return sanitized[:max_length]


def format_node_address(ip: str, port: int) -> str:
    """
    Format node address as ip:port
    """
    return f"{ip}:{port}"


def parse_node_address(address: str) -> tuple:
    """
    Parse node address into (ip, port)
    Returns (None, None) if invalid
    """
    try:
        if ':' not in address:
            return None, None
        
        ip, port_str = address.rsplit(':', 1)
        port = int(port_str)
        
        if not validate_ip_address(ip) or not validate_port(port):
            return None, None
        
        return ip, port
    except (ValueError, TypeError):
        return None, None


def get_node_type_display(node_type: str) -> str:
    """
    Get display name for node type
    """
    type_map = {
        'genesis': 'Genesis Node',
        'validator': 'Validator Node',
        'miner': 'Mining Node',
        'relay': 'Relay Node',
        'light': 'Light Node'
    }
    
    return type_map.get(node_type.lower(), 'Unknown Node')


def is_genesis_node(node_type: str) -> bool:
    """
    Check if node type is genesis
    """
    return node_type.lower() == 'genesis'


def calculate_network_health(total_nodes: int, active_nodes: int, genesis_nodes: int) -> dict:
    """
    Calculate network health metrics
    """
    if total_nodes == 0:
        return {
            'health_score': 0.0,
            'status': 'offline',
            'active_percentage': 0.0,
            'genesis_percentage': 0.0
        }
    
    active_percentage = (active_nodes / total_nodes) * 100
    genesis_percentage = (genesis_nodes / total_nodes) * 100 if total_nodes > 0 else 0
    
    # Calculate health score (0-100)
    health_score = 0.0
    
    # Active nodes contribute 60% to health
    health_score += (active_percentage * 0.6)
    
    # Genesis nodes contribute 30% to health
    health_score += (genesis_percentage * 0.3)
    
    # Network diversity contributes 10% to health
    if active_nodes > 1:
        health_score += 10.0
    
    # Determine status
    if health_score >= 80:
        status = 'excellent'
    elif health_score >= 60:
        status = 'good'
    elif health_score >= 40:
        status = 'fair'
    elif health_score >= 20:
        status = 'poor'
    else:
        status = 'critical'
    
    return {
        'health_score': round(health_score, 2),
        'status': status,
        'active_percentage': round(active_percentage, 2),
        'genesis_percentage': round(genesis_percentage, 2)
    }
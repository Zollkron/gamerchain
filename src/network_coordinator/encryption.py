"""
Encryption and cryptographic utilities for Network Coordinator
"""

import os
import hashlib
import hmac
from typing import Tuple, List
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import base64

from .models import NetworkNode, EncryptedNetworkMap


class NetworkEncryption:
    """Handles encryption and decryption of network data"""
    
    def __init__(self, master_key: bytes = None):
        """Initialize with master key for encryption"""
        if master_key is None:
            # Generate a random master key (in production, this should be from secure storage)
            master_key = os.urandom(32)
        self.master_key = master_key
    
    def generate_salt(self) -> bytes:
        """Generate a unique salt for encryption"""
        return os.urandom(16)
    
    def derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master key and salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self.master_key)
    
    def encrypt_data(self, data: bytes, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-256-GCM
        Returns (encrypted_data, salt)
        """
        if salt is None:
            salt = self.generate_salt()
        
        key = self.derive_key(salt)
        iv = os.urandom(12)  # GCM mode uses 12-byte IV
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Combine IV, tag, and ciphertext
        encrypted_data = iv + encryptor.tag + ciphertext
        
        return encrypted_data, salt
    
    def decrypt_data(self, encrypted_data: bytes, salt: bytes) -> bytes:
        """Decrypt data using AES-256-GCM"""
        key = self.derive_key(salt)
        
        # Extract IV, tag, and ciphertext
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext
    
    def encrypt_node_list(self, nodes: List[NetworkNode]) -> EncryptedNetworkMap:
        """Encrypt a list of network nodes"""
        from datetime import datetime
        
        # Convert nodes to JSON
        node_data = {
            'nodes': [node.to_dict() for node in nodes],
            'timestamp': datetime.utcnow().isoformat(),
            'total_count': len(nodes)
        }
        
        json_data = json.dumps(node_data, sort_keys=True).encode('utf-8')
        
        # Encrypt the data
        salt = self.generate_salt()
        encrypted_data, _ = self.encrypt_data(json_data, salt)
        
        # Create signature
        signature = self.sign_data(encrypted_data + salt)
        
        # Count node types
        active_nodes = sum(1 for node in nodes if node.status.value == 'active')
        genesis_nodes = sum(1 for node in nodes if node.is_genesis)
        
        return EncryptedNetworkMap(
            encrypted_data=encrypted_data,
            salt=salt,
            timestamp=datetime.utcnow(),
            signature=signature,
            version=1,
            total_nodes=len(nodes),
            active_nodes=active_nodes,
            genesis_nodes=genesis_nodes
        )
    
    def decrypt_node_list(self, encrypted_map: EncryptedNetworkMap) -> List[NetworkNode]:
        """Decrypt an encrypted network map"""
        # Verify signature
        if not self.verify_signature(encrypted_map.encrypted_data + encrypted_map.salt, encrypted_map.signature):
            raise ValueError("Invalid signature on encrypted network map")
        
        # Decrypt the data
        decrypted_data = self.decrypt_data(encrypted_map.encrypted_data, encrypted_map.salt)
        
        # Parse JSON
        node_data = json.loads(decrypted_data.decode('utf-8'))
        
        # Convert back to NetworkNode objects
        nodes = [NetworkNode.from_dict(node_dict) for node_dict in node_data['nodes']]
        
        return nodes
    
    def sign_data(self, data: bytes) -> bytes:
        """Sign data using HMAC-SHA256"""
        return hmac.new(self.master_key, data, hashlib.sha256).digest()
    
    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        """Verify HMAC signature"""
        expected_signature = self.sign_data(data)
        return hmac.compare_digest(expected_signature, signature)


class NodeAuthentication:
    """Handles node authentication using Ed25519 signatures"""
    
    @staticmethod
    def generate_keypair() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """Generate a new Ed25519 keypair"""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def serialize_public_key(public_key: ed25519.Ed25519PublicKey) -> str:
        """Serialize public key to base64 string"""
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return base64.b64encode(public_bytes).decode('utf-8')
    
    @staticmethod
    def deserialize_public_key(public_key_str: str) -> ed25519.Ed25519PublicKey:
        """Deserialize public key from base64 string"""
        public_bytes = base64.b64decode(public_key_str.encode('utf-8'))
        return ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
    
    @staticmethod
    def sign_message(private_key: ed25519.Ed25519PrivateKey, message: bytes) -> str:
        """Sign a message and return base64 encoded signature"""
        signature = private_key.sign(message)
        return base64.b64encode(signature).decode('utf-8')
    
    @staticmethod
    def verify_signature(public_key: ed25519.Ed25519PublicKey, message: bytes, signature_str: str) -> bool:
        """Verify a signature"""
        try:
            signature = base64.b64decode(signature_str.encode('utf-8'))
            public_key.verify(signature, message)
            return True
        except Exception:
            return False
    
    @staticmethod
    def create_node_id(public_key: ed25519.Ed25519PublicKey) -> str:
        """Create a node ID from public key hash"""
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        hash_digest = hashlib.sha256(public_bytes).hexdigest()
        return f"PG{hash_digest[:40]}"  # PlayerGold prefix + 40 chars
    
    def create_registration_signature(self, private_key: ed25519.Ed25519PrivateKey, 
                                    node_id: str, public_ip: str, port: int) -> str:
        """Create signature for node registration"""
        message = f"{node_id}:{public_ip}:{port}".encode('utf-8')
        return self.sign_message(private_key, message)
    
    def verify_registration_signature(self, public_key: ed25519.Ed25519PublicKey,
                                    node_id: str, public_ip: str, port: int, signature: str) -> bool:
        """Verify node registration signature"""
        message = f"{node_id}:{public_ip}:{port}".encode('utf-8')
        return self.verify_signature(public_key, message, signature)


def encrypt_ip_address(ip_address: str, encryption: NetworkEncryption) -> Tuple[bytes, bytes]:
    """Encrypt an IP address"""
    ip_bytes = ip_address.encode('utf-8')
    return encryption.encrypt_data(ip_bytes)


def decrypt_ip_address(encrypted_ip: bytes, salt: bytes, encryption: NetworkEncryption) -> str:
    """Decrypt an IP address"""
    ip_bytes = encryption.decrypt_data(encrypted_ip, salt)
    return ip_bytes.decode('utf-8')
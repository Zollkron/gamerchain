"""
Merkle Tree implementation for efficient transaction verification.
Used in PlayerGold blockchain for block validation.
"""

import hashlib
from typing import List, Optional


class MerkleNode:
    """Node in a Merkle tree."""
    
    def __init__(self, hash_value: str, left: Optional['MerkleNode'] = None, 
                 right: Optional['MerkleNode'] = None):
        self.hash = hash_value
        self.left = left
        self.right = right
    
    def is_leaf(self) -> bool:
        """Check if node is a leaf (no children)."""
        return self.left is None and self.right is None


class MerkleTree:
    """
    Merkle Tree for efficient verification of transaction sets.
    Provides O(log n) verification of transaction inclusion.
    """
    
    def __init__(self, transaction_hashes: List[str]):
        """
        Initialize Merkle tree from transaction hashes.
        
        Args:
            transaction_hashes: List of transaction hash strings
        """
        if not transaction_hashes:
            raise ValueError("Cannot create Merkle tree with empty transaction list")
        
        self.transaction_hashes = transaction_hashes.copy()
        self.root = self._build_tree(transaction_hashes)
    
    def _build_tree(self, hashes: List[str]) -> MerkleNode:
        """
        Build Merkle tree from list of hashes.
        
        Args:
            hashes: List of hash strings
            
        Returns:
            MerkleNode: Root node of the tree
        """
        # Create leaf nodes
        nodes = [MerkleNode(h) for h in hashes]
        
        # Build tree bottom-up
        while len(nodes) > 1:
            next_level = []
            
            # Process pairs of nodes
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]  # Duplicate if odd
                
                # Calculate parent hash
                combined = left.hash + right.hash
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                parent = MerkleNode(parent_hash, left, right)
                
                next_level.append(parent)
            
            nodes = next_level
        
        return nodes[0]
    
    def get_root_hash(self) -> str:
        """
        Get the root hash of the Merkle tree.
        
        Returns:
            str: Root hash as hexadecimal string
        """
        return self.root.hash
    
    def get_proof(self, transaction_hash: str) -> List[str]:
        """
        Generate Merkle proof for a transaction.
        
        Args:
            transaction_hash: Hash of transaction to prove
            
        Returns:
            List[str]: List of hashes forming the proof path
            
        Raises:
            ValueError: If transaction hash not found in tree
        """
        try:
            index = self.transaction_hashes.index(transaction_hash)
        except ValueError:
            raise ValueError(f"Transaction hash {transaction_hash} not found in tree")
        
        return self._get_proof_path(index, len(self.transaction_hashes))
    
    def _get_proof_path(self, index: int, total_count: int) -> List[str]:
        """
        Generate proof path for transaction at given index.
        
        Args:
            index: Index of transaction in original list
            total_count: Total number of transactions
            
        Returns:
            List[str]: Proof path hashes
        """
        proof = []
        current_hashes = self.transaction_hashes.copy()
        
        while len(current_hashes) > 1:
            next_level = []
            
            # Find sibling hash for current index
            if index % 2 == 0:
                # Left node, sibling is right
                sibling_index = index + 1
                if sibling_index < len(current_hashes):
                    proof.append(current_hashes[sibling_index])
                else:
                    proof.append(current_hashes[index])  # Duplicate for odd count
            else:
                # Right node, sibling is left
                sibling_index = index - 1
                proof.append(current_hashes[sibling_index])
            
            # Build next level
            for i in range(0, len(current_hashes), 2):
                left = current_hashes[i]
                right = current_hashes[i + 1] if i + 1 < len(current_hashes) else current_hashes[i]
                
                combined = left + right
                parent_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(parent_hash)
            
            current_hashes = next_level
            index = index // 2
        
        return proof
    
    @staticmethod
    def verify_proof(transaction_hash: str, proof: List[str], root_hash: str, 
                     index: int, total_count: int) -> bool:
        """
        Verify a Merkle proof for a transaction.
        
        Args:
            transaction_hash: Hash of transaction to verify
            proof: Merkle proof path
            root_hash: Expected root hash
            index: Original index of transaction
            total_count: Total number of transactions in tree
            
        Returns:
            bool: True if proof is valid
        """
        current_hash = transaction_hash
        current_index = index
        
        for sibling_hash in proof:
            if current_index % 2 == 0:
                # Current is left, sibling is right
                combined = current_hash + sibling_hash
            else:
                # Current is right, sibling is left
                combined = sibling_hash + current_hash
            
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
            current_index = current_index // 2
        
        return current_hash == root_hash
    
    def verify_transaction(self, transaction_hash: str) -> bool:
        """
        Verify that a transaction is included in this tree.
        
        Args:
            transaction_hash: Hash of transaction to verify
            
        Returns:
            bool: True if transaction is in the tree
        """
        try:
            proof = self.get_proof(transaction_hash)
            index = self.transaction_hashes.index(transaction_hash)
            return self.verify_proof(
                transaction_hash, proof, self.root.hash, 
                index, len(self.transaction_hashes)
            )
        except ValueError:
            return False
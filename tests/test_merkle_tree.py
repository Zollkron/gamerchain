"""
Tests for Merkle Tree implementation.
"""

import pytest
import hashlib
from src.blockchain.merkle_tree import MerkleTree, MerkleNode


class TestMerkleNode:
    """Test cases for MerkleNode class."""
    
    def test_node_creation(self):
        """Test basic node creation."""
        node = MerkleNode("test_hash")
        assert node.hash == "test_hash"
        assert node.left is None
        assert node.right is None
        assert node.is_leaf() is True
    
    def test_node_with_children(self):
        """Test node with children."""
        left = MerkleNode("left_hash")
        right = MerkleNode("right_hash")
        parent = MerkleNode("parent_hash", left, right)
        
        assert parent.hash == "parent_hash"
        assert parent.left == left
        assert parent.right == right
        assert parent.is_leaf() is False


class TestMerkleTree:
    """Test cases for MerkleTree class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_hashes = [
            "hash1",
            "hash2", 
            "hash3",
            "hash4"
        ]
    
    def test_tree_creation_empty_list(self):
        """Test tree creation with empty hash list."""
        with pytest.raises(ValueError):
            MerkleTree([])
    
    def test_tree_creation_single_hash(self):
        """Test tree creation with single hash."""
        tree = MerkleTree(["single_hash"])
        assert tree.get_root_hash() == "single_hash"
    
    def test_tree_creation_two_hashes(self):
        """Test tree creation with two hashes."""
        hashes = ["hash1", "hash2"]
        tree = MerkleTree(hashes)
        
        # Root should be hash of combined hashes
        expected_root = hashlib.sha256("hash1hash2".encode()).hexdigest()
        assert tree.get_root_hash() == expected_root
    
    def test_tree_creation_four_hashes(self):
        """Test tree creation with four hashes (perfect binary tree)."""
        tree = MerkleTree(self.sample_hashes)
        
        # Manually calculate expected root
        # Level 1: hash1+hash2, hash3+hash4
        left_parent = hashlib.sha256("hash1hash2".encode()).hexdigest()
        right_parent = hashlib.sha256("hash3hash4".encode()).hexdigest()
        
        # Level 2: combine parents
        expected_root = hashlib.sha256((left_parent + right_parent).encode()).hexdigest()
        
        assert tree.get_root_hash() == expected_root
    
    def test_tree_creation_odd_number(self):
        """Test tree creation with odd number of hashes."""
        hashes = ["hash1", "hash2", "hash3"]
        tree = MerkleTree(hashes)
        
        # Should handle odd number by duplicating last hash
        # Level 1: hash1+hash2, hash3+hash3
        left_parent = hashlib.sha256("hash1hash2".encode()).hexdigest()
        right_parent = hashlib.sha256("hash3hash3".encode()).hexdigest()
        
        # Level 2: combine parents
        expected_root = hashlib.sha256((left_parent + right_parent).encode()).hexdigest()
        
        assert tree.get_root_hash() == expected_root
    
    def test_get_proof_valid_hash(self):
        """Test getting proof for valid transaction hash."""
        tree = MerkleTree(self.sample_hashes)
        
        # Get proof for first hash
        proof = tree.get_proof("hash1")
        assert isinstance(proof, list)
        assert len(proof) > 0
    
    def test_get_proof_invalid_hash(self):
        """Test getting proof for invalid transaction hash."""
        tree = MerkleTree(self.sample_hashes)
        
        with pytest.raises(ValueError):
            tree.get_proof("nonexistent_hash")
    
    def test_verify_proof_valid(self):
        """Test verifying valid Merkle proof."""
        tree = MerkleTree(self.sample_hashes)
        
        # Get proof for hash1
        proof = tree.get_proof("hash1")
        root_hash = tree.get_root_hash()
        
        # Verify proof
        is_valid = MerkleTree.verify_proof(
            "hash1", proof, root_hash, 0, len(self.sample_hashes)
        )
        assert is_valid is True
    
    def test_verify_proof_invalid(self):
        """Test verifying invalid Merkle proof."""
        tree = MerkleTree(self.sample_hashes)
        
        # Get proof for hash1 but verify with wrong hash
        proof = tree.get_proof("hash1")
        root_hash = tree.get_root_hash()
        
        # Verify with wrong transaction hash
        is_valid = MerkleTree.verify_proof(
            "wrong_hash", proof, root_hash, 0, len(self.sample_hashes)
        )
        assert is_valid is False
        
        # Verify with wrong root hash
        is_valid = MerkleTree.verify_proof(
            "hash1", proof, "wrong_root", 0, len(self.sample_hashes)
        )
        assert is_valid is False
    
    def test_verify_transaction_included(self):
        """Test verifying transaction is included in tree."""
        tree = MerkleTree(self.sample_hashes)
        
        # All original hashes should be verifiable
        for hash_val in self.sample_hashes:
            assert tree.verify_transaction(hash_val) is True
        
        # Non-existent hash should not be verifiable
        assert tree.verify_transaction("nonexistent") is False
    
    def test_proof_verification_all_positions(self):
        """Test proof verification for all positions in tree."""
        tree = MerkleTree(self.sample_hashes)
        root_hash = tree.get_root_hash()
        
        # Verify proof for each transaction
        for i, hash_val in enumerate(self.sample_hashes):
            proof = tree.get_proof(hash_val)
            is_valid = MerkleTree.verify_proof(
                hash_val, proof, root_hash, i, len(self.sample_hashes)
            )
            assert is_valid is True
    
    def test_tree_with_large_dataset(self):
        """Test tree creation and verification with larger dataset."""
        # Create 16 hashes
        large_hashes = [f"hash_{i}" for i in range(16)]
        tree = MerkleTree(large_hashes)
        
        # Verify all transactions
        for hash_val in large_hashes:
            assert tree.verify_transaction(hash_val) is True
        
        # Verify root hash is calculated correctly
        root_hash = tree.get_root_hash()
        assert len(root_hash) == 64  # SHA-256 hex length
    
    def test_tree_deterministic(self):
        """Test that tree construction is deterministic."""
        tree1 = MerkleTree(self.sample_hashes)
        tree2 = MerkleTree(self.sample_hashes)
        
        # Same input should produce same root
        assert tree1.get_root_hash() == tree2.get_root_hash()
        
        # Proofs should be identical
        for hash_val in self.sample_hashes:
            proof1 = tree1.get_proof(hash_val)
            proof2 = tree2.get_proof(hash_val)
            assert proof1 == proof2
    
    def test_tree_different_order(self):
        """Test that different hash order produces different tree."""
        hashes1 = ["hash1", "hash2", "hash3", "hash4"]
        hashes2 = ["hash2", "hash1", "hash3", "hash4"]  # Swapped first two
        
        tree1 = MerkleTree(hashes1)
        tree2 = MerkleTree(hashes2)
        
        # Different order should produce different root
        assert tree1.get_root_hash() != tree2.get_root_hash()


class TestMerkleTreeEdgeCases:
    """Test edge cases for Merkle Tree."""
    
    def test_single_transaction(self):
        """Test tree with single transaction."""
        tree = MerkleTree(["single_tx"])
        
        assert tree.get_root_hash() == "single_tx"
        
        proof = tree.get_proof("single_tx")
        assert len(proof) == 0  # No siblings for single node
        
        # Verification should still work
        is_valid = MerkleTree.verify_proof(
            "single_tx", proof, "single_tx", 0, 1
        )
        assert is_valid is True
    
    def test_very_large_tree(self):
        """Test tree with many transactions."""
        # Create 1000 hashes
        many_hashes = [f"tx_hash_{i}" for i in range(1000)]
        tree = MerkleTree(many_hashes)
        
        # Should be able to create tree
        root_hash = tree.get_root_hash()
        assert len(root_hash) == 64
        
        # Verify random transactions
        test_indices = [0, 100, 500, 999]
        for i in test_indices:
            hash_val = many_hashes[i]
            assert tree.verify_transaction(hash_val) is True
    
    def test_duplicate_hashes(self):
        """Test tree with duplicate transaction hashes."""
        hashes_with_duplicates = ["hash1", "hash2", "hash1", "hash3"]
        tree = MerkleTree(hashes_with_duplicates)
        
        # Should handle duplicates (though not recommended in practice)
        root_hash = tree.get_root_hash()
        assert len(root_hash) == 64
        
        # Both instances of hash1 should be verifiable
        assert tree.verify_transaction("hash1") is True
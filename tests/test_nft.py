"""
Tests para el sistema de NFTs de juego
"""

import pytest
from decimal import Decimal
import time

from src.blockchain.nft import (
    NFT, NFTMetadata, NFTRoyalty, NFTRegistry, NFTMarketplace
)


@pytest.fixture
def sample_metadata():
    """Crea metadatos de ejemplo"""
    return NFTMetadata(
        name="Legendary Sword",
        description="A powerful sword forged in dragon fire",
        image_url="https://example.com/sword.png",
        game_id="game_001",
        item_type="weapon",
        rarity="legendary",
        level=50,
        attributes={
            "attack": 100,
            "durability": 95,
            "element": "fire"
        },
        creator="creator_address"
    )


@pytest.fixture
def nft_registry():
    """Crea un registro de NFTs"""
    return NFTRegistry()


@pytest.fixture
def marketplace(nft_registry):
    """Crea un marketplace"""
    return NFTMarketplace(nft_registry)


class TestNFTMetadata:
    """Tests para metadatos de NFT"""
    
    def test_create_metadata(self, sample_metadata):
        """Test: Crear metadatos"""
        assert sample_metadata.name == "Legendary Sword"
        assert sample_metadata.game_id == "game_001"
        assert sample_metadata.rarity == "legendary"
        assert sample_metadata.attributes["attack"] == 100
    
    def test_metadata_to_dict(self, sample_metadata):
        """Test: Convertir metadatos a diccionario"""
        data = sample_metadata.to_dict()
        
        assert data["name"] == "Legendary Sword"
        assert data["attributes"]["attack"] == 100
    
    def test_metadata_from_dict(self, sample_metadata):
        """Test: Crear metadatos desde diccionario"""
        data = sample_metadata.to_dict()
        restored = NFTMetadata.from_dict(data)
        
        assert restored.name == sample_metadata.name
        assert restored.attributes == sample_metadata.attributes


class TestNFTRoyalty:
    """Tests para royalties de NFT"""
    
    def test_create_royalty(self):
        """Test: Crear configuración de royalty"""
        royalty = NFTRoyalty(
            creator_address="creator_123",
            royalty_percentage=Decimal('5.0')
        )
        
        assert royalty.creator_address == "creator_123"
        assert royalty.royalty_percentage == Decimal('5.0')
    
    def test_calculate_royalty(self):
        """Test: Calcular monto de royalty"""
        royalty = NFTRoyalty(
            creator_address="creator_123",
            royalty_percentage=Decimal('5.0')
        )
        
        sale_price = Decimal('100.0')
        royalty_amount = royalty.calculate_royalty(sale_price)
        
        assert royalty_amount == Decimal('5.0')
    
    def test_royalty_to_dict(self):
        """Test: Convertir royalty a diccionario"""
        royalty = NFTRoyalty(
            creator_address="creator_123",
            royalty_percentage=Decimal('10.0')
        )
        
        data = royalty.to_dict()
        
        assert data["creator_address"] == "creator_123"
        assert data["royalty_percentage"] == 10.0


class TestNFT:
    """Tests para NFT"""
    
    def test_create_nft(self, sample_metadata):
        """Test: Crear NFT"""
        royalty = NFTRoyalty("creator_123", Decimal('5.0'))
        nft = NFT("NFT-001", "owner_123", sample_metadata, royalty)
        
        assert nft.token_id == "NFT-001"
        assert nft.owner == "owner_123"
        assert nft.metadata.name == "Legendary Sword"
        assert nft.royalty.creator_address == "creator_123"
    
    def test_transfer_nft(self, sample_metadata):
        """Test: Transferir NFT"""
        nft = NFT("NFT-001", "owner_123", sample_metadata)
        
        transfer_data = nft.transfer("new_owner_456")
        
        assert nft.owner == "new_owner_456"
        assert transfer_data["from"] == "owner_123"
        assert transfer_data["to"] == "new_owner_456"
        assert len(nft.transfer_history) == 1
    
    def test_transfer_with_royalty(self, sample_metadata):
        """Test: Transferir NFT con royalty"""
        royalty = NFTRoyalty("creator_123", Decimal('5.0'))
        nft = NFT("NFT-001", "owner_123", sample_metadata, royalty)
        
        sale_price = Decimal('100.0')
        transfer_data = nft.transfer("new_owner_456", sale_price)
        
        assert transfer_data["price"] == 100.0
        assert transfer_data["royalty_paid"]["amount"] == 5.0
        assert transfer_data["royalty_paid"]["recipient"] == "creator_123"
    
    def test_update_metadata(self, sample_metadata):
        """Test: Actualizar metadatos del NFT"""
        nft = NFT("NFT-001", "owner_123", sample_metadata)
        
        nft.update_metadata({"attack": 120, "new_stat": "value"})
        
        assert nft.metadata.attributes["attack"] == 120
        assert nft.metadata.attributes["new_stat"] == "value"
    
    def test_nft_hash(self, sample_metadata):
        """Test: Calcular hash del NFT"""
        nft = NFT("NFT-001", "owner_123", sample_metadata)
        
        hash1 = nft.calculate_hash()
        assert len(hash1) == 64  # SHA-256
        
        # Hash debe cambiar si cambia el owner
        nft.owner = "new_owner"
        hash2 = nft.calculate_hash()
        assert hash1 != hash2
    
    def test_nft_to_dict(self, sample_metadata):
        """Test: Convertir NFT a diccionario"""
        royalty = NFTRoyalty("creator_123", Decimal('5.0'))
        nft = NFT("NFT-001", "owner_123", sample_metadata, royalty)
        
        data = nft.to_dict()
        
        assert data["token_id"] == "NFT-001"
        assert data["owner"] == "owner_123"
        assert "metadata" in data
        assert "royalty" in data
        assert "hash" in data


class TestNFTRegistry:
    """Tests para registro de NFTs"""
    
    def test_mint_nft(self, nft_registry, sample_metadata):
        """Test: Mintear nuevo NFT"""
        nft = nft_registry.mint_nft(
            owner="owner_123",
            metadata=sample_metadata,
            royalty_percentage=Decimal('5.0')
        )
        
        assert nft.token_id == "NFT-00000001"
        assert nft.owner == "owner_123"
        assert nft.royalty.royalty_percentage == Decimal('5.0')
        assert nft.token_id in nft_registry.nfts
    
    def test_mint_multiple_nfts(self, nft_registry, sample_metadata):
        """Test: Mintear múltiples NFTs"""
        nft1 = nft_registry.mint_nft("owner_123", sample_metadata)
        nft2 = nft_registry.mint_nft("owner_456", sample_metadata)
        
        assert nft1.token_id == "NFT-00000001"
        assert nft2.token_id == "NFT-00000002"
        assert len(nft_registry.nfts) == 2
    
    def test_transfer_nft(self, nft_registry, sample_metadata):
        """Test: Transferir NFT en el registro"""
        nft = nft_registry.mint_nft("owner_123", sample_metadata)
        
        transfer_data = nft_registry.transfer_nft(
            token_id=nft.token_id,
            from_address="owner_123",
            to_address="owner_456",
            price=Decimal('100.0')
        )
        
        assert nft.owner == "owner_456"
        assert nft.token_id in nft_registry.owner_nfts["owner_456"]
        assert nft.token_id not in nft_registry.owner_nfts.get("owner_123", [])
    
    def test_transfer_nft_invalid_owner(self, nft_registry, sample_metadata):
        """Test: Transferir NFT con propietario inválido"""
        nft = nft_registry.mint_nft("owner_123", sample_metadata)
        
        with pytest.raises(ValueError, match="no pertenece"):
            nft_registry.transfer_nft(
                token_id=nft.token_id,
                from_address="wrong_owner",
                to_address="owner_456"
            )
    
    def test_get_nft(self, nft_registry, sample_metadata):
        """Test: Obtener NFT por ID"""
        nft = nft_registry.mint_nft("owner_123", sample_metadata)
        
        retrieved = nft_registry.get_nft(nft.token_id)
        
        assert retrieved is not None
        assert retrieved.token_id == nft.token_id
    
    def test_get_nfts_by_owner(self, nft_registry, sample_metadata):
        """Test: Obtener NFTs por propietario"""
        nft1 = nft_registry.mint_nft("owner_123", sample_metadata)
        nft2 = nft_registry.mint_nft("owner_123", sample_metadata)
        nft3 = nft_registry.mint_nft("owner_456", sample_metadata)
        
        owner_nfts = nft_registry.get_nfts_by_owner("owner_123")
        
        assert len(owner_nfts) == 2
        assert nft1 in owner_nfts
        assert nft2 in owner_nfts
        assert nft3 not in owner_nfts
    
    def test_get_nfts_by_game(self, nft_registry):
        """Test: Obtener NFTs por juego"""
        metadata1 = NFTMetadata(
            name="Item 1", description="", image_url="",
            game_id="game_001", item_type="weapon", rarity="common"
        )
        metadata2 = NFTMetadata(
            name="Item 2", description="", image_url="",
            game_id="game_002", item_type="armor", rarity="rare"
        )
        
        nft1 = nft_registry.mint_nft("owner_123", metadata1)
        nft2 = nft_registry.mint_nft("owner_456", metadata1)
        nft3 = nft_registry.mint_nft("owner_789", metadata2)
        
        game_nfts = nft_registry.get_nfts_by_game("game_001")
        
        assert len(game_nfts) == 2
        assert nft1 in game_nfts
        assert nft2 in game_nfts
        assert nft3 not in game_nfts
    
    def test_burn_nft(self, nft_registry, sample_metadata):
        """Test: Quemar NFT"""
        nft = nft_registry.mint_nft("owner_123", sample_metadata)
        token_id = nft.token_id
        
        nft_registry.burn_nft(token_id, "owner_123")
        
        assert token_id not in nft_registry.nfts
        assert token_id not in nft_registry.owner_nfts.get("owner_123", [])
    
    def test_burn_nft_invalid_owner(self, nft_registry, sample_metadata):
        """Test: Quemar NFT con propietario inválido"""
        nft = nft_registry.mint_nft("owner_123", sample_metadata)
        
        with pytest.raises(ValueError, match="no pertenece"):
            nft_registry.burn_nft(nft.token_id, "wrong_owner")
    
    def test_registry_serialization(self, nft_registry, sample_metadata):
        """Test: Serializar y deserializar registro"""
        nft1 = nft_registry.mint_nft("owner_123", sample_metadata)
        nft2 = nft_registry.mint_nft("owner_456", sample_metadata)
        
        data = nft_registry.to_dict()
        restored = NFTRegistry.from_dict(data)
        
        assert len(restored.nfts) == 2
        assert nft1.token_id in restored.nfts
        assert nft2.token_id in restored.nfts


class TestNFTMarketplace:
    """Tests para marketplace de NFTs"""
    
    def test_list_nft(self, marketplace, nft_registry, sample_metadata):
        """Test: Listar NFT para venta"""
        nft = nft_registry.mint_nft("seller_123", sample_metadata)
        
        marketplace.list_nft(
            token_id=nft.token_id,
            seller="seller_123",
            price=Decimal('100.0')
        )
        
        assert nft.token_id in marketplace.listings
        assert marketplace.listings[nft.token_id]["price"] == Decimal('100.0')
    
    def test_list_nft_invalid_owner(self, marketplace, nft_registry, sample_metadata):
        """Test: Listar NFT con propietario inválido"""
        nft = nft_registry.mint_nft("owner_123", sample_metadata)
        
        with pytest.raises(ValueError, match="no pertenece"):
            marketplace.list_nft(
                token_id=nft.token_id,
                seller="wrong_seller",
                price=Decimal('100.0')
            )
    
    def test_unlist_nft(self, marketplace, nft_registry, sample_metadata):
        """Test: Remover NFT del marketplace"""
        nft = nft_registry.mint_nft("seller_123", sample_metadata)
        marketplace.list_nft(nft.token_id, "seller_123", Decimal('100.0'))
        
        marketplace.unlist_nft(nft.token_id, "seller_123")
        
        assert nft.token_id not in marketplace.listings
    
    def test_buy_nft(self, marketplace, nft_registry, sample_metadata):
        """Test: Comprar NFT del marketplace"""
        nft = nft_registry.mint_nft("seller_123", sample_metadata)
        marketplace.list_nft(nft.token_id, "seller_123", Decimal('100.0'))
        
        purchase_data = marketplace.buy_nft(
            token_id=nft.token_id,
            buyer="buyer_456",
            buyer_balance=Decimal('200.0')
        )
        
        assert nft.owner == "buyer_456"
        assert nft.token_id not in marketplace.listings
        assert purchase_data["price"] == 100.0
        assert purchase_data["seller"] == "seller_123"
        assert purchase_data["buyer"] == "buyer_456"
    
    def test_buy_nft_with_royalty(self, marketplace, nft_registry, sample_metadata):
        """Test: Comprar NFT con royalty"""
        nft = nft_registry.mint_nft(
            owner="creator_123",
            metadata=sample_metadata,
            royalty_percentage=Decimal('10.0')
        )
        
        # Transferir a vendedor
        nft_registry.transfer_nft(nft.token_id, "creator_123", "seller_456")
        
        # Listar para venta
        marketplace.list_nft(nft.token_id, "seller_456", Decimal('100.0'))
        
        # Comprar
        purchase_data = marketplace.buy_nft(
            token_id=nft.token_id,
            buyer="buyer_789",
            buyer_balance=Decimal('200.0')
        )
        
        assert purchase_data["royalty"]["amount"] == 10.0
        assert purchase_data["royalty"]["recipient"] == "creator_123"
        assert purchase_data["seller_receives"] == 90.0
    
    def test_buy_nft_insufficient_balance(self, marketplace, nft_registry, sample_metadata):
        """Test: Comprar NFT con saldo insuficiente"""
        nft = nft_registry.mint_nft("seller_123", sample_metadata)
        marketplace.list_nft(nft.token_id, "seller_123", Decimal('100.0'))
        
        with pytest.raises(ValueError, match="Saldo insuficiente"):
            marketplace.buy_nft(
                token_id=nft.token_id,
                buyer="buyer_456",
                buyer_balance=Decimal('50.0')
            )
    
    def test_get_listings(self, marketplace, nft_registry, sample_metadata):
        """Test: Obtener listings activos"""
        nft1 = nft_registry.mint_nft("seller_123", sample_metadata)
        nft2 = nft_registry.mint_nft("seller_456", sample_metadata)
        
        marketplace.list_nft(nft1.token_id, "seller_123", Decimal('100.0'))
        marketplace.list_nft(nft2.token_id, "seller_456", Decimal('200.0'))
        
        listings = marketplace.get_listings()
        
        assert len(listings) == 2
        assert any(l["token_id"] == nft1.token_id for l in listings)
        assert any(l["token_id"] == nft2.token_id for l in listings)
    
    def test_get_listings_by_game(self, marketplace, nft_registry):
        """Test: Obtener listings filtrados por juego"""
        metadata1 = NFTMetadata(
            name="Item 1", description="", image_url="",
            game_id="game_001", item_type="weapon", rarity="common"
        )
        metadata2 = NFTMetadata(
            name="Item 2", description="", image_url="",
            game_id="game_002", item_type="armor", rarity="rare"
        )
        
        nft1 = nft_registry.mint_nft("seller_123", metadata1)
        nft2 = nft_registry.mint_nft("seller_456", metadata2)
        
        marketplace.list_nft(nft1.token_id, "seller_123", Decimal('100.0'))
        marketplace.list_nft(nft2.token_id, "seller_456", Decimal('200.0'))
        
        listings = marketplace.get_listings(game_id="game_001")
        
        assert len(listings) == 1
        assert listings[0]["token_id"] == nft1.token_id

"""
Sistema de NFTs para activos de juego
Implementa NFTs con metadatos extensibles y royalties automáticos
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from decimal import Decimal


@dataclass
class NFTMetadata:
    """Metadatos extensibles para NFTs de juego"""
    name: str
    description: str
    image_url: str
    
    # Atributos del juego
    game_id: str
    item_type: str  # weapon, armor, skin, character, etc.
    rarity: str  # common, rare, epic, legendary
    level: int = 1
    
    # Atributos personalizados
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Información del creador
    creator: str = ""
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte metadatos a diccionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NFTMetadata':
        """Crea metadatos desde diccionario"""
        return cls(**data)


@dataclass
class NFTRoyalty:
    """Configuración de royalties para NFTs"""
    creator_address: str
    royalty_percentage: Decimal  # Porcentaje (0-100)
    
    def calculate_royalty(self, sale_price: Decimal) -> Decimal:
        """Calcula el monto de royalty para una venta"""
        return (sale_price * self.royalty_percentage) / Decimal(100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte royalty a diccionario"""
        return {
            'creator_address': self.creator_address,
            'royalty_percentage': float(self.royalty_percentage)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NFTRoyalty':
        """Crea royalty desde diccionario"""
        return cls(
            creator_address=data['creator_address'],
            royalty_percentage=Decimal(str(data['royalty_percentage']))
        )


class NFT:
    """Clase que representa un NFT de juego"""
    
    def __init__(
        self,
        token_id: str,
        owner: str,
        metadata: NFTMetadata,
        royalty: Optional[NFTRoyalty] = None
    ):
        self.token_id = token_id
        self.owner = owner
        self.metadata = metadata
        self.royalty = royalty
        self.transfer_history: List[Dict[str, Any]] = []
        self.created_at = time.time()
        
    def transfer(self, new_owner: str, price: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Transfiere el NFT a un nuevo propietario
        
        Args:
            new_owner: Dirección del nuevo propietario
            price: Precio de venta (opcional, para calcular royalties)
            
        Returns:
            Información de la transferencia incluyendo royalties
        """
        transfer_data = {
            'from': self.owner,
            'to': new_owner,
            'timestamp': time.time(),
            'price': float(price) if price else None,
            'royalty_paid': None
        }
        
        # Calcular y registrar royalty si hay precio de venta
        if price and self.royalty:
            royalty_amount = self.royalty.calculate_royalty(price)
            transfer_data['royalty_paid'] = {
                'amount': float(royalty_amount),
                'recipient': self.royalty.creator_address
            }
        
        self.transfer_history.append(transfer_data)
        self.owner = new_owner
        
        return transfer_data
    
    def update_metadata(self, new_attributes: Dict[str, Any]):
        """Actualiza atributos del NFT (para items que evolucionan)"""
        self.metadata.attributes.update(new_attributes)
    
    def calculate_hash(self) -> str:
        """Calcula hash único del NFT"""
        nft_string = f"{self.token_id}{self.owner}{json.dumps(self.metadata.to_dict(), sort_keys=True)}"
        return hashlib.sha256(nft_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte NFT a diccionario"""
        return {
            'token_id': self.token_id,
            'owner': self.owner,
            'metadata': self.metadata.to_dict(),
            'royalty': self.royalty.to_dict() if self.royalty else None,
            'transfer_history': self.transfer_history,
            'created_at': self.created_at,
            'hash': self.calculate_hash()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NFT':
        """Crea NFT desde diccionario"""
        nft = cls(
            token_id=data['token_id'],
            owner=data['owner'],
            metadata=NFTMetadata.from_dict(data['metadata']),
            royalty=NFTRoyalty.from_dict(data['royalty']) if data.get('royalty') else None
        )
        nft.transfer_history = data.get('transfer_history', [])
        nft.created_at = data.get('created_at', time.time())
        return nft


class NFTRegistry:
    """Registro de NFTs en la blockchain"""
    
    def __init__(self):
        self.nfts: Dict[str, NFT] = {}
        self.owner_nfts: Dict[str, List[str]] = {}  # owner -> [token_ids]
        self.next_token_id = 1
        
    def mint_nft(
        self,
        owner: str,
        metadata: NFTMetadata,
        royalty_percentage: Decimal = Decimal('5.0')
    ) -> NFT:
        """
        Crea (mintea) un nuevo NFT
        
        Args:
            owner: Dirección del propietario inicial
            metadata: Metadatos del NFT
            royalty_percentage: Porcentaje de royalty para el creador
            
        Returns:
            NFT creado
        """
        token_id = f"NFT-{self.next_token_id:08d}"
        self.next_token_id += 1
        
        # Crear royalty para el creador
        royalty = NFTRoyalty(
            creator_address=owner,
            royalty_percentage=royalty_percentage
        )
        
        # Crear NFT
        nft = NFT(
            token_id=token_id,
            owner=owner,
            metadata=metadata,
            royalty=royalty
        )
        
        # Registrar NFT
        self.nfts[token_id] = nft
        
        if owner not in self.owner_nfts:
            self.owner_nfts[owner] = []
        self.owner_nfts[owner].append(token_id)
        
        return nft
    
    def transfer_nft(
        self,
        token_id: str,
        from_address: str,
        to_address: str,
        price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Transfiere un NFT entre direcciones
        
        Args:
            token_id: ID del NFT
            from_address: Dirección actual del propietario
            to_address: Dirección del nuevo propietario
            price: Precio de venta (opcional)
            
        Returns:
            Información de la transferencia
        """
        if token_id not in self.nfts:
            raise ValueError(f"NFT {token_id} no existe")
        
        nft = self.nfts[token_id]
        
        if nft.owner != from_address:
            raise ValueError(f"NFT {token_id} no pertenece a {from_address}")
        
        # Realizar transferencia
        transfer_data = nft.transfer(to_address, price)
        
        # Actualizar índice de propietarios
        self.owner_nfts[from_address].remove(token_id)
        if not self.owner_nfts[from_address]:
            del self.owner_nfts[from_address]
        
        if to_address not in self.owner_nfts:
            self.owner_nfts[to_address] = []
        self.owner_nfts[to_address].append(token_id)
        
        return transfer_data
    
    def get_nft(self, token_id: str) -> Optional[NFT]:
        """Obtiene un NFT por su ID"""
        return self.nfts.get(token_id)
    
    def get_nfts_by_owner(self, owner: str) -> List[NFT]:
        """Obtiene todos los NFTs de un propietario"""
        token_ids = self.owner_nfts.get(owner, [])
        return [self.nfts[token_id] for token_id in token_ids]
    
    def get_nfts_by_game(self, game_id: str) -> List[NFT]:
        """Obtiene todos los NFTs de un juego específico"""
        return [
            nft for nft in self.nfts.values()
            if nft.metadata.game_id == game_id
        ]
    
    def burn_nft(self, token_id: str, owner: str):
        """
        Quema (destruye) un NFT
        
        Args:
            token_id: ID del NFT
            owner: Dirección del propietario (para verificación)
        """
        if token_id not in self.nfts:
            raise ValueError(f"NFT {token_id} no existe")
        
        nft = self.nfts[token_id]
        
        if nft.owner != owner:
            raise ValueError(f"NFT {token_id} no pertenece a {owner}")
        
        # Eliminar NFT
        del self.nfts[token_id]
        self.owner_nfts[owner].remove(token_id)
        if not self.owner_nfts[owner]:
            del self.owner_nfts[owner]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el registro a diccionario"""
        return {
            'nfts': {token_id: nft.to_dict() for token_id, nft in self.nfts.items()},
            'next_token_id': self.next_token_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NFTRegistry':
        """Crea registro desde diccionario"""
        registry = cls()
        registry.next_token_id = data.get('next_token_id', 1)
        
        for token_id, nft_data in data.get('nfts', {}).items():
            nft = NFT.from_dict(nft_data)
            registry.nfts[token_id] = nft
            
            if nft.owner not in registry.owner_nfts:
                registry.owner_nfts[nft.owner] = []
            registry.owner_nfts[nft.owner].append(token_id)
        
        return registry


class NFTMarketplace:
    """Marketplace para trading de NFTs"""
    
    def __init__(self, nft_registry: NFTRegistry):
        self.nft_registry = nft_registry
        self.listings: Dict[str, Dict[str, Any]] = {}  # token_id -> listing_data
        
    def list_nft(
        self,
        token_id: str,
        seller: str,
        price: Decimal,
        expiration: Optional[float] = None
    ):
        """
        Lista un NFT para venta
        
        Args:
            token_id: ID del NFT
            seller: Dirección del vendedor
            price: Precio de venta
            expiration: Timestamp de expiración (opcional)
        """
        nft = self.nft_registry.get_nft(token_id)
        
        if not nft:
            raise ValueError(f"NFT {token_id} no existe")
        
        if nft.owner != seller:
            raise ValueError(f"NFT {token_id} no pertenece a {seller}")
        
        if token_id in self.listings:
            raise ValueError(f"NFT {token_id} ya está listado")
        
        self.listings[token_id] = {
            'seller': seller,
            'price': price,
            'listed_at': time.time(),
            'expiration': expiration
        }
    
    def unlist_nft(self, token_id: str, seller: str):
        """
        Remueve un NFT del marketplace
        
        Args:
            token_id: ID del NFT
            seller: Dirección del vendedor (para verificación)
        """
        if token_id not in self.listings:
            raise ValueError(f"NFT {token_id} no está listado")
        
        listing = self.listings[token_id]
        
        if listing['seller'] != seller:
            raise ValueError(f"Solo el vendedor puede remover el listing")
        
        del self.listings[token_id]
    
    def buy_nft(
        self,
        token_id: str,
        buyer: str,
        buyer_balance: Decimal
    ) -> Dict[str, Any]:
        """
        Compra un NFT del marketplace
        
        Args:
            token_id: ID del NFT
            buyer: Dirección del comprador
            buyer_balance: Saldo del comprador
            
        Returns:
            Información de la compra incluyendo distribución de fondos
        """
        if token_id not in self.listings:
            raise ValueError(f"NFT {token_id} no está listado")
        
        listing = self.listings[token_id]
        price = listing['price']
        seller = listing['seller']
        
        # Verificar expiración
        if listing['expiration'] and time.time() > listing['expiration']:
            del self.listings[token_id]
            raise ValueError(f"Listing de NFT {token_id} ha expirado")
        
        # Verificar saldo
        if buyer_balance < price:
            raise ValueError(f"Saldo insuficiente para comprar NFT {token_id}")
        
        # Obtener NFT para calcular royalty
        nft = self.nft_registry.get_nft(token_id)
        
        # Calcular distribución de fondos
        royalty_amount = Decimal('0')
        royalty_recipient = None
        
        if nft.royalty:
            royalty_amount = nft.royalty.calculate_royalty(price)
            royalty_recipient = nft.royalty.creator_address
        
        seller_amount = price - royalty_amount
        
        # Transferir NFT
        transfer_data = self.nft_registry.transfer_nft(
            token_id=token_id,
            from_address=seller,
            to_address=buyer,
            price=price
        )
        
        # Remover listing
        del self.listings[token_id]
        
        return {
            'token_id': token_id,
            'buyer': buyer,
            'seller': seller,
            'price': float(price),
            'seller_receives': float(seller_amount),
            'royalty': {
                'amount': float(royalty_amount),
                'recipient': royalty_recipient
            } if royalty_recipient else None,
            'transfer_data': transfer_data
        }
    
    def get_listings(self, game_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los listings activos
        
        Args:
            game_id: Filtrar por juego específico (opcional)
            
        Returns:
            Lista de listings con información del NFT
        """
        listings = []
        current_time = time.time()
        
        for token_id, listing in self.listings.items():
            # Verificar expiración
            if listing['expiration'] and current_time > listing['expiration']:
                continue
            
            nft = self.nft_registry.get_nft(token_id)
            
            # Filtrar por juego si se especifica
            if game_id and nft.metadata.game_id != game_id:
                continue
            
            listings.append({
                'token_id': token_id,
                'nft': nft.to_dict(),
                'price': float(listing['price']),
                'seller': listing['seller'],
                'listed_at': listing['listed_at']
            })
        
        return listings

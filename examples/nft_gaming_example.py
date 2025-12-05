"""
Ejemplo de uso del sistema de NFTs para activos de juego
Demuestra cómo crear, transferir y comerciar NFTs con royalties automáticos
"""

from decimal import Decimal

from src.blockchain.nft import (
    NFT, NFTMetadata, NFTRoyalty, NFTRegistry, NFTMarketplace
)


def print_separator(title=""):
    """Imprime un separador visual"""
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def print_nft_info(nft: NFT):
    """Imprime información de un NFT"""
    print(f"\n📦 NFT: {nft.token_id}")
    print(f"   Nombre: {nft.metadata.name}")
    print(f"   Propietario: {nft.owner}")
    print(f"   Juego: {nft.metadata.game_id}")
    print(f"   Tipo: {nft.metadata.item_type}")
    print(f"   Rareza: {nft.metadata.rarity}")
    print(f"   Nivel: {nft.metadata.level}")
    print(f"   Atributos: {nft.metadata.attributes}")
    if nft.royalty:
        print(f"   Royalty: {nft.royalty.royalty_percentage}% para {nft.royalty.creator_address}")


def example_1_create_nfts():
    """Ejemplo 1: Crear NFTs de diferentes tipos"""
    print_separator("Ejemplo 1: Crear NFTs de Juego")
    
    registry = NFTRegistry()
    
    # Crear un arma legendaria
    weapon_metadata = NFTMetadata(
        name="Dragon Slayer Sword",
        description="A legendary sword forged from dragon scales",
        image_url="https://game.com/items/dragon_sword.png",
        game_id="fantasy_rpg",
        item_type="weapon",
        rarity="legendary",
        level=75,
        attributes={
            "attack": 150,
            "critical_chance": 25,
            "durability": 100,
            "element": "fire",
            "special_ability": "Dragon's Breath"
        },
        creator="game_developer"
    )
    
    weapon_nft = registry.mint_nft(
        owner="player_001",
        metadata=weapon_metadata,
        royalty_percentage=Decimal('5.0')
    )
    
    print("\n✓ Arma legendaria creada:")
    print_nft_info(weapon_nft)
    
    # Crear una armadura épica
    armor_metadata = NFTMetadata(
        name="Celestial Plate Armor",
        description="Armor blessed by the gods",
        image_url="https://game.com/items/celestial_armor.png",
        game_id="fantasy_rpg",
        item_type="armor",
        rarity="epic",
        level=60,
        attributes={
            "defense": 120,
            "magic_resistance": 80,
            "durability": 95,
            "set_bonus": "Celestial Protection"
        },
        creator="game_developer"
    )
    
    armor_nft = registry.mint_nft(
        owner="player_002",
        metadata=armor_metadata,
        royalty_percentage=Decimal('5.0')
    )
    
    print("\n✓ Armadura épica creada:")
    print_nft_info(armor_nft)
    
    # Crear una skin de personaje
    skin_metadata = NFTMetadata(
        name="Cyberpunk Ninja Skin",
        description="Limited edition cyberpunk skin",
        image_url="https://game.com/skins/cyberpunk_ninja.png",
        game_id="battle_royale",
        item_type="skin",
        rarity="rare",
        level=1,
        attributes={
            "visual_effects": ["neon_glow", "holographic_trail"],
            "edition": "limited",
            "release_date": "2024-01-15"
        },
        creator="artist_123"
    )
    
    skin_nft = registry.mint_nft(
        owner="player_003",
        metadata=skin_metadata,
        royalty_percentage=Decimal('10.0')  # Mayor royalty para artistas
    )
    
    print("\n✓ Skin de personaje creada:")
    print_nft_info(skin_nft)
    
    return registry


def example_2_transfer_and_royalties():
    """Ejemplo 2: Transferir NFTs y calcular royalties"""
    print_separator("Ejemplo 2: Transferencias y Royalties")
    
    registry = NFTRegistry()
    
    # Crear NFT
    metadata = NFTMetadata(
        name="Rare Battle Axe",
        description="A powerful battle axe",
        image_url="https://game.com/items/battle_axe.png",
        game_id="fantasy_rpg",
        item_type="weapon",
        rarity="rare",
        level=40,
        attributes={"attack": 80, "durability": 90},
        creator="creator_wallet"
    )
    
    nft = registry.mint_nft(
        owner="creator_wallet",
        metadata=metadata,
        royalty_percentage=Decimal('7.5')
    )
    
    print("\n✓ NFT creado por el creador:")
    print_nft_info(nft)
    
    # Primera venta: Creador -> Jugador 1
    print("\n📤 Primera venta: Creador -> Jugador 1")
    sale_price_1 = Decimal('100.0')
    transfer_1 = registry.transfer_nft(
        token_id=nft.token_id,
        from_address="creator_wallet",
        to_address="player_001",
        price=sale_price_1
    )
    
    print(f"   Precio de venta: {sale_price_1} $PRGLD")
    print(f"   Royalty pagado: {transfer_1['royalty_paid']['amount']} $PRGLD")
    print(f"   Destinatario del royalty: {transfer_1['royalty_paid']['recipient']}")
    print(f"   Nuevo propietario: {nft.owner}")
    
    # Segunda venta: Jugador 1 -> Jugador 2
    print("\n📤 Segunda venta: Jugador 1 -> Jugador 2")
    sale_price_2 = Decimal('150.0')
    transfer_2 = registry.transfer_nft(
        token_id=nft.token_id,
        from_address="player_001",
        to_address="player_002",
        price=sale_price_2
    )
    
    royalty_amount = transfer_2['royalty_paid']['amount']
    seller_receives = float(sale_price_2) - royalty_amount
    
    print(f"   Precio de venta: {sale_price_2} $PRGLD")
    print(f"   Royalty al creador: {royalty_amount} $PRGLD")
    print(f"   Vendedor recibe: {seller_receives} $PRGLD")
    print(f"   Nuevo propietario: {nft.owner}")
    
    # Mostrar historial de transferencias
    print("\n📜 Historial de transferencias:")
    for i, transfer in enumerate(nft.transfer_history, 1):
        print(f"\n   Transferencia {i}:")
        print(f"   De: {transfer['from']}")
        print(f"   A: {transfer['to']}")
        print(f"   Precio: {transfer['price']} $PRGLD")
        if transfer['royalty_paid']:
            print(f"   Royalty: {transfer['royalty_paid']['amount']} $PRGLD")


def example_3_marketplace():
    """Ejemplo 3: Marketplace de NFTs"""
    print_separator("Ejemplo 3: Marketplace de NFTs")
    
    registry = NFTRegistry()
    marketplace = NFTMarketplace(registry)
    
    # Crear varios NFTs
    print("\n✓ Creando NFTs para el marketplace...")
    
    nfts = []
    for i in range(3):
        metadata = NFTMetadata(
            name=f"Epic Item #{i+1}",
            description=f"Epic item number {i+1}",
            image_url=f"https://game.com/items/epic_{i+1}.png",
            game_id="fantasy_rpg",
            item_type="weapon" if i % 2 == 0 else "armor",
            rarity="epic",
            level=50 + i * 10,
            attributes={"power": 100 + i * 20},
            creator=f"creator_{i+1}"
        )
        
        nft = registry.mint_nft(
            owner=f"seller_{i+1}",
            metadata=metadata,
            royalty_percentage=Decimal('5.0')
        )
        nfts.append(nft)
        print(f"   - {nft.metadata.name} (Owner: {nft.owner})")
    
    # Listar NFTs en el marketplace
    print("\n📋 Listando NFTs en el marketplace...")
    
    marketplace.list_nft(nfts[0].token_id, "seller_1", Decimal('100.0'))
    marketplace.list_nft(nfts[1].token_id, "seller_2", Decimal('150.0'))
    marketplace.list_nft(nfts[2].token_id, "seller_3", Decimal('200.0'))
    
    # Mostrar listings
    listings = marketplace.get_listings()
    print(f"\n   Total de listings: {len(listings)}")
    for listing in listings:
        print(f"\n   📦 {listing['nft']['metadata']['name']}")
        print(f"      Token ID: {listing['token_id']}")
        print(f"      Precio: {listing['price']} $PRGLD")
        print(f"      Vendedor: {listing['seller']}")
    
    # Comprar un NFT
    print("\n💰 Comprando NFT del marketplace...")
    
    buyer_balance = Decimal('500.0')
    purchase = marketplace.buy_nft(
        token_id=nfts[0].token_id,
        buyer="buyer_001",
        buyer_balance=buyer_balance
    )
    
    print(f"\n   ✓ Compra exitosa!")
    print(f"   NFT: {purchase['token_id']}")
    print(f"   Comprador: {purchase['buyer']}")
    print(f"   Vendedor: {purchase['seller']}")
    print(f"   Precio: {purchase['price']} $PRGLD")
    print(f"   Vendedor recibe: {purchase['seller_receives']} $PRGLD")
    if purchase['royalty']:
        print(f"   Royalty: {purchase['royalty']['amount']} $PRGLD para {purchase['royalty']['recipient']}")
    
    # Verificar que el NFT ya no está listado
    remaining_listings = marketplace.get_listings()
    print(f"\n   Listings restantes: {len(remaining_listings)}")


def example_4_nft_evolution():
    """Ejemplo 4: Evolución de NFTs (items que mejoran)"""
    print_separator("Ejemplo 4: Evolución de NFTs")
    
    registry = NFTRegistry()
    
    # Crear un item que puede evolucionar
    metadata = NFTMetadata(
        name="Apprentice Staff",
        description="A basic magical staff that grows with its wielder",
        image_url="https://game.com/items/staff_lv1.png",
        game_id="fantasy_rpg",
        item_type="weapon",
        rarity="common",
        level=1,
        attributes={
            "magic_power": 10,
            "intelligence": 5,
            "experience": 0,
            "max_experience": 100
        },
        creator="game_developer"
    )
    
    nft = registry.mint_nft(
        owner="player_001",
        metadata=metadata,
        royalty_percentage=Decimal('5.0')
    )
    
    print("\n✓ Item inicial:")
    print_nft_info(nft)
    
    # Simular evolución del item
    print("\n⚡ Jugador usa el item y gana experiencia...")
    
    # Nivel 2
    nft.update_metadata({
        "experience": 100,
        "magic_power": 25,
        "intelligence": 12
    })
    nft.metadata.level = 2
    nft.metadata.rarity = "uncommon"
    nft.metadata.name = "Adept Staff"
    nft.metadata.image_url = "https://game.com/items/staff_lv2.png"
    
    print("\n✓ Item evolucionado a Nivel 2:")
    print_nft_info(nft)
    
    # Nivel 3
    nft.update_metadata({
        "experience": 250,
        "magic_power": 50,
        "intelligence": 25,
        "special_ability": "Arcane Blast"
    })
    nft.metadata.level = 3
    nft.metadata.rarity = "rare"
    nft.metadata.name = "Master Staff"
    nft.metadata.image_url = "https://game.com/items/staff_lv3.png"
    
    print("\n✓ Item evolucionado a Nivel 3:")
    print_nft_info(nft)
    
    print("\n💡 El NFT mantiene su token_id y royalties originales,")
    print("   pero sus atributos evolucionan con el progreso del jugador.")


def example_5_cross_game_nfts():
    """Ejemplo 5: NFTs que funcionan en múltiples juegos"""
    print_separator("Ejemplo 5: NFTs Cross-Game")
    
    registry = NFTRegistry()
    
    # Crear un NFT que puede usarse en múltiples juegos
    metadata = NFTMetadata(
        name="Legendary Dragon Pet",
        description="A powerful dragon companion that travels across games",
        image_url="https://platform.com/pets/dragon.png",
        game_id="gaming_platform",  # Plataforma general
        item_type="pet",
        rarity="legendary",
        level=50,
        attributes={
            # Atributos para RPG
            "rpg_stats": {
                "attack": 100,
                "defense": 80,
                "magic": 120
            },
            # Atributos para Battle Royale
            "battle_royale_stats": {
                "damage_boost": 15,
                "health_regen": 10
            },
            # Atributos para Racing Game
            "racing_stats": {
                "speed_boost": 20,
                "handling": 15
            },
            # Metadatos generales
            "cross_game_compatible": True,
            "supported_games": ["fantasy_rpg", "battle_royale", "racing_game"]
        },
        creator="platform_developer"
    )
    
    nft = registry.mint_nft(
        owner="player_001",
        metadata=metadata,
        royalty_percentage=Decimal('10.0')
    )
    
    print("\n✓ NFT Cross-Game creado:")
    print_nft_info(nft)
    
    print("\n🎮 Este NFT puede usarse en múltiples juegos:")
    for game in nft.metadata.attributes["supported_games"]:
        print(f"   - {game}")
    
    print("\n💡 Los NFTs cross-game aumentan el valor y utilidad")
    print("   al permitir que los jugadores usen sus activos en diferentes juegos.")


def main():
    """Ejecuta todos los ejemplos"""
    print("\n" + "🎮" * 30)
    print("  Sistema de NFTs para Activos de Juego - PlayerGold")
    print("🎮" * 30)
    
    # Ejecutar ejemplos
    example_1_create_nfts()
    example_2_transfer_and_royalties()
    example_3_marketplace()
    example_4_nft_evolution()
    example_5_cross_game_nfts()
    
    print_separator("Ejemplos Completados")
    print("\n✓ Todos los ejemplos se ejecutaron exitosamente")
    print("\nCaracterísticas demostradas:")
    print("  • Creación de NFTs con metadatos extensibles")
    print("  • Royalties automáticos para creadores")
    print("  • Marketplace descentralizado")
    print("  • Evolución de items")
    print("  • NFTs cross-game")
    print("\n")


if __name__ == "__main__":
    main()

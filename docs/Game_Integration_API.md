# API de Integración con Juegos - PlayerGold

## Resumen

Este documento describe la API completa para integrar PlayerGold ($PRGLD) en juegos. La API proporciona endpoints REST y GraphQL, SDKs para motores de juegos populares, y soporte completo para NFTs gaming con royalties automáticos.

## Tabla de Contenidos

1. [API REST](#api-rest)
2. [API GraphQL](#api-graphql)
3. [SDKs para Motores de Juegos](#sdks-para-motores-de-juegos)
4. [Sistema de NFTs](#sistema-de-nfts)
5. [Autenticación y Seguridad](#autenticación-y-seguridad)
6. [Ejemplos de Integración](#ejemplos-de-integración)

---

## API REST

### URL Base
```
http://localhost:5000/api/v1
```

### Autenticación

#### Registrar Desarrollador
```http
POST /auth/register
Content-Type: application/json

{
  "email": "developer@yourgame.com",
  "game_name": "Your Awesome Game"
}
```

**Respuesta:**
```json
{
  "api_key": "your_api_key_here",
  "message": "Desarrollador registrado exitosamente"
}
```

#### Obtener Token JWT
```http
POST /auth/token
Content-Type: application/json

{
  "api_key": "your_api_key_here"
}
```

**Respuesta:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}
```

### Endpoints Públicos

#### Health Check
```http
GET /health
```

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### Estado de la Red
```http
GET /network/status
```

**Respuesta:**
```json
{
  "chain_length": 1234,
  "last_block_index": 1233,
  "last_block_hash": "0x1234...",
  "pending_transactions": 5,
  "difficulty": 4,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Endpoints Protegidos

Todos los endpoints protegidos requieren el header:
```
Authorization: Bearer <jwt_token>
```

#### Consultar Saldo
```http
GET /balance/{address}
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "address": "PRGLD1234...",
  "balance": 150.50,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Crear Transacción
```http
POST /transaction
Authorization: Bearer <token>
Content-Type: application/json

{
  "from_address": "PRGLD1234...",
  "to_address": "PRGLD5678...",
  "amount": 10.0,
  "private_key": "your_private_key",
  "fee": 0.01
}
```

**Respuesta:**
```json
{
  "transaction_hash": "0xabcd...",
  "status": "pending",
  "message": "Transacción creada exitosamente"
}
```

#### Obtener Transacción
```http
GET /transaction/{tx_hash}
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "transaction": {
    "from_address": "PRGLD1234...",
    "to_address": "PRGLD5678...",
    "amount": 10.0,
    "fee": 0.01,
    "timestamp": 1705315800.0
  },
  "block_index": 1234,
  "confirmations": 6,
  "status": "confirmed"
}
```

#### Historial de Transacciones
```http
GET /transactions/history/{address}?page=1&per_page=20
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "address": "PRGLD1234...",
  "transactions": [
    {
      "transaction": {...},
      "block_index": 1234,
      "timestamp": 1705315800.0,
      "confirmations": 6
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20
}
```

#### Obtener Bloque
```http
GET /block/{block_index}
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "block": {
    "index": 1234,
    "previous_hash": "0x1234...",
    "timestamp": 1705315800.0,
    "transactions": [...],
    "merkle_root": "0xabcd...",
    "hash": "0xefgh..."
  },
  "confirmations": 10
}
```

### Rate Limiting

- **Límite por defecto:** 100 peticiones/minuto, 1000 peticiones/hora
- **Endpoints públicos:** 30 peticiones/minuto
- **Autenticación:** 10 peticiones/minuto

---

## API GraphQL

### URL Base
```
http://localhost:5001/graphql
```

### Queries

#### Estado de la Red
```graphql
query {
  networkStatus {
    chainLength
    lastBlockIndex
    lastBlockHash
    pendingTransactions
    difficulty
    timestamp
  }
}
```

#### Consultar Saldo
```graphql
query GetBalance($address: String!) {
  balance(address: $address) {
    address
    balance
    timestamp
  }
}
```

#### Obtener Transacción
```graphql
query GetTransaction($txHash: String!) {
  transaction(txHash: $txHash) {
    fromAddress
    toAddress
    amount
    fee
    timestamp
    transactionHash
  }
}
```

#### Historial de Transacciones
```graphql
query GetHistory($address: String!, $limit: Int) {
  transactionHistory(address: $address, limit: $limit) {
    address
    transactions {
      fromAddress
      toAddress
      amount
      fee
    }
    total
  }
}
```

#### Obtener Bloque
```graphql
query GetBlock($index: Int!) {
  block(index: $index) {
    index
    previousHash
    timestamp
    transactions {
      fromAddress
      toAddress
      amount
    }
    merkleRoot
    hash
  }
}
```

#### Últimos Bloques
```graphql
query GetLatestBlocks($limit: Int) {
  latestBlocks(limit: $limit) {
    index
    hash
    timestamp
    transactions {
      fromAddress
      toAddress
      amount
    }
  }
}
```

### Mutations

#### Crear Transacción
```graphql
mutation CreateTransaction(
  $fromAddress: String!,
  $toAddress: String!,
  $amount: Float!,
  $privateKey: String!
) {
  createTransaction(
    fromAddress: $fromAddress,
    toAddress: $toAddress,
    amount: $amount,
    privateKey: $privateKey
  ) {
    transactionHash
    status
    message
  }
}
```

---

## SDKs para Motores de Juegos

### Unity SDK (C#)

**Instalación:**
1. Copia `PlayerGoldSDK.cs` a `Assets/Scripts/`
2. Configura tu API key en el Inspector

**Ejemplo de uso:**
```csharp
// Inicializar
PlayerGoldSDK.Instance.Initialize("your_api_key");

// Consultar saldo
PlayerGoldSDK.Instance.GetBalance(
    "player_address",
    onSuccess: (balance) => {
        Debug.Log($"Saldo: {balance} $PRGLD");
    },
    onError: (error) => {
        Debug.LogError($"Error: {error}");
    }
);

// Crear transacción
PlayerGoldSDK.Instance.CreateTransaction(
    fromAddress: "player_address",
    toAddress: "game_address",
    amount: 10.0f,
    privateKey: "player_key",
    onSuccess: (txHash) => {
        Debug.Log($"Transacción: {txHash}");
    },
    onError: (error) => {
        Debug.LogError($"Error: {error}");
    }
);
```

### Unreal Engine SDK (C++)

**Instalación:**
1. Copia archivos `.h` y `.cpp` a `Source/YourProject/`
2. Agrega dependencias en `.Build.cs`
3. Recompila el proyecto

**Ejemplo de uso:**
```cpp
// Obtener subsistema
UPlayerGoldSDK* SDK = GetGameInstance()->GetSubsystem<UPlayerGoldSDK>();

// Inicializar
SDK->InitializeSDK("your_api_key");

// Consultar saldo
FOnBalanceReceived OnSuccess;
OnSuccess.BindDynamic(this, &AMyActor::OnBalanceReceived);

FOnError OnError;
OnError.BindDynamic(this, &AMyActor::OnError);

SDK->GetBalance("player_address", OnSuccess, OnError);
```

### JavaScript SDK

**Instalación (Navegador):**
```html
<script src="playergold-sdk.js"></script>
<script>
    const sdk = new PlayerGoldSDK({
        apiKey: 'your_api_key',
        apiUrl: 'http://localhost:5000/api/v1'
    });
</script>
```

**Instalación (Node.js):**
```javascript
const { PlayerGoldSDK } = require('./playergold-sdk.js');

const sdk = new PlayerGoldSDK({
    apiKey: 'your_api_key'
});
```

**Ejemplo de uso:**
```javascript
// Inicializar
await sdk.initialize();

// Consultar saldo
const balance = await sdk.getBalance('player_address');
console.log(`Saldo: ${balance} $PRGLD`);

// Crear transacción
const txHash = await sdk.createTransaction({
    fromAddress: 'player_address',
    toAddress: 'game_address',
    amount: 10.0,
    privateKey: 'player_key'
});

// Esperar confirmación
const confirmedTx = await sdk.waitForConfirmation(txHash, 3);
console.log('Transacción confirmada:', confirmedTx);
```

---

## Sistema de NFTs

### Crear NFT

```python
from src.blockchain.nft import NFTRegistry, NFTMetadata
from decimal import Decimal

registry = NFTRegistry()

# Definir metadatos
metadata = NFTMetadata(
    name="Legendary Sword",
    description="A powerful sword",
    image_url="https://game.com/items/sword.png",
    game_id="fantasy_rpg",
    item_type="weapon",
    rarity="legendary",
    level=50,
    attributes={
        "attack": 100,
        "durability": 95
    },
    creator="creator_address"
)

# Mintear NFT
nft = registry.mint_nft(
    owner="player_address",
    metadata=metadata,
    royalty_percentage=Decimal('5.0')
)
```

### Transferir NFT

```python
# Transferir con precio (calcula royalty automáticamente)
transfer_data = registry.transfer_nft(
    token_id="NFT-00000001",
    from_address="seller_address",
    to_address="buyer_address",
    price=Decimal('100.0')
)

print(f"Royalty pagado: {transfer_data['royalty_paid']['amount']}")
print(f"Destinatario: {transfer_data['royalty_paid']['recipient']}")
```

### Marketplace

```python
from src.blockchain.nft import NFTMarketplace

marketplace = NFTMarketplace(registry)

# Listar NFT para venta
marketplace.list_nft(
    token_id="NFT-00000001",
    seller="seller_address",
    price=Decimal('100.0')
)

# Comprar NFT
purchase = marketplace.buy_nft(
    token_id="NFT-00000001",
    buyer="buyer_address",
    buyer_balance=Decimal('200.0')
)

print(f"Vendedor recibe: {purchase['seller_receives']}")
print(f"Royalty: {purchase['royalty']['amount']}")
```

### Características de NFTs

- **Metadatos Extensibles:** Atributos personalizados para cualquier tipo de activo
- **Royalties Automáticos:** Porcentaje configurable para creadores en cada venta
- **Historial de Transferencias:** Registro completo de todas las transacciones
- **Evolución de Items:** Actualización de atributos sin cambiar el token ID
- **Cross-Game:** NFTs que funcionan en múltiples juegos

---

## Autenticación y Seguridad

### Mejores Prácticas

1. **Protección de API Keys**
   - Nunca expongas API keys en código cliente
   - Usa variables de entorno
   - Rota keys periódicamente

2. **Gestión de Claves Privadas**
   - Nunca almacenes claves privadas en texto plano
   - Usa wallets del lado del servidor para transacciones del juego
   - Implementa firma de transacciones en el cliente

3. **Rate Limiting**
   - Respeta los límites de la API
   - Implementa retry logic con backoff exponencial
   - Usa caching para reducir peticiones

4. **Validación**
   - Valida todas las direcciones antes de transacciones
   - Verifica saldos antes de compras
   - Implementa límites de transacción

---

## Ejemplos de Integración

### Caso 1: Compra en el Juego

```javascript
async function purchaseItem(itemId, price) {
    try {
        // Verificar saldo
        const balance = await sdk.getBalance(playerAddress);
        if (balance < price) {
            throw new Error('Saldo insuficiente');
        }
        
        // Crear transacción
        const txHash = await sdk.createTransaction({
            fromAddress: playerAddress,
            toAddress: gameWalletAddress,
            amount: price,
            privateKey: playerPrivateKey
        });
        
        // Esperar confirmación
        await sdk.waitForConfirmation(txHash, 3);
        
        // Entregar item
        giveItemToPlayer(itemId);
        
        console.log('Compra exitosa');
    } catch (error) {
        console.error('Error en compra:', error);
    }
}
```

### Caso 2: Recompensa por Logro

```javascript
async function rewardPlayer(playerAddress, amount, achievement) {
    try {
        const txHash = await sdk.createTransaction({
            fromAddress: gameWalletAddress,
            toAddress: playerAddress,
            amount: amount,
            privateKey: gamePrivateKey
        });
        
        console.log(`Recompensa de ${amount} $PRGLD por ${achievement}`);
        
        return txHash;
    } catch (error) {
        console.error('Error al recompensar:', error);
    }
}
```

### Caso 3: Trading de NFTs entre Jugadores

```python
def player_to_player_nft_trade(nft_id, seller, buyer, price):
    """Trading P2P de NFTs"""
    
    # Verificar propiedad
    nft = registry.get_nft(nft_id)
    if nft.owner != seller:
        raise ValueError("Vendedor no es el propietario")
    
    # Verificar saldo del comprador
    buyer_balance = blockchain.get_balance(buyer)
    if buyer_balance < price:
        raise ValueError("Comprador no tiene saldo suficiente")
    
    # Transferir tokens
    token_tx = blockchain.create_transaction(
        from_address=buyer,
        to_address=seller,
        amount=price - nft.royalty.calculate_royalty(price)
    )
    
    # Pagar royalty al creador
    if nft.royalty:
        royalty_amount = nft.royalty.calculate_royalty(price)
        royalty_tx = blockchain.create_transaction(
            from_address=buyer,
            to_address=nft.royalty.creator_address,
            amount=royalty_amount
        )
    
    # Transferir NFT
    registry.transfer_nft(nft_id, seller, buyer, price)
    
    return {
        'nft_id': nft_id,
        'token_tx': token_tx,
        'royalty_tx': royalty_tx if nft.royalty else None
    }
```

---

## Soporte y Recursos

### Documentación Adicional
- [Technical Whitepaper](./Technical_Whitepaper.md)
- [SDK README](../src/api/sdks/README.md)
- [Ejemplos de Código](../examples/)

### Testing
- Usa la testnet para desarrollo
- Ejecuta tests de integración antes de producción
- Monitorea transacciones en el explorador de bloques

### Contacto
Para soporte técnico o preguntas:
- GitHub Issues: [repositorio]
- Email: support@playergold.com
- Discord: [servidor de desarrollo]

---

## Changelog

### v1.0.0 (2024-01-15)
- ✅ API REST completa
- ✅ API GraphQL
- ✅ SDKs para Unity, Unreal y JavaScript
- ✅ Sistema de NFTs con royalties
- ✅ Marketplace descentralizado
- ✅ Autenticación JWT
- ✅ Rate limiting y protección DDoS

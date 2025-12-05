# PlayerGold SDKs para Motores de Juegos

Este directorio contiene los SDKs oficiales de PlayerGold para integración con diferentes motores de juegos.

## 📦 SDKs Disponibles

### Unity SDK (C#)
SDK completo para integración con Unity Engine.

**Ubicación:** `unity/PlayerGoldSDK.cs`

**Características:**
- Gestión automática de autenticación
- Consulta de saldos en tiempo real
- Creación y seguimiento de transacciones
- Integración con coroutines de Unity
- Soporte para callbacks asíncronos

**Instalación:**
1. Copia `PlayerGoldSDK.cs` a tu proyecto Unity en `Assets/Scripts/`
2. Copia `ExampleUsage.cs` para ver ejemplos de uso
3. Configura tu API key en el Inspector

**Ejemplo de uso:**
```csharp
// Inicializar SDK
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
        Debug.Log($"Transacción creada: {txHash}");
    },
    onError: (error) => {
        Debug.LogError($"Error: {error}");
    }
);
```

### Unreal Engine SDK (C++)
SDK nativo para Unreal Engine con soporte completo de Blueprints.

**Ubicación:** `unreal/PlayerGoldSDK.h` y `unreal/PlayerGoldSDK.cpp`

**Características:**
- Implementado como Game Instance Subsystem
- Soporte completo para Blueprints
- Gestión automática de HTTP requests
- Serialización JSON integrada
- Delegates para callbacks

**Instalación:**
1. Copia los archivos `.h` y `.cpp` a tu proyecto Unreal en `Source/YourProject/`
2. Agrega las dependencias en tu archivo `.Build.cs`:
```csharp
PublicDependencyModuleNames.AddRange(new string[] { 
    "Core", 
    "CoreUObject", 
    "Engine", 
    "Http", 
    "Json", 
    "JsonUtilities" 
});
```
3. Recompila el proyecto

**Ejemplo de uso (C++):**
```cpp
// Obtener el subsistema
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

**Ejemplo de uso (Blueprints):**
1. En cualquier Blueprint, usa "Get Game Instance" → "Get Subsystem" → "PlayerGold SDK"
2. Llama a "Initialize SDK" con tu API key
3. Usa los nodos "Get Balance", "Create Transaction", etc.

### JavaScript SDK
SDK ligero para juegos web y aplicaciones JavaScript.

**Ubicación:** `javascript/playergold-sdk.js`

**Características:**
- Compatible con navegadores modernos y Node.js
- API basada en Promises/async-await
- Gestión automática de tokens
- Utilidades para gestión de wallets
- Sin dependencias externas

**Instalación:**

**Para navegadores:**
```html
<script src="playergold-sdk.js"></script>
<script>
    const sdk = new PlayerGoldSDK({
        apiKey: 'your_api_key',
        apiUrl: 'http://localhost:5000/api/v1'
    });
</script>
```

**Para Node.js:**
```javascript
const { PlayerGoldSDK } = require('./playergold-sdk.js');

const sdk = new PlayerGoldSDK({
    apiKey: 'your_api_key',
    apiUrl: 'http://localhost:5000/api/v1'
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

// Generar nueva wallet
const wallet = PlayerGoldWallet.generateWallet();
console.log('Nueva wallet:', wallet);
```

## 🔑 Obtener API Key

Para usar cualquiera de los SDKs, necesitas una API key:

1. Registra tu juego en la API:
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@yourgame.com",
    "game_name": "Your Awesome Game"
  }'
```

2. Guarda la API key que recibes en la respuesta

3. Usa la API key en tu SDK

## 📚 Funcionalidades Comunes

Todos los SDKs proporcionan las siguientes funcionalidades:

### Autenticación
- Registro automático con API key
- Gestión de tokens JWT
- Renovación automática de tokens

### Consultas
- **getBalance(address)**: Obtiene el saldo de una dirección
- **getTransaction(txHash)**: Obtiene información de una transacción
- **getTransactionHistory(address)**: Obtiene el historial de transacciones
- **getNetworkStatus()**: Obtiene el estado de la red
- **getBlock(index)**: Obtiene información de un bloque

### Transacciones
- **createTransaction()**: Crea una nueva transacción
- **waitForConfirmation()**: Espera la confirmación de una transacción

## 🔒 Seguridad

### Mejores Prácticas

1. **Nunca expongas claves privadas en el código**
   - Usa variables de entorno
   - Implementa un sistema de gestión de claves seguro
   - Considera usar wallets del lado del servidor

2. **Valida todas las entradas**
   - Verifica direcciones antes de enviar transacciones
   - Valida cantidades y fees
   - Implementa límites de transacción

3. **Maneja errores apropiadamente**
   - Implementa reintentos para errores de red
   - Muestra mensajes claros al usuario
   - Registra errores para debugging

4. **Rate Limiting**
   - Respeta los límites de la API
   - Implementa caching cuando sea apropiado
   - Usa batch requests cuando sea posible

## 🎮 Casos de Uso

### Compras en el Juego
```javascript
// Jugador compra un item
async function purchaseItem(itemId, price) {
    try {
        const txHash = await sdk.createTransaction({
            fromAddress: playerWallet,
            toAddress: gameWallet,
            amount: price,
            privateKey: playerKey
        });
        
        // Esperar confirmación
        await sdk.waitForConfirmation(txHash);
        
        // Entregar item al jugador
        giveItemToPlayer(itemId);
    } catch (error) {
        console.error('Purchase failed:', error);
    }
}
```

### Recompensas por Logros
```javascript
// Recompensar al jugador por completar un logro
async function rewardPlayer(playerAddress, amount) {
    try {
        const txHash = await sdk.createTransaction({
            fromAddress: gameWallet,
            toAddress: playerAddress,
            amount: amount,
            privateKey: gameKey
        });
        
        console.log(`Recompensa enviada: ${amount} $PRGLD`);
    } catch (error) {
        console.error('Reward failed:', error);
    }
}
```

### Trading entre Jugadores
```javascript
// Intercambio P2P entre jugadores
async function playerToPlayerTrade(fromPlayer, toPlayer, amount) {
    try {
        const txHash = await sdk.createTransaction({
            fromAddress: fromPlayer.address,
            toAddress: toPlayer.address,
            amount: amount,
            privateKey: fromPlayer.key
        });
        
        await sdk.waitForConfirmation(txHash);
        
        console.log('Trade completed successfully');
    } catch (error) {
        console.error('Trade failed:', error);
    }
}
```

## 📊 Monitoreo

Todos los SDKs incluyen logging integrado para facilitar el debugging:

- **Unity**: Usa `Debug.Log()` para mensajes
- **Unreal**: Usa `UE_LOG()` con categoría `LogTemp`
- **JavaScript**: Usa `console.log()` y `console.error()`

## 🆘 Soporte

Si encuentras problemas o tienes preguntas:

1. Revisa la documentación de la API en `/docs`
2. Consulta los ejemplos incluidos
3. Abre un issue en el repositorio
4. Contacta al equipo de desarrollo

## 📝 Licencia

Estos SDKs son parte del proyecto PlayerGold y están disponibles bajo la misma licencia del proyecto principal.

## 🔄 Actualizaciones

Mantén tus SDKs actualizados para obtener las últimas características y correcciones de seguridad:

- **Unity**: Reemplaza el archivo `.cs` con la última versión
- **Unreal**: Recompila después de actualizar los archivos
- **JavaScript**: Actualiza el archivo `.js` y limpia el cache del navegador

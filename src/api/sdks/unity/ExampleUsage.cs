/*
 * Ejemplo de uso del SDK de PlayerGold en Unity
 */

using UnityEngine;
using PlayerGold.SDK;

public class PlayerGoldExample : MonoBehaviour
{
    [Header("Configuration")]
    [SerializeField] private string apiKey = "your_api_key_here";
    [SerializeField] private string playerAddress = "player_wallet_address";
    [SerializeField] private string playerPrivateKey = "player_private_key";
    
    [Header("UI References")]
    [SerializeField] private TMPro.TextMeshProUGUI balanceText;
    [SerializeField] private TMPro.TextMeshProUGUI statusText;
    
    private void Start()
    {
        // Inicializar SDK
        PlayerGoldSDK.Instance.Initialize(apiKey);
        
        // Obtener estado de la red
        CheckNetworkStatus();
        
        // Obtener saldo del jugador
        UpdatePlayerBalance();
    }
    
    /// <summary>
    /// Verifica el estado de la red
    /// </summary>
    public void CheckNetworkStatus()
    {
        PlayerGoldSDK.Instance.GetNetworkStatus(
            onSuccess: (status) =>
            {
                Debug.Log($"Red PlayerGold conectada - Bloques: {status.chain_length}");
                statusText.text = $"Conectado - Bloque #{status.last_block_index}";
            },
            onError: (error) =>
            {
                Debug.LogError($"Error al conectar con la red: {error}");
                statusText.text = "Desconectado";
            }
        );
    }
    
    /// <summary>
    /// Actualiza el saldo del jugador
    /// </summary>
    public void UpdatePlayerBalance()
    {
        PlayerGoldSDK.Instance.GetBalance(
            playerAddress,
            onSuccess: (balance) =>
            {
                Debug.Log($"Saldo del jugador: {balance} $PRGLD");
                balanceText.text = $"{balance:F2} $PRGLD";
            },
            onError: (error) =>
            {
                Debug.LogError($"Error al obtener saldo: {error}");
                balanceText.text = "Error";
            }
        );
    }
    
    /// <summary>
    /// Compra un item en el juego usando PlayerGold
    /// </summary>
    public void PurchaseItem(string itemId, float price)
    {
        string gameWalletAddress = "game_treasury_address";
        
        Debug.Log($"Comprando {itemId} por {price} $PRGLD...");
        
        PlayerGoldSDK.Instance.CreateTransaction(
            fromAddress: playerAddress,
            toAddress: gameWalletAddress,
            amount: price,
            privateKey: playerPrivateKey,
            onSuccess: (txHash) =>
            {
                Debug.Log($"Compra exitosa! Hash: {txHash}");
                
                // Esperar confirmación
                StartCoroutine(WaitForConfirmation(txHash, itemId));
            },
            onError: (error) =>
            {
                Debug.LogError($"Error en la compra: {error}");
                ShowErrorMessage("No se pudo completar la compra");
            }
        );
    }
    
    /// <summary>
    /// Espera la confirmación de una transacción
    /// </summary>
    private System.Collections.IEnumerator WaitForConfirmation(string txHash, string itemId)
    {
        int maxAttempts = 30;
        int attempts = 0;
        
        while (attempts < maxAttempts)
        {
            bool confirmed = false;
            
            PlayerGoldSDK.Instance.GetTransaction(
                txHash,
                onSuccess: (txInfo) =>
                {
                    if (txInfo.status == "confirmed" && txInfo.confirmations >= 3)
                    {
                        confirmed = true;
                        Debug.Log($"Transacción confirmada con {txInfo.confirmations} confirmaciones");
                        
                        // Entregar el item al jugador
                        DeliverItemToPlayer(itemId);
                    }
                },
                onError: (error) =>
                {
                    Debug.LogWarning($"Error al verificar transacción: {error}");
                }
            );
            
            if (confirmed)
            {
                yield break;
            }
            
            attempts++;
            yield return new WaitForSeconds(2f);
        }
        
        Debug.LogWarning("Timeout esperando confirmación de transacción");
    }
    
    /// <summary>
    /// Entrega un item al jugador después de confirmar el pago
    /// </summary>
    private void DeliverItemToPlayer(string itemId)
    {
        Debug.Log($"Entregando item {itemId} al jugador");
        
        // Aquí iría la lógica para agregar el item al inventario del jugador
        // Por ejemplo:
        // PlayerInventory.AddItem(itemId);
        
        ShowSuccessMessage($"¡Has adquirido {itemId}!");
        
        // Actualizar saldo
        UpdatePlayerBalance();
    }
    
    /// <summary>
    /// Recompensa al jugador con tokens por logros
    /// </summary>
    public void RewardPlayer(float amount, string reason)
    {
        string gameWalletAddress = "game_treasury_address";
        string gamePrivateKey = "game_private_key";
        
        Debug.Log($"Recompensando jugador con {amount} $PRGLD por: {reason}");
        
        PlayerGoldSDK.Instance.CreateTransaction(
            fromAddress: gameWalletAddress,
            toAddress: playerAddress,
            amount: amount,
            privateKey: gamePrivateKey,
            onSuccess: (txHash) =>
            {
                Debug.Log($"Recompensa enviada! Hash: {txHash}");
                ShowSuccessMessage($"¡Has ganado {amount} $PRGLD!");
                UpdatePlayerBalance();
            },
            onError: (error) =>
            {
                Debug.LogError($"Error al enviar recompensa: {error}");
            }
        );
    }
    
    // Métodos auxiliares para UI
    private void ShowSuccessMessage(string message)
    {
        Debug.Log($"SUCCESS: {message}");
        // Aquí mostrarías un mensaje en la UI del juego
    }
    
    private void ShowErrorMessage(string message)
    {
        Debug.LogError($"ERROR: {message}");
        // Aquí mostrarías un mensaje de error en la UI del juego
    }
}

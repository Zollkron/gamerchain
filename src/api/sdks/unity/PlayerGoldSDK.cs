/*
 * PlayerGold SDK para Unity
 * SDK para integración de blockchain PlayerGold en juegos Unity
 */

using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace PlayerGold.SDK
{
    /// <summary>
    /// Cliente principal del SDK de PlayerGold para Unity
    /// </summary>
    public class PlayerGoldSDK : MonoBehaviour
    {
        [Header("API Configuration")]
        [SerializeField] private string apiUrl = "http://localhost:5000/api/v1";
        [SerializeField] private string apiKey;
        
        private string authToken;
        private float tokenExpirationTime;
        
        // Singleton
        private static PlayerGoldSDK instance;
        public static PlayerGoldSDK Instance
        {
            get
            {
                if (instance == null)
                {
                    GameObject go = new GameObject("PlayerGoldSDK");
                    instance = go.AddComponent<PlayerGoldSDK>();
                    DontDestroyOnLoad(go);
                }
                return instance;
            }
        }
        
        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Destroy(gameObject);
                return;
            }
            instance = this;
            DontDestroyOnLoad(gameObject);
        }
        
        /// <summary>
        /// Inicializa el SDK con la API key
        /// </summary>
        public void Initialize(string apiKey, string apiUrl = null)
        {
            this.apiKey = apiKey;
            if (!string.IsNullOrEmpty(apiUrl))
            {
                this.apiUrl = apiUrl;
            }
            
            StartCoroutine(AuthenticateCoroutine());
        }
        
        /// <summary>
        /// Autentica con la API y obtiene token JWT
        /// </summary>
        private IEnumerator AuthenticateCoroutine()
        {
            string url = $"{apiUrl}/auth/token";
            
            var requestData = new Dictionary<string, string>
            {
                { "api_key", apiKey }
            };
            
            string jsonData = JsonUtility.ToJson(new ApiKeyRequest { api_key = apiKey });
            
            using (UnityWebRequest request = UnityWebRequest.Post(url, jsonData, "application/json"))
            {
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    TokenResponse response = JsonUtility.FromJson<TokenResponse>(request.downloadHandler.text);
                    authToken = response.token;
                    tokenExpirationTime = Time.time + response.expires_in;
                    
                    Debug.Log("PlayerGold SDK: Autenticación exitosa");
                }
                else
                {
                    Debug.LogError($"PlayerGold SDK: Error de autenticación - {request.error}");
                }
            }
        }
        
        /// <summary>
        /// Obtiene el saldo de una dirección
        /// </summary>
        public void GetBalance(string address, Action<float> onSuccess, Action<string> onError)
        {
            StartCoroutine(GetBalanceCoroutine(address, onSuccess, onError));
        }
        
        private IEnumerator GetBalanceCoroutine(string address, Action<float> onSuccess, Action<string> onError)
        {
            yield return EnsureAuthenticated();
            
            string url = $"{apiUrl}/balance/{address}";
            
            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                request.SetRequestHeader("Authorization", $"Bearer {authToken}");
                
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    BalanceResponse response = JsonUtility.FromJson<BalanceResponse>(request.downloadHandler.text);
                    onSuccess?.Invoke(response.balance);
                }
                else
                {
                    onError?.Invoke(request.error);
                }
            }
        }
        
        /// <summary>
        /// Crea una transacción
        /// </summary>
        public void CreateTransaction(
            string fromAddress,
            string toAddress,
            float amount,
            string privateKey,
            Action<string> onSuccess,
            Action<string> onError
        )
        {
            StartCoroutine(CreateTransactionCoroutine(fromAddress, toAddress, amount, privateKey, onSuccess, onError));
        }
        
        private IEnumerator CreateTransactionCoroutine(
            string fromAddress,
            string toAddress,
            float amount,
            string privateKey,
            Action<string> onSuccess,
            Action<string> onError
        )
        {
            yield return EnsureAuthenticated();
            
            string url = $"{apiUrl}/transaction";
            
            TransactionRequest txRequest = new TransactionRequest
            {
                from_address = fromAddress,
                to_address = toAddress,
                amount = amount,
                private_key = privateKey,
                fee = 0.01f
            };
            
            string jsonData = JsonUtility.ToJson(txRequest);
            
            using (UnityWebRequest request = UnityWebRequest.Post(url, jsonData, "application/json"))
            {
                request.SetRequestHeader("Authorization", $"Bearer {authToken}");
                
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    TransactionResponse response = JsonUtility.FromJson<TransactionResponse>(request.downloadHandler.text);
                    onSuccess?.Invoke(response.transaction_hash);
                }
                else
                {
                    onError?.Invoke(request.error);
                }
            }
        }
        
        /// <summary>
        /// Obtiene el estado de una transacción
        /// </summary>
        public void GetTransaction(string txHash, Action<TransactionInfo> onSuccess, Action<string> onError)
        {
            StartCoroutine(GetTransactionCoroutine(txHash, onSuccess, onError));
        }
        
        private IEnumerator GetTransactionCoroutine(string txHash, Action<TransactionInfo> onSuccess, Action<string> onError)
        {
            yield return EnsureAuthenticated();
            
            string url = $"{apiUrl}/transaction/{txHash}";
            
            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                request.SetRequestHeader("Authorization", $"Bearer {authToken}");
                
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    TransactionInfo response = JsonUtility.FromJson<TransactionInfo>(request.downloadHandler.text);
                    onSuccess?.Invoke(response);
                }
                else
                {
                    onError?.Invoke(request.error);
                }
            }
        }
        
        /// <summary>
        /// Obtiene el estado de la red
        /// </summary>
        public void GetNetworkStatus(Action<NetworkStatus> onSuccess, Action<string> onError)
        {
            StartCoroutine(GetNetworkStatusCoroutine(onSuccess, onError));
        }
        
        private IEnumerator GetNetworkStatusCoroutine(Action<NetworkStatus> onSuccess, Action<string> onError)
        {
            string url = $"{apiUrl}/network/status";
            
            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                yield return request.SendWebRequest();
                
                if (request.result == UnityWebRequest.Result.Success)
                {
                    NetworkStatus response = JsonUtility.FromJson<NetworkStatus>(request.downloadHandler.text);
                    onSuccess?.Invoke(response);
                }
                else
                {
                    onError?.Invoke(request.error);
                }
            }
        }
        
        /// <summary>
        /// Asegura que el token esté válido
        /// </summary>
        private IEnumerator EnsureAuthenticated()
        {
            if (string.IsNullOrEmpty(authToken) || Time.time >= tokenExpirationTime - 300)
            {
                yield return AuthenticateCoroutine();
            }
        }
    }
    
    // Clases de datos
    [Serializable]
    public class ApiKeyRequest
    {
        public string api_key;
    }
    
    [Serializable]
    public class TokenResponse
    {
        public string token;
        public int expires_in;
    }
    
    [Serializable]
    public class BalanceResponse
    {
        public string address;
        public float balance;
        public string timestamp;
    }
    
    [Serializable]
    public class TransactionRequest
    {
        public string from_address;
        public string to_address;
        public float amount;
        public string private_key;
        public float fee;
    }
    
    [Serializable]
    public class TransactionResponse
    {
        public string transaction_hash;
        public string status;
        public string message;
    }
    
    [Serializable]
    public class TransactionInfo
    {
        public string status;
        public int confirmations;
        public TransactionData transaction;
    }
    
    [Serializable]
    public class TransactionData
    {
        public string from_address;
        public string to_address;
        public float amount;
        public float fee;
        public float timestamp;
    }
    
    [Serializable]
    public class NetworkStatus
    {
        public int chain_length;
        public int last_block_index;
        public string last_block_hash;
        public int pending_transactions;
        public int difficulty;
    }
}

/**
 * PlayerGold SDK para JavaScript
 * SDK para integración de blockchain PlayerGold en juegos web
 * @version 1.0.0
 */

class PlayerGoldSDK {
    /**
     * Constructor del SDK
     * @param {Object} config - Configuración del SDK
     * @param {string} config.apiKey - API key del desarrollador
     * @param {string} config.apiUrl - URL base de la API (opcional)
     */
    constructor(config = {}) {
        this.apiKey = config.apiKey;
        this.apiUrl = config.apiUrl || 'http://localhost:5000/api/v1';
        this.authToken = null;
        this.tokenExpiration = null;
    }

    /**
     * Inicializa el SDK y autentica con la API
     * @returns {Promise<boolean>} - True si la autenticación fue exitosa
     */
    async initialize() {
        try {
            await this.authenticate();
            console.log('PlayerGold SDK initialized successfully');
            return true;
        } catch (error) {
            console.error('Failed to initialize PlayerGold SDK:', error);
            return false;
        }
    }

    /**
     * Autentica con la API y obtiene token JWT
     * @private
     * @returns {Promise<void>}
     */
    async authenticate() {
        const response = await fetch(`${this.apiUrl}/auth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_key: this.apiKey
            })
        });

        if (!response.ok) {
            throw new Error(`Authentication failed: ${response.statusText}`);
        }

        const data = await response.json();
        this.authToken = data.token;
        this.tokenExpiration = Date.now() + (data.expires_in * 1000);
    }

    /**
     * Asegura que el token esté válido
     * @private
     * @returns {Promise<void>}
     */
    async ensureAuthenticated() {
        // Re-autenticar si el token está por expirar (5 minutos antes)
        if (!this.authToken || Date.now() >= (this.tokenExpiration - 300000)) {
            await this.authenticate();
        }
    }

    /**
     * Realiza una petición HTTP autenticada
     * @private
     * @param {string} endpoint - Endpoint de la API
     * @param {Object} options - Opciones de fetch
     * @returns {Promise<Object>} - Respuesta JSON
     */
    async request(endpoint, options = {}) {
        await this.ensureAuthenticated();

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authToken}`,
            ...options.headers
        };

        const response = await fetch(`${this.apiUrl}${endpoint}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || response.statusText);
        }

        return response.json();
    }

    /**
     * Obtiene el estado de la red
     * @returns {Promise<Object>} - Estado de la red
     */
    async getNetworkStatus() {
        const response = await fetch(`${this.apiUrl}/network/status`);
        
        if (!response.ok) {
            throw new Error(`Failed to get network status: ${response.statusText}`);
        }
        
        return response.json();
    }

    /**
     * Obtiene el saldo de una dirección
     * @param {string} address - Dirección de la wallet
     * @returns {Promise<number>} - Saldo en $PRGLD
     */
    async getBalance(address) {
        const data = await this.request(`/balance/${address}`);
        return data.balance;
    }

    /**
     * Crea una nueva transacción
     * @param {Object} transaction - Datos de la transacción
     * @param {string} transaction.fromAddress - Dirección origen
     * @param {string} transaction.toAddress - Dirección destino
     * @param {number} transaction.amount - Cantidad a transferir
     * @param {string} transaction.privateKey - Clave privada para firmar
     * @param {number} [transaction.fee=0.01] - Fee de la transacción
     * @returns {Promise<string>} - Hash de la transacción
     */
    async createTransaction({ fromAddress, toAddress, amount, privateKey, fee = 0.01 }) {
        const data = await this.request('/transaction', {
            method: 'POST',
            body: JSON.stringify({
                from_address: fromAddress,
                to_address: toAddress,
                amount,
                private_key: privateKey,
                fee
            })
        });

        return data.transaction_hash;
    }

    /**
     * Obtiene información de una transacción
     * @param {string} txHash - Hash de la transacción
     * @returns {Promise<Object>} - Información de la transacción
     */
    async getTransaction(txHash) {
        return this.request(`/transaction/${txHash}`);
    }

    /**
     * Obtiene el historial de transacciones de una dirección
     * @param {string} address - Dirección de la wallet
     * @param {Object} options - Opciones de paginación
     * @param {number} [options.page=1] - Número de página
     * @param {number} [options.perPage=20] - Transacciones por página
     * @returns {Promise<Object>} - Historial de transacciones
     */
    async getTransactionHistory(address, { page = 1, perPage = 20 } = {}) {
        return this.request(`/transactions/history/${address}?page=${page}&per_page=${perPage}`);
    }

    /**
     * Obtiene información de un bloque
     * @param {number} blockIndex - Índice del bloque
     * @returns {Promise<Object>} - Información del bloque
     */
    async getBlock(blockIndex) {
        return this.request(`/block/${blockIndex}`);
    }

    /**
     * Espera la confirmación de una transacción
     * @param {string} txHash - Hash de la transacción
     * @param {number} [requiredConfirmations=3] - Confirmaciones requeridas
     * @param {number} [timeout=60000] - Timeout en milisegundos
     * @returns {Promise<Object>} - Información de la transacción confirmada
     */
    async waitForConfirmation(txHash, requiredConfirmations = 3, timeout = 60000) {
        const startTime = Date.now();
        const pollInterval = 2000; // 2 segundos

        while (Date.now() - startTime < timeout) {
            try {
                const txInfo = await this.getTransaction(txHash);

                if (txInfo.status === 'confirmed' && txInfo.confirmations >= requiredConfirmations) {
                    return txInfo;
                }

                await new Promise(resolve => setTimeout(resolve, pollInterval));
            } catch (error) {
                console.warn('Error checking transaction status:', error);
                await new Promise(resolve => setTimeout(resolve, pollInterval));
            }
        }

        throw new Error('Transaction confirmation timeout');
    }
}

// Clase auxiliar para gestión de wallets en el navegador
class PlayerGoldWallet {
    /**
     * Genera una nueva wallet
     * @returns {Object} - Wallet con address y privateKey
     */
    static generateWallet() {
        // En producción, usar una librería criptográfica apropiada
        console.warn('This is a demo implementation. Use proper cryptography in production.');
        
        const randomBytes = new Uint8Array(32);
        crypto.getRandomValues(randomBytes);
        
        const privateKey = Array.from(randomBytes)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
        
        // Generar address desde private key (simplificado)
        const address = 'PRGLD' + privateKey.substring(0, 40);
        
        return {
            address,
            privateKey
        };
    }

    /**
     * Guarda una wallet en localStorage
     * @param {Object} wallet - Wallet a guardar
     * @param {string} password - Password para encriptar
     */
    static saveWallet(wallet, password) {
        // En producción, encriptar apropiadamente
        const encrypted = btoa(JSON.stringify(wallet));
        localStorage.setItem('playergold_wallet', encrypted);
    }

    /**
     * Carga una wallet desde localStorage
     * @param {string} password - Password para desencriptar
     * @returns {Object|null} - Wallet o null si no existe
     */
    static loadWallet(password) {
        const encrypted = localStorage.getItem('playergold_wallet');
        
        if (!encrypted) {
            return null;
        }

        try {
            return JSON.parse(atob(encrypted));
        } catch (error) {
            console.error('Failed to load wallet:', error);
            return null;
        }
    }
}

// Exportar para uso en Node.js y navegador
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PlayerGoldSDK, PlayerGoldWallet };
}

// Exportar para uso con ES6 modules
if (typeof window !== 'undefined') {
    window.PlayerGoldSDK = PlayerGoldSDK;
    window.PlayerGoldWallet = PlayerGoldWallet;
}

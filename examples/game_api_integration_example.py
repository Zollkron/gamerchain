"""
Ejemplo de integración de la API REST/GraphQL con juegos
Demuestra cómo usar la API para transacciones, consultas de saldos y estado de red
"""

import requests
import json
from typing import Dict, Any


class GameAPIClient:
    """Cliente para interactuar con la API de PlayerGold"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.api_key = None
        self.token = None
    
    def register_game(self, email: str, game_name: str) -> Dict[str, Any]:
        """Registra un juego y obtiene API key"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json={
                "email": email,
                "game_name": game_name
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            self.api_key = data['api_key']
            print(f"✓ Juego registrado exitosamente")
            print(f"  API Key: {self.api_key}")
            return data
        else:
            print(f"✗ Error al registrar: {response.json()}")
            return None
    
    def get_auth_token(self) -> str:
        """Obtiene token JWT para autenticación"""
        if not self.api_key:
            print("✗ Primero debes registrar el juego")
            return None
        
        response = requests.post(
            f"{self.base_url}/api/v1/auth/token",
            json={"api_key": self.api_key}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            print(f"✓ Token obtenido (expira en {data['expires_in']} segundos)")
            return self.token
        else:
            print(f"✗ Error al obtener token: {response.json()}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene headers con autenticación"""
        if not self.token:
            self.get_auth_token()
        
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_network_status(self) -> Dict[str, Any]:
        """Obtiene el estado de la red"""
        response = requests.get(f"{self.base_url}/api/v1/network/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Estado de la Red:")
            print(f"  Longitud de cadena: {data['chain_length']}")
            print(f"  Último bloque: #{data['last_block_index']}")
            print(f"  Transacciones pendientes: {data['pending_transactions']}")
            print(f"  Dificultad: {data['difficulty']}")
            return data
        else:
            print(f"✗ Error al obtener estado: {response.json()}")
            return None
    
    def get_balance(self, address: str) -> float:
        """Obtiene el saldo de una dirección"""
        response = requests.get(
            f"{self.base_url}/api/v1/balance/{address}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n💰 Saldo de {address[:10]}...:")
            print(f"  Balance: {data['balance']} $PRGLD")
            return data['balance']
        else:
            print(f"✗ Error al obtener saldo: {response.json()}")
            return None
    
    def create_transaction(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        private_key: str,
        fee: float = 0.01
    ) -> Dict[str, Any]:
        """Crea una nueva transacción"""
        response = requests.post(
            f"{self.base_url}/api/v1/transaction",
            headers=self._get_headers(),
            json={
                "from_address": from_address,
                "to_address": to_address,
                "amount": amount,
                "fee": fee,
                "private_key": private_key
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"\n✓ Transacción creada:")
            print(f"  Hash: {data['transaction_hash']}")
            print(f"  Estado: {data['status']}")
            print(f"  Cantidad: {amount} $PRGLD")
            return data
        else:
            print(f"✗ Error al crear transacción: {response.json()}")
            return None
    
    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Obtiene información de una transacción"""
        response = requests.get(
            f"{self.base_url}/api/v1/transaction/{tx_hash}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📝 Transacción {tx_hash[:10]}...:")
            print(f"  Estado: {data['status']}")
            if 'confirmations' in data:
                print(f"  Confirmaciones: {data['confirmations']}")
            return data
        else:
            print(f"✗ Error al obtener transacción: {response.json()}")
            return None
    
    def get_transaction_history(
        self,
        address: str,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """Obtiene el historial de transacciones"""
        response = requests.get(
            f"{self.base_url}/api/v1/transactions/history/{address}",
            headers=self._get_headers(),
            params={"page": page, "per_page": per_page}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📜 Historial de {address[:10]}...:")
            print(f"  Total de transacciones: {data['total']}")
            print(f"  Mostrando página {data['page']} ({len(data['transactions'])} transacciones)")
            
            for i, tx_data in enumerate(data['transactions'][:5], 1):
                tx = tx_data['transaction']
                print(f"\n  {i}. {tx['from_address'][:8]}... → {tx['to_address'][:8]}...")
                print(f"     Cantidad: {tx['amount']} $PRGLD")
                print(f"     Confirmaciones: {tx_data['confirmations']}")
            
            return data
        else:
            print(f"✗ Error al obtener historial: {response.json()}")
            return None
    
    def get_block(self, block_index: int) -> Dict[str, Any]:
        """Obtiene información de un bloque"""
        response = requests.get(
            f"{self.base_url}/api/v1/block/{block_index}",
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            block = data['block']
            print(f"\n🔗 Bloque #{block['index']}:")
            print(f"  Hash: {block['hash'][:16]}...")
            print(f"  Transacciones: {len(block['transactions'])}")
            print(f"  Confirmaciones: {data['confirmations']}")
            return data
        else:
            print(f"✗ Error al obtener bloque: {response.json()}")
            return None


class GraphQLGameAPIClient:
    """Cliente para interactuar con la API GraphQL"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = f"{base_url}/graphql"
        self.token = None
    
    def set_token(self, token: str):
        """Establece el token de autenticación"""
        self.token = token
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene headers con autenticación"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def query(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """Ejecuta una query GraphQL"""
        response = requests.post(
            self.base_url,
            headers=self._get_headers(),
            json={"query": query, "variables": variables}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Error en query: {response.json()}")
            return None
    
    def get_network_status(self):
        """Obtiene el estado de la red usando GraphQL"""
        query = """
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
        """
        
        result = self.query(query)
        if result and 'data' in result:
            status = result['data']['networkStatus']
            print(f"\n📊 Estado de la Red (GraphQL):")
            print(f"  Longitud de cadena: {status['chainLength']}")
            print(f"  Último bloque: #{status['lastBlockIndex']}")
            print(f"  Transacciones pendientes: {status['pendingTransactions']}")
            return status
        return None
    
    def get_balance(self, address: str):
        """Obtiene el saldo usando GraphQL"""
        query = """
        query GetBalance($address: String!) {
            balance(address: $address) {
                address
                balance
                timestamp
            }
        }
        """
        
        result = self.query(query, {"address": address})
        if result and 'data' in result:
            balance = result['data']['balance']
            print(f"\n💰 Saldo (GraphQL):")
            print(f"  Dirección: {balance['address'][:10]}...")
            print(f"  Balance: {balance['balance']} $PRGLD")
            return balance
        return None
    
    def create_transaction(
        self,
        from_address: str,
        to_address: str,
        amount: float,
        private_key: str
    ):
        """Crea una transacción usando GraphQL"""
        mutation = """
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
        """
        
        variables = {
            "fromAddress": from_address,
            "toAddress": to_address,
            "amount": amount,
            "privateKey": private_key
        }
        
        result = self.query(mutation, variables)
        if result and 'data' in result:
            tx = result['data']['createTransaction']
            print(f"\n✓ Transacción creada (GraphQL):")
            print(f"  Hash: {tx['transactionHash']}")
            print(f"  Estado: {tx['status']}")
            return tx
        return None


def main():
    """Ejemplo de uso de la API"""
    print("=" * 60)
    print("Ejemplo de Integración API PlayerGold para Juegos")
    print("=" * 60)
    
    # Inicializar cliente REST
    rest_client = GameAPIClient()
    
    # 1. Registrar juego
    print("\n1. Registrando juego...")
    rest_client.register_game(
        email="developer@mygame.com",
        game_name="My Awesome Game"
    )
    
    # 2. Obtener token de autenticación
    print("\n2. Obteniendo token de autenticación...")
    rest_client.get_auth_token()
    
    # 3. Consultar estado de la red
    print("\n3. Consultando estado de la red...")
    rest_client.get_network_status()
    
    # 4. Consultar saldo de jugador
    print("\n4. Consultando saldo de jugador...")
    player_address = "player_wallet_address_123"
    rest_client.get_balance(player_address)
    
    # 5. Crear transacción (compra en juego)
    print("\n5. Creando transacción de compra en juego...")
    tx_data = rest_client.create_transaction(
        from_address=player_address,
        to_address="game_treasury_address",
        amount=10.0,
        private_key="player_private_key",
        fee=0.01
    )
    
    # 6. Verificar transacción
    if tx_data:
        print("\n6. Verificando transacción...")
        rest_client.get_transaction(tx_data['transaction_hash'])
    
    # 7. Obtener historial de transacciones
    print("\n7. Obteniendo historial de transacciones...")
    rest_client.get_transaction_history(player_address, page=1, per_page=10)
    
    # 8. Consultar bloque
    print("\n8. Consultando último bloque...")
    rest_client.get_block(0)
    
    # Ejemplo con GraphQL
    print("\n" + "=" * 60)
    print("Ejemplo con GraphQL")
    print("=" * 60)
    
    graphql_client = GraphQLGameAPIClient()
    graphql_client.set_token(rest_client.token)
    
    # Consultas GraphQL
    print("\n9. Consultando estado con GraphQL...")
    graphql_client.get_network_status()
    
    print("\n10. Consultando saldo con GraphQL...")
    graphql_client.get_balance(player_address)
    
    print("\n" + "=" * 60)
    print("✓ Ejemplo completado")
    print("=" * 60)


if __name__ == "__main__":
    main()

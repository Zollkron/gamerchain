"""
Tests para la API REST de integración con juegos
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.api.game_api import GameAPI
from src.blockchain.transaction import Transaction
from src.blockchain.block import Block


@pytest.fixture
def mock_blockchain():
    """Crea un blockchain mock para testing"""
    blockchain = Mock()
    blockchain.chain = []
    blockchain.pending_transactions = []
    blockchain.difficulty = 1
    
    # Mock de métodos
    blockchain.get_balance = Mock(return_value=100.0)
    blockchain.add_transaction = Mock(return_value=True)
    
    return blockchain


@pytest.fixture
def api_client(mock_blockchain):
    """Crea un cliente de API para testing"""
    api = GameAPI(mock_blockchain, secret_key='test_secret_key')
    api.app.config['TESTING'] = True
    return api.app.test_client()


class TestAuthentication:
    """Tests para autenticación de la API"""
    
    def test_register_developer(self, api_client):
        """Test: Registro de desarrollador"""
        response = api_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'dev@example.com',
                'game_name': 'Test Game'
            }
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'api_key' in data
        assert data['message'] == 'Desarrollador registrado exitosamente'
    
    def test_register_developer_missing_fields(self, api_client):
        """Test: Registro sin campos requeridos"""
        response = api_client.post(
            '/api/v1/auth/register',
            json={'email': 'dev@example.com'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_auth_token(self, api_client):
        """Test: Obtención de token JWT"""
        # Primero registrar
        register_response = api_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'dev@example.com',
                'game_name': 'Test Game'
            }
        )
        api_key = json.loads(register_response.data)['api_key']
        
        # Obtener token
        response = api_client.post(
            '/api/v1/auth/token',
            json={'api_key': api_key}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
        assert 'expires_in' in data
    
    def test_get_auth_token_invalid_key(self, api_client):
        """Test: Token con API key inválida"""
        response = api_client.post(
            '/api/v1/auth/token',
            json={'api_key': 'invalid_key'}
        )
        
        assert response.status_code == 401


class TestPublicEndpoints:
    """Tests para endpoints públicos"""
    
    def test_health_check(self, api_client):
        """Test: Health check endpoint"""
        response = api_client.get('/api/v1/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
    
    def test_network_status(self, api_client, mock_blockchain):
        """Test: Estado de la red"""
        # Agregar un bloque mock
        mock_block = Mock()
        mock_block.index = 0
        mock_block.hash = 'test_hash'
        mock_blockchain.chain = [mock_block]
        
        response = api_client.get('/api/v1/network/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['chain_length'] == 1
        assert data['last_block_index'] == 0
        assert data['last_block_hash'] == 'test_hash'


class TestProtectedEndpoints:
    """Tests para endpoints protegidos"""
    
    @pytest.fixture
    def auth_headers(self, api_client):
        """Crea headers de autenticación"""
        # Registrar y obtener token
        register_response = api_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'dev@example.com',
                'game_name': 'Test Game'
            }
        )
        api_key = json.loads(register_response.data)['api_key']
        
        token_response = api_client.post(
            '/api/v1/auth/token',
            json={'api_key': api_key}
        )
        token = json.loads(token_response.data)['token']
        
        return {'Authorization': f'Bearer {token}'}
    
    def test_get_balance_authenticated(self, api_client, auth_headers):
        """Test: Obtener saldo con autenticación"""
        response = api_client.get(
            '/api/v1/balance/test_address',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['address'] == 'test_address'
        assert data['balance'] == 100.0
    
    def test_get_balance_unauthenticated(self, api_client):
        """Test: Obtener saldo sin autenticación"""
        response = api_client.get('/api/v1/balance/test_address')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_transaction_authenticated(self, api_client, auth_headers, mock_blockchain):
        """Test: Crear transacción con autenticación"""
        # Mock de transacción válida
        mock_tx = Mock()
        mock_tx.is_valid = Mock(return_value=True)
        mock_tx.calculate_hash = Mock(return_value='tx_hash_123')
        
        with pytest.mock.patch('src.api.game_api.Transaction', return_value=mock_tx):
            response = api_client.post(
                '/api/v1/transaction',
                headers=auth_headers,
                json={
                    'from_address': 'address1',
                    'to_address': 'address2',
                    'amount': 10.0,
                    'private_key': 'test_key'
                }
            )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['status'] == 'pending'
        assert 'transaction_hash' in data


class TestRateLimiting:
    """Tests para rate limiting"""
    
    def test_rate_limit_exceeded(self, api_client):
        """Test: Exceder límite de rate"""
        # Hacer muchas peticiones rápidas
        for _ in range(150):
            response = api_client.get('/api/v1/health')
        
        # La última debería ser rechazada
        assert response.status_code == 429


class TestTransactionHistory:
    """Tests para historial de transacciones"""
    
    def test_get_transaction_history(self, api_client, auth_headers, mock_blockchain):
        """Test: Obtener historial de transacciones"""
        # Mock de bloques con transacciones
        mock_tx = Mock()
        mock_tx.from_address = 'test_address'
        mock_tx.to_address = 'other_address'
        mock_tx.to_dict = Mock(return_value={'amount': 10.0})
        
        mock_block = Mock()
        mock_block.index = 0
        mock_block.timestamp = datetime.utcnow().timestamp()
        mock_block.transactions = [mock_tx]
        
        mock_blockchain.chain = [mock_block]
        
        response = api_client.get(
            '/api/v1/transactions/history/test_address',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['address'] == 'test_address'
        assert len(data['transactions']) > 0
    
    def test_transaction_history_pagination(self, api_client, auth_headers, mock_blockchain):
        """Test: Paginación del historial"""
        # Mock de múltiples transacciones
        mock_blockchain.chain = []
        
        response = api_client.get(
            '/api/v1/transactions/history/test_address?page=1&per_page=10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['page'] == 1
        assert data['per_page'] == 10


class TestBlockEndpoints:
    """Tests para endpoints de bloques"""
    
    def test_get_block(self, api_client, auth_headers, mock_blockchain):
        """Test: Obtener bloque por índice"""
        mock_block = Mock()
        mock_block.to_dict = Mock(return_value={'index': 0})
        mock_blockchain.chain = [mock_block]
        
        response = api_client.get(
            '/api/v1/block/0',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'block' in data
        assert 'confirmations' in data
    
    def test_get_block_invalid_index(self, api_client, auth_headers, mock_blockchain):
        """Test: Obtener bloque con índice inválido"""
        mock_blockchain.chain = []
        
        response = api_client.get(
            '/api/v1/block/999',
            headers=auth_headers
        )
        
        assert response.status_code == 404

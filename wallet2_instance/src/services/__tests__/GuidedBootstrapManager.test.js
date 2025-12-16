/**
 * Guided Bootstrap Manager Tests
 * 
 * Tests for the intelligent bootstrap system that uses Network Coordinator
 * data to connect to known nodes before falling back to network scanning.
 */

const { GuidedBootstrapManager, BootstrapStrategy } = require('../GuidedBootstrapManager');

// Mock dependencies
const mockNetworkCoordinatorClient = {
  nodeId: 'test-node-123',
  getNetworkMap: jest.fn(),
  getCurrentLocation: jest.fn().mockResolvedValue({
    latitude: 40.4168,
    longitude: -3.7038
  })
};

const mockPeerDiscoveryManager = {
  validatePeerConnection: jest.fn(),
  establishConnection: jest.fn(),
  scanForPeers: jest.fn()
};

describe('GuidedBootstrapManager', () => {
  let guidedBootstrapManager;
  
  beforeEach(() => {
    jest.clearAllMocks();
    guidedBootstrapManager = new GuidedBootstrapManager(
      mockNetworkCoordinatorClient,
      mockPeerDiscoveryManager
    );
  });
  
  afterEach(() => {
    if (guidedBootstrapManager) {
      guidedBootstrapManager.cleanup();
    }
  });
  
  describe('Initialization', () => {
    test('should initialize with required dependencies', () => {
      expect(guidedBootstrapManager.networkCoordinatorClient).toBe(mockNetworkCoordinatorClient);
      expect(guidedBootstrapManager.peerDiscoveryManager).toBe(mockPeerDiscoveryManager);
      expect(guidedBootstrapManager.isBootstrapping).toBe(false);
    });
    
    test('should have default configuration', () => {
      expect(guidedBootstrapManager.config.maxCoordinatorNodes).toBe(10);
      expect(guidedBootstrapManager.config.connectionTimeout).toBe(8000);
      expect(guidedBootstrapManager.config.maxConcurrentConnections).toBe(5);
    });
  });
  
  describe('Network Map Fetching', () => {
    test('should fetch network map from coordinator', async () => {
      const mockNetworkMap = {
        active_nodes: 3,
        nodes: [
          {
            node_id: 'node1',
            public_ip: '192.168.1.100',
            port: 8000,
            latitude: 40.4168,
            longitude: -3.7038,
            last_seen: new Date().toISOString(),
            mining_active: true
          },
          {
            node_id: 'node2',
            public_ip: '192.168.1.101',
            port: 8000,
            latitude: 40.4200,
            longitude: -3.7100,
            last_seen: new Date().toISOString(),
            mining_active: false
          }
        ]
      };
      
      mockNetworkCoordinatorClient.getNetworkMap.mockResolvedValue(mockNetworkMap);
      
      const result = await guidedBootstrapManager.fetchNetworkMap();
      
      expect(result).toEqual(mockNetworkMap);
      expect(guidedBootstrapManager.networkMap).toEqual(mockNetworkMap);
      expect(guidedBootstrapManager.lastMapUpdate).toBeInstanceOf(Date);
    });
    
    test('should handle network map fetch failure', async () => {
      mockNetworkCoordinatorClient.getNetworkMap.mockRejectedValue(new Error('Network error'));
      
      const result = await guidedBootstrapManager.fetchNetworkMap();
      
      expect(result).toBeNull();
      expect(guidedBootstrapManager.networkMap).toBeNull();
    });
  });
  
  describe('Node Priority Calculation', () => {
    test('should calculate node priority based on proximity and other factors', () => {
      const node = {
        node_id: 'test-node',
        public_ip: '192.168.1.100',
        port: 8000,
        latitude: 40.4168,
        longitude: -3.7038,
        network_latency: 50,
        uptime_percentage: 95,
        connected_peers: 5,
        mining_active: true
      };
      
      const ourLocation = { latitude: 40.4200, longitude: -3.7100 };
      
      const priority = guidedBootstrapManager.calculateNodePriority(node, ourLocation);
      
      expect(priority).toBeGreaterThan(0);
      expect(priority).toBeLessThanOrEqual(2); // Max possible priority
    });
    
    test('should prioritize closer nodes', () => {
      const closeNode = {
        node_id: 'close-node',
        latitude: 40.4168,
        longitude: -3.7038,
        network_latency: 50
      };
      
      const farNode = {
        node_id: 'far-node',
        latitude: 41.0000,
        longitude: -4.0000,
        network_latency: 50
      };
      
      const ourLocation = { latitude: 40.4168, longitude: -3.7038 };
      
      const closePriority = guidedBootstrapManager.calculateNodePriority(closeNode, ourLocation);
      const farPriority = guidedBootstrapManager.calculateNodePriority(farNode, ourLocation);
      
      expect(closePriority).toBeGreaterThan(farPriority);
    });
  });
  
  describe('Node Validation', () => {
    test('should validate coordinator nodes correctly', () => {
      const validNode = {
        node_id: 'valid-node',
        public_ip: '192.168.1.100',
        port: 8000,
        last_seen: new Date().toISOString()
      };
      
      const invalidNode = {
        node_id: 'invalid-node',
        public_ip: 'invalid-ip',
        port: 8000
      };
      
      expect(guidedBootstrapManager.isValidCoordinatorNode(validNode)).toBe(true);
      expect(guidedBootstrapManager.isValidCoordinatorNode(invalidNode)).toBe(false);
    });
    
    test('should reject own node', () => {
      const ownNode = {
        node_id: 'test-node-123', // Same as mockNetworkCoordinatorClient.nodeId
        public_ip: '192.168.1.100',
        port: 8000,
        last_seen: new Date().toISOString()
      };
      
      expect(guidedBootstrapManager.isValidCoordinatorNode(ownNode)).toBe(false);
    });
    
    test('should reject stale nodes', () => {
      const staleNode = {
        node_id: 'stale-node',
        public_ip: '192.168.1.100',
        port: 8000,
        last_seen: new Date(Date.now() - 60 * 60 * 1000).toISOString() // 1 hour ago
      };
      
      expect(guidedBootstrapManager.isValidCoordinatorNode(staleNode)).toBe(false);
    });
  });
  
  describe('Coordinator-Guided Bootstrap', () => {
    test('should successfully connect to coordinator nodes', async () => {
      const mockNetworkMap = {
        active_nodes: 2,
        nodes: [
          {
            node_id: 'node1',
            public_ip: '192.168.1.100',
            port: 8000,
            latitude: 40.4168,
            longitude: -3.7038,
            last_seen: new Date().toISOString(),
            mining_active: true
          },
          {
            node_id: 'node2',
            public_ip: '192.168.1.101',
            port: 8000,
            latitude: 40.4200,
            longitude: -3.7100,
            last_seen: new Date().toISOString(),
            mining_active: false
          }
        ]
      };
      
      mockPeerDiscoveryManager.validatePeerConnection.mockResolvedValue(true);
      mockPeerDiscoveryManager.establishConnection.mockResolvedValue({
        socket: {},
        peer: { id: 'node1' }
      });
      
      const connectedPeers = await guidedBootstrapManager.attemptCoordinatorGuidedConnections(
        mockNetworkMap,
        'test-wallet-address'
      );
      
      expect(connectedPeers.length).toBeGreaterThan(0);
      expect(mockPeerDiscoveryManager.validatePeerConnection).toHaveBeenCalled();
      expect(mockPeerDiscoveryManager.establishConnection).toHaveBeenCalled();
    });
    
    test('should handle connection failures gracefully', async () => {
      const mockNetworkMap = {
        active_nodes: 1,
        nodes: [
          {
            node_id: 'failing-node',
            public_ip: '192.168.1.100',
            port: 8000,
            last_seen: new Date().toISOString()
          }
        ]
      };
      
      mockPeerDiscoveryManager.validatePeerConnection.mockResolvedValue(true);
      mockPeerDiscoveryManager.establishConnection.mockRejectedValue(new Error('Connection failed'));
      
      const connectedPeers = await guidedBootstrapManager.attemptCoordinatorGuidedConnections(
        mockNetworkMap,
        'test-wallet-address'
      );
      
      expect(connectedPeers.length).toBe(0);
      expect(guidedBootstrapManager.connectionAttempts.length).toBeGreaterThan(0);
      expect(guidedBootstrapManager.connectionAttempts[0].success).toBe(false);
    });
  });
  
  describe('Fallback to Network Scan', () => {
    test('should fallback to network scanning when coordinator fails', async () => {
      const mockDiscoveredPeers = [
        { id: 'scanned-peer-1', address: '192.168.1.200', port: 8000 },
        { id: 'scanned-peer-2', address: '192.168.1.201', port: 8000 }
      ];
      
      mockPeerDiscoveryManager.scanForPeers.mockResolvedValue(mockDiscoveredPeers);
      
      const result = await guidedBootstrapManager.fallbackToNetworkScan('test-wallet-address');
      
      expect(result).toEqual(mockDiscoveredPeers);
      expect(mockPeerDiscoveryManager.scanForPeers).toHaveBeenCalled();
    });
  });
  
  describe('Complete Bootstrap Process', () => {
    test('should complete guided bootstrap successfully', async () => {
      const mockNetworkMap = {
        active_nodes: 1,
        nodes: [
          {
            node_id: 'successful-node',
            public_ip: '192.168.1.100',
            port: 8000,
            last_seen: new Date().toISOString(),
            mining_active: true
          }
        ]
      };
      
      mockNetworkCoordinatorClient.getNetworkMap.mockResolvedValue(mockNetworkMap);
      mockPeerDiscoveryManager.validatePeerConnection.mockResolvedValue(true);
      mockPeerDiscoveryManager.establishConnection.mockResolvedValue({
        socket: {},
        peer: { id: 'successful-node' }
      });
      
      const result = await guidedBootstrapManager.startGuidedBootstrap('test-wallet-address');
      
      expect(result.length).toBeGreaterThan(0);
      expect(guidedBootstrapManager.isBootstrapping).toBe(false);
    });
    
    test('should fallback to scanning when coordinator guidance fails', async () => {
      const mockDiscoveredPeers = [
        { id: 'scanned-peer', address: '192.168.1.200', port: 8000 }
      ];
      
      // Coordinator fails
      mockNetworkCoordinatorClient.getNetworkMap.mockResolvedValue(null);
      
      // Network scan succeeds
      mockPeerDiscoveryManager.scanForPeers.mockResolvedValue(mockDiscoveredPeers);
      
      const result = await guidedBootstrapManager.startGuidedBootstrap('test-wallet-address');
      
      expect(result).toEqual(mockDiscoveredPeers);
      expect(mockPeerDiscoveryManager.scanForPeers).toHaveBeenCalled();
    });
  });
  
  describe('Statistics and Monitoring', () => {
    test('should provide bootstrap statistics', () => {
      // Add some connection attempts
      guidedBootstrapManager.recordConnectionAttempt('node1', '192.168.1.100', 8000, true, null, 50);
      guidedBootstrapManager.recordConnectionAttempt('node2', '192.168.1.101', 8000, false, new Error('Failed'), 100);
      
      const stats = guidedBootstrapManager.getBootstrapStats();
      
      expect(stats.totalConnectionAttempts).toBe(2);
      expect(stats.successfulConnections).toBe(1);
      expect(stats.successRate).toBe(0.5);
      expect(stats.averageLatency).toBe(50);
    });
    
    test('should track connection attempts', () => {
      const initialAttempts = guidedBootstrapManager.connectionAttempts.length;
      
      guidedBootstrapManager.recordConnectionAttempt('test-node', '192.168.1.100', 8000, true, null, 75);
      
      expect(guidedBootstrapManager.connectionAttempts.length).toBe(initialAttempts + 1);
      
      const lastAttempt = guidedBootstrapManager.connectionAttempts[guidedBootstrapManager.connectionAttempts.length - 1];
      expect(lastAttempt.nodeId).toBe('test-node');
      expect(lastAttempt.success).toBe(true);
      expect(lastAttempt.latency).toBe(75);
    });
  });
  
  describe('Cleanup and Reset', () => {
    test('should reset state correctly', () => {
      // Set some state
      guidedBootstrapManager.isBootstrapping = true;
      guidedBootstrapManager.networkMap = { active_nodes: 1 };
      guidedBootstrapManager.connectionAttempts = [{ nodeId: 'test' }];
      
      guidedBootstrapManager.reset();
      
      expect(guidedBootstrapManager.isBootstrapping).toBe(false);
      expect(guidedBootstrapManager.networkMap).toBeNull();
      expect(guidedBootstrapManager.connectionAttempts.length).toBe(0);
    });
    
    test('should cleanup resources', () => {
      const resetSpy = jest.spyOn(guidedBootstrapManager, 'reset');
      const removeListenersSpy = jest.spyOn(guidedBootstrapManager, 'removeAllListeners');
      
      guidedBootstrapManager.cleanup();
      
      expect(resetSpy).toHaveBeenCalled();
      expect(removeListenersSpy).toHaveBeenCalled();
    });
  });
});
/**
 * Guided Bootstrap Integration Tests
 * 
 * Tests the complete integration of guided bootstrap with the existing
 * bootstrap system, ensuring coordinator-guided connections work seamlessly.
 */

const { BootstrapService, BootstrapMode } = require('../BootstrapService');
const { GuidedBootstrapManager, BootstrapStrategy } = require('../GuidedBootstrapManager');

// Mock NetworkCoordinatorClient
const mockNetworkCoordinatorClient = {
  nodeId: 'integration-test-node',
  coordinatorUrl: 'https://test-coordinator.com',
  getNetworkMap: jest.fn(),
  getCurrentLocation: jest.fn().mockResolvedValue({
    latitude: 40.4168,
    longitude: -3.7038
  })
};

// Mock PeerDiscoveryManager
const mockPeerDiscoveryManager = {
  validatePeerConnection: jest.fn(),
  establishConnection: jest.fn(),
  scanForPeers: jest.fn(),
  cleanup: jest.fn(),
  removeAllListeners: jest.fn()
};

describe('Guided Bootstrap Integration', () => {
  let bootstrapService;
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Create bootstrap service with coordinator client
    bootstrapService = new BootstrapService(mockNetworkCoordinatorClient);
    
    // Replace peer discovery manager with mock
    bootstrapService.peerDiscoveryManager = mockPeerDiscoveryManager;
  });
  
  afterEach(() => {
    if (bootstrapService) {
      bootstrapService.reset();
    }
  });
  
  describe('Service Initialization', () => {
    test('should initialize with guided bootstrap when coordinator is available', () => {
      expect(bootstrapService.networkCoordinatorClient).toBe(mockNetworkCoordinatorClient);
      expect(bootstrapService.guidedBootstrapManager).toBeInstanceOf(GuidedBootstrapManager);
      expect(bootstrapService.config.preferCoordinatorGuidance).toBe(true);
    });
    
    test('should initialize without guided bootstrap when coordinator is unavailable', () => {
      const serviceWithoutCoordinator = new BootstrapService(null);
      
      expect(serviceWithoutCoordinator.networkCoordinatorClient).toBeNull();
      expect(serviceWithoutCoordinator.guidedBootstrapManager).toBeNull();
    });
    
    test('should include bootstrap strategy in state', () => {
      const state = bootstrapService.getState();
      
      expect(state.bootstrapStrategy).toBe(BootstrapStrategy.COORDINATOR_GUIDED);
    });
  });
  
  describe('Coordinator-Guided Discovery', () => {
    test('should use coordinator guidance when available', async () => {
      // Setup: Prepare wallet for discovery
      bootstrapService.onWalletAddressCreated('test-wallet-address');
      bootstrapService.onMiningReadiness('/path/to/model', { id: 'test-model' });
      
      // Mock successful coordinator guidance
      const mockNetworkMap = {
        active_nodes: 2,
        nodes: [
          {
            node_id: 'coordinator-node-1',
            public_ip: '192.168.1.100',
            port: 8000,
            last_seen: new Date().toISOString(),
            mining_active: true
          },
          {
            node_id: 'coordinator-node-2',
            public_ip: '192.168.1.101',
            port: 8000,
            last_seen: new Date().toISOString(),
            mining_active: false
          }
        ]
      };
      
      mockNetworkCoordinatorClient.getNetworkMap.mockResolvedValue(mockNetworkMap);
      mockPeerDiscoveryManager.validatePeerConnection.mockResolvedValue(true);
      mockPeerDiscoveryManager.establishConnection.mockResolvedValue({
        socket: {},
        peer: { id: 'coordinator-node-1' }
      });
      
      // Mock guided bootstrap manager
      const mockGuidedBootstrap = jest.spyOn(bootstrapService.guidedBootstrapManager, 'startGuidedBootstrap');
      mockGuidedBootstrap.mockResolvedValue([
        {
          id: 'coordinator-node-1',
          address: '192.168.1.100',
          port: 8000,
          walletAddress: 'coord-wallet-1',
          networkMode: 'testnet',
          isReady: true,
          capabilities: ['p2p-discovery', 'genesis-creation'],
          coordinatorNode: true
        }
      ]);
      
      // Start peer discovery
      await bootstrapService.startPeerDiscovery();
      
      // Verify coordinator guidance was used
      expect(mockGuidedBootstrap).toHaveBeenCalledWith(
        'test-wallet-address',
        { networkMode: 'testnet' }
      );
      
      // Verify state was updated
      const state = bootstrapService.getState();
      expect(state.mode).toBe(BootstrapMode.DISCOVERY);
      expect(state.bootstrapStrategy).toBe(BootstrapStrategy.COORDINATOR_GUIDED);
      expect(state.discoveredPeers.length).toBeGreaterThan(0);
    });
    
    test('should fallback to network scan when coordinator guidance fails', async () => {
      // Setup: Prepare wallet for discovery
      bootstrapService.onWalletAddressCreated('test-wallet-address');
      bootstrapService.onMiningReadiness('/path/to/model', { id: 'test-model' });
      
      // Mock coordinator guidance failure
      const mockGuidedBootstrap = jest.spyOn(bootstrapService.guidedBootstrapManager, 'startGuidedBootstrap');
      mockGuidedBootstrap.mockRejectedValue(new Error('Coordinator unavailable'));
      
      // Mock successful network scan
      const mockScanPeers = [
        {
          id: 'scanned-peer-1',
          address: '192.168.1.200',
          port: 8000,
          walletAddress: 'scan-wallet-1',
          networkMode: 'testnet',
          isReady: true,
          capabilities: ['p2p-discovery', 'genesis-creation']
        }
      ];
      
      mockPeerDiscoveryManager.scanForPeers.mockResolvedValue(mockScanPeers);
      
      // Start peer discovery
      await bootstrapService.startPeerDiscovery();
      
      // Verify fallback to network scan
      expect(mockGuidedBootstrap).toHaveBeenCalled();
      expect(mockPeerDiscoveryManager.scanForPeers).toHaveBeenCalled();
      
      // Verify state was updated with fallback strategy
      const state = bootstrapService.getState();
      expect(state.bootstrapStrategy).toBe(BootstrapStrategy.NETWORK_SCAN);
      expect(state.discoveredPeers).toEqual(mockScanPeers);
    });
  });
  
  describe('Event Integration', () => {
    test('should emit guided bootstrap events', async () => {
      const events = [];
      
      // Listen to all events
      bootstrapService.on('stateChanged', (state) => events.push({ type: 'stateChanged', data: state }));
      bootstrapService.on('peerDiscoveryStarted', () => events.push({ type: 'peerDiscoveryStarted' }));
      bootstrapService.on('peersDiscovered', (peers) => events.push({ type: 'peersDiscovered', data: peers }));
      
      // Setup guided bootstrap
      bootstrapService.onWalletAddressCreated('test-wallet-address');
      bootstrapService.onMiningReadiness('/path/to/model', { id: 'test-model' });
      
      // Mock successful guided bootstrap
      const mockGuidedBootstrap = jest.spyOn(bootstrapService.guidedBootstrapManager, 'startGuidedBootstrap');
      mockGuidedBootstrap.mockResolvedValue([
        {
          id: 'event-test-peer',
          address: '192.168.1.100',
          port: 8000,
          walletAddress: 'event-wallet',
          networkMode: 'testnet',
          isReady: true
        }
      ]);
      
      // Start discovery
      await bootstrapService.startPeerDiscovery();
      
      // Verify events were emitted
      expect(events.some(e => e.type === 'peerDiscoveryStarted')).toBe(true);
      expect(events.some(e => e.type === 'peersDiscovered')).toBe(true);
      
      const stateChanges = events.filter(e => e.type === 'stateChanged');
      expect(stateChanges.length).toBeGreaterThan(0);
      
      const finalState = stateChanges[stateChanges.length - 1].data;
      expect(finalState.mode).toBe(BootstrapMode.DISCOVERY);
    });
    
    test('should handle guided bootstrap manager events', () => {
      const guidedBootstrapManager = bootstrapService.guidedBootstrapManager;
      const events = [];
      
      // Listen to bootstrap service events
      bootstrapService.on('stateChanged', (state) => events.push({ type: 'stateChanged', data: state }));
      
      // Simulate guided bootstrap events
      guidedBootstrapManager.emit('bootstrapPhaseChanged', 'fetching_network_map');
      guidedBootstrapManager.emit('networkMapUpdated', { active_nodes: 3 });
      guidedBootstrapManager.emit('nodeConnected', {
        id: 'connected-node',
        address: '192.168.1.100',
        port: 8000
      }, 'coordinator');
      
      // Verify events were handled (state changes should occur)
      expect(events.length).toBeGreaterThan(0);
    });
  });
  
  describe('Statistics Integration', () => {
    test('should include guided bootstrap stats in service stats', () => {
      const stats = bootstrapService.getBootstrapStats();
      
      expect(stats.hasNetworkCoordinator).toBe(true);
      expect(stats.hasGuidedBootstrap).toBe(true);
      expect(stats.bootstrapStrategy).toBe(BootstrapStrategy.COORDINATOR_GUIDED);
      expect(stats.guidedBootstrap).toBeDefined();
    });
    
    test('should provide comprehensive bootstrap statistics', () => {
      // Add some connection attempts to guided bootstrap manager
      const guidedBootstrapManager = bootstrapService.guidedBootstrapManager;
      guidedBootstrapManager.recordConnectionAttempt('node1', '192.168.1.100', 8000, true, null, 50);
      guidedBootstrapManager.recordConnectionAttempt('node2', '192.168.1.101', 8000, false, new Error('Failed'), 100);
      
      const stats = bootstrapService.getBootstrapStats();
      
      expect(stats.guidedBootstrap.totalConnectionAttempts).toBe(2);
      expect(stats.guidedBootstrap.successfulConnections).toBe(1);
      expect(stats.guidedBootstrap.successRate).toBe(0.5);
      expect(stats.guidedBootstrap.averageLatency).toBe(50);
    });
  });
  
  describe('Error Handling Integration', () => {
    test('should handle guided bootstrap errors gracefully', async () => {
      const errors = [];
      bootstrapService.on('error', (error) => errors.push(error));
      
      // Setup for discovery
      bootstrapService.onWalletAddressCreated('test-wallet-address');
      bootstrapService.onMiningReadiness('/path/to/model', { id: 'test-model' });
      
      // Mock complete failure (both coordinator and scan fail)
      const mockGuidedBootstrap = jest.spyOn(bootstrapService.guidedBootstrapManager, 'startGuidedBootstrap');
      mockGuidedBootstrap.mockRejectedValue(new Error('Coordinator completely unavailable'));
      mockPeerDiscoveryManager.scanForPeers.mockRejectedValue(new Error('Network scan failed'));
      
      // Attempt discovery (should fail gracefully)
      try {
        await bootstrapService.startPeerDiscovery();
      } catch (error) {
        // Expected to fail
      }
      
      // Verify error was handled
      expect(errors.length).toBeGreaterThan(0);
      expect(errors[0].type).toBeDefined();
      expect(errors[0].message).toBeDefined();
    });
  });
  
  describe('Cleanup Integration', () => {
    test('should cleanup guided bootstrap manager on reset', () => {
      const guidedBootstrapManager = bootstrapService.guidedBootstrapManager;
      const cleanupSpy = jest.spyOn(guidedBootstrapManager, 'cleanup');
      
      bootstrapService.reset();
      
      expect(cleanupSpy).toHaveBeenCalled();
    });
    
    test('should maintain service integrity after reset', () => {
      // Set some state
      bootstrapService.setState({
        mode: BootstrapMode.DISCOVERY,
        discoveredPeers: [{ id: 'test-peer' }]
      });
      
      // Reset
      bootstrapService.reset();
      
      // Verify clean state
      const state = bootstrapService.getState();
      expect(state.mode).toBe(BootstrapMode.PIONEER);
      expect(state.discoveredPeers.length).toBe(0);
      expect(state.bootstrapStrategy).toBe(BootstrapStrategy.COORDINATOR_GUIDED);
      
      // Verify guided bootstrap manager is still available
      expect(bootstrapService.guidedBootstrapManager).toBeInstanceOf(GuidedBootstrapManager);
    });
  });
});
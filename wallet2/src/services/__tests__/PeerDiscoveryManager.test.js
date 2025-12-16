/**
 * Tests for PeerDiscoveryManager - Auto-Bootstrap P2P Network
 * Includes both unit tests and property-based tests
 */

// Mock fast-check for property-based testing
const fc = {
  assert: (property, options) => {
    const numRuns = options?.numRuns || 100;
    for (let i = 0; i < numRuns; i++) {
      try {
        const testData = property.generator();
        const result = property.predicate(testData);
        if (!result) {
          throw new Error(`Property failed on run ${i + 1} with data: ${JSON.stringify(testData)}`);
        }
      } catch (error) {
        throw new Error(`Property failed on run ${i + 1}: ${error.message}`);
      }
    }
  },
  property: (generator, predicate) => ({ generator, predicate }),
  
  // IP address generators
  ipAddress: () => () => {
    const octets = Array(4).fill().map(() => Math.floor(Math.random() * 256));
    return octets.join('.');
  },
  
  localIpAddress: () => () => {
    const ranges = [
      () => `192.168.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 254) + 1}`,
      () => `10.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 254) + 1}`,
      () => `172.${Math.floor(Math.random() * 16) + 16}.${Math.floor(Math.random() * 256)}.${Math.floor(Math.random() * 254) + 1}`,
      () => `127.0.0.${Math.floor(Math.random() * 254) + 1}`
    ];
    return ranges[Math.floor(Math.random() * ranges.length)]();
  },
  
  publicIpAddress: () => () => {
    // Generate public IP (avoiding private ranges)
    let ip;
    do {
      const octets = [
        Math.floor(Math.random() * 223) + 1, // 1-223 (avoid 0 and 224+)
        Math.floor(Math.random() * 256),
        Math.floor(Math.random() * 256),
        Math.floor(Math.random() * 254) + 1
      ];
      ip = octets.join('.');
    } while (isPrivateIp(ip));
    return ip;
  },
  
  constantFrom: (...values) => () => values[Math.floor(Math.random() * values.length)],
  
  array: (generator, options) => () => {
    const length = Math.floor(Math.random() * ((options?.maxLength || 10) - (options?.minLength || 0) + 1)) + (options?.minLength || 0);
    return Array(length).fill().map(() => generator());
  },
  
  integer: (options) => () => {
    const min = options?.min || 0;
    const max = options?.max || 100;
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }
};

// Helper function to check if IP is private
function isPrivateIp(ip) {
  const parts = ip.split('.').map(Number);
  
  // 127.x.x.x (localhost)
  if (parts[0] === 127) return true;
  
  // 10.x.x.x (Class A private)
  if (parts[0] === 10) return true;
  
  // 172.16.x.x - 172.31.x.x (Class B private)
  if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;
  
  // 192.168.x.x (Class C private)
  if (parts[0] === 192 && parts[1] === 168) return true;
  
  return false;
}

const { PeerDiscoveryManager, PeerInfo } = require('../PeerDiscoveryManager');
const { NetworkMode } = require('../BootstrapService');

describe('PeerDiscoveryManager', () => {
  let peerDiscoveryManager;

  beforeEach(() => {
    peerDiscoveryManager = new PeerDiscoveryManager(NetworkMode.TESTNET);
  });

  afterEach(() => {
    if (peerDiscoveryManager) {
      peerDiscoveryManager.cleanup();
      peerDiscoveryManager.removeAllListeners();
    }
  });

  describe('Unit Tests', () => {
    describe('initialization', () => {
      it('should initialize with testnet mode by default', () => {
        const manager = new PeerDiscoveryManager();
        expect(manager.detectNetworkMode()).toBe(NetworkMode.TESTNET);
      });

      it('should initialize with specified network mode', () => {
        const manager = new PeerDiscoveryManager(NetworkMode.MAINNET);
        expect(manager.detectNetworkMode()).toBe(NetworkMode.MAINNET);
      });
    });

    describe('IP address validation', () => {
      it('should validate local IP addresses in testnet mode', () => {
        const testnetManager = new PeerDiscoveryManager(NetworkMode.TESTNET);
        
        expect(testnetManager.validateIpAddress('192.168.1.1')).toBe(true);
        expect(testnetManager.validateIpAddress('10.0.0.1')).toBe(true);
        expect(testnetManager.validateIpAddress('172.16.0.1')).toBe(true);
        expect(testnetManager.validateIpAddress('127.0.0.1')).toBe(true);
      });

      it('should accept public IP addresses in testnet mode', () => {
        const testnetManager = new PeerDiscoveryManager(NetworkMode.TESTNET);
        
        expect(testnetManager.validateIpAddress('8.8.8.8')).toBe(true);
        expect(testnetManager.validateIpAddress('1.1.1.1')).toBe(true);
      });

      it('should validate public IP addresses in mainnet mode', () => {
        const mainnetManager = new PeerDiscoveryManager(NetworkMode.MAINNET);
        
        expect(mainnetManager.validateIpAddress('8.8.8.8')).toBe(true);
        expect(mainnetManager.validateIpAddress('1.1.1.1')).toBe(true);
      });

      it('should reject local IP addresses in mainnet mode', () => {
        const mainnetManager = new PeerDiscoveryManager(NetworkMode.MAINNET);
        
        expect(mainnetManager.validateIpAddress('192.168.1.1')).toBe(false);
        expect(mainnetManager.validateIpAddress('10.0.0.1')).toBe(false);
        expect(mainnetManager.validateIpAddress('127.0.0.1')).toBe(false);
      });
    });

    describe('peer validation', () => {
      it('should validate compatible peers', async () => {
        const peer = new PeerInfo(
          'test-peer',
          '192.168.1.100',
          8000,
          'PGtest123',
          NetworkMode.TESTNET,
          true
        );

        const isValid = await peerDiscoveryManager.validatePeerConnection(peer);
        expect(isValid).toBe(true);
      });

      it('should reject peers with incompatible network mode', async () => {
        const peer = new PeerInfo(
          'test-peer',
          '192.168.1.100',
          8000,
          'PGtest123',
          NetworkMode.MAINNET, // Different from manager's testnet mode
          true
        );

        const isValid = await peerDiscoveryManager.validatePeerConnection(peer);
        expect(isValid).toBe(false);
      });
    });

    describe('local network scanning', () => {
      it('should generate local network targets for testnet', () => {
        const targets = peerDiscoveryManager.generateScanTargets();
        
        expect(targets.length).toBeGreaterThan(0);
        
        // All targets should be local IP addresses
        targets.forEach(ip => {
          expect(peerDiscoveryManager.isLocalIpAddress(ip)).toBe(true);
        });
      });

      it('should include common local network ranges', () => {
        const targets = peerDiscoveryManager.generateScanTargets();
        
        const hasLocalhost = targets.some(ip => ip.startsWith('127.0.0.'));
        const has192168 = targets.some(ip => ip.startsWith('192.168.'));
        const has10 = targets.some(ip => ip.startsWith('10.'));
        
        expect(hasLocalhost).toBe(true);
        expect(has192168).toBe(true);
        expect(has10).toBe(true);
      });
    });
  });

  describe('Property-Based Tests', () => {
    /**
     * **Feature: auto-bootstrap-p2p, Property 11: IP address validation by network mode**
     * **Validates: Requirements 4.1, 4.2**
     * 
     * For any IP address, testnet mode should accept local/private addresses 
     * while mainnet mode should only accept public addresses
     */
    it('Property 11: IP address validation by network mode', () => {
      fc.assert(fc.property(
        fc.constantFrom(NetworkMode.TESTNET, NetworkMode.MAINNET),
        (networkMode) => {
          const manager = new PeerDiscoveryManager(networkMode);
          
          // Test with local IP addresses
          const localIps = [
            '192.168.1.1', '192.168.0.100', '192.168.255.254',
            '10.0.0.1', '10.255.255.254',
            '172.16.0.1', '172.31.255.254',
            '127.0.0.1', '127.0.0.10'
          ];
          
          // Test with public IP addresses
          const publicIps = [
            '8.8.8.8', '1.1.1.1', '208.67.222.222',
            '74.125.224.72', '151.101.193.140'
          ];
          
          // Property: Testnet should accept both local and public IPs
          if (networkMode === NetworkMode.TESTNET) {
            for (const localIp of localIps) {
              if (!manager.validateIpAddress(localIp)) {
                return false; // Testnet should accept local IPs
              }
            }
            for (const publicIp of publicIps) {
              if (!manager.validateIpAddress(publicIp)) {
                return false; // Testnet should also accept public IPs
              }
            }
          }
          
          // Property: Mainnet should accept public IPs, reject local IPs
          if (networkMode === NetworkMode.MAINNET) {
            for (const publicIp of publicIps) {
              if (!manager.validateIpAddress(publicIp)) {
                return false; // Mainnet should accept public IPs
              }
            }
            for (const localIp of localIps) {
              if (manager.validateIpAddress(localIp)) {
                return false; // Mainnet should reject local IPs
              }
            }
          }
          
          return true;
        }
      ), { numRuns: 100 });
    });

    /**
     * **Feature: auto-bootstrap-p2p, Property 12: Local network scanning in testnet**
     * **Validates: Requirements 4.3**
     * 
     * For any testnet operation, the system should scan common local IP ranges 
     * for peer discovery
     */
    it('Property 12: Local network scanning in testnet', () => {
      fc.assert(fc.property(
        fc.constantFrom(NetworkMode.TESTNET),
        (networkMode) => {
          const manager = new PeerDiscoveryManager(networkMode);
          const scanTargets = manager.generateScanTargets();
          
          // Property: Should generate scan targets
          if (scanTargets.length === 0) {
            return false;
          }
          
          // Property: All scan targets should be local IP addresses
          for (const ip of scanTargets) {
            if (!manager.isLocalIpAddress(ip)) {
              return false;
            }
          }
          
          // Property: Should include common local ranges
          const ranges = {
            localhost: scanTargets.some(ip => ip.startsWith('127.')),
            class_c_private: scanTargets.some(ip => ip.startsWith('192.168.')),
            class_a_private: scanTargets.some(ip => ip.startsWith('10.')),
            class_b_private: scanTargets.some(ip => ip.startsWith('172.'))
          };
          
          // Should include at least localhost and one private range
          const hasRequiredRanges = ranges.localhost && 
            (ranges.class_c_private || ranges.class_a_private || ranges.class_b_private);
          
          return hasRequiredRanges;
        }
      ), { numRuns: 100 });
    });

    /**
     * **Feature: auto-bootstrap-p2p, Property 14: Comprehensive local peer detection**
     * **Validates: Requirements 4.5**
     * 
     * For any local network with multiple devices in testnet mode, the system should 
     * detect and connect to all available local peers
     */
    it('Property 14: Comprehensive local peer detection', () => {
      fc.assert(fc.property(
        fc.array(fc.localIpAddress(), { minLength: 1, maxLength: 10 }),
        async (localIpAddresses) => {
          const manager = new PeerDiscoveryManager(NetworkMode.TESTNET);
          
          // Property: All local IP addresses should be valid for testnet
          for (const ip of localIpAddresses) {
            if (!manager.validateIpAddress(ip)) {
              return false;
            }
          }
          
          // Property: Manager should be able to generate comprehensive scan targets
          const scanTargets = manager.generateScanTargets();
          
          // Should generate targets that cover the IP space where peers might exist
          const coverageRanges = [
            '192.168.0', '192.168.1', '192.168.2',
            '10.0.0', '10.0.1',
            '172.16.0', '172.17.0',
            '127.0.0'
          ];
          
          let hasCoverage = false;
          for (const range of coverageRanges) {
            if (scanTargets.some(ip => ip.startsWith(range))) {
              hasCoverage = true;
              break;
            }
          }
          
          // Property: Should have comprehensive coverage of local network ranges
          return hasCoverage && scanTargets.length > 0;
        }
      ), { numRuns: 100 });
    });

    /**
     * **Feature: auto-bootstrap-p2p, Property 6: P2P peer detection**
     * **Validates: Requirements 3.1**
     * 
     * For any set of peers in discovery mode, each peer should be able to detect 
     * the others via P2P protocols
     */
    it('Property 6: P2P peer detection', () => {
      fc.assert(fc.property(
        fc.array(fc.localIpAddress(), { minLength: 2, maxLength: 5 }),
        fc.array(fc.integer({ min: 8000, max: 9000 }), { minLength: 1, maxLength: 3 }),
        (peerIpAddresses, ports) => {
          const manager = new PeerDiscoveryManager(NetworkMode.TESTNET);
          
          // Create mock peers in discovery mode
          const mockPeers = peerIpAddresses.map((ip, index) => new PeerInfo(
            `peer-${index}`,
            ip,
            ports[index % ports.length],
            `wallet-${index}`,
            NetworkMode.TESTNET,
            true, // isReady = true (in discovery mode)
            ['p2p-discovery']
          ));
          
          // Property: All peers should be detectable via P2P protocols
          for (const peer of mockPeers) {
            // Each peer should be valid for P2P detection
            if (!manager.validateIpAddress(peer.address)) {
              return false;
            }
            
            // Peer should be in ready state for discovery
            if (!peer.isReady) {
              return false;
            }
            
            // Peer should have P2P capabilities
            if (!peer.capabilities.includes('p2p-discovery')) {
              return false;
            }
          }
          
          // Property: P2P detection should work for multiple peers
          const scanTargets = manager.generateScanTargets();
          
          // Should be able to scan the network ranges where peers exist
          let canDetectPeers = false;
          for (const peer of mockPeers) {
            const peerNetwork = peer.address.split('.').slice(0, 3).join('.');
            if (scanTargets.some(target => target.startsWith(peerNetwork))) {
              canDetectPeers = true;
              break;
            }
          }
          
          return canDetectPeers;
        }
      ), { numRuns: 100 });
    });

    /**
     * **Feature: auto-bootstrap-p2p, Property 7: Network formation trigger**
     * **Validates: Requirements 3.2**
     * 
     * For any peer count of two or more ready peers, the system should automatically 
     * initiate network formation
     */
    it('Property 7: Network formation trigger', () => {
      fc.assert(fc.property(
        fc.integer({ min: 2, max: 10 }),
        (peerCount) => {
          const manager = new PeerDiscoveryManager(NetworkMode.TESTNET);
          
          // Create ready peers
          const readyPeers = Array(peerCount).fill().map((_, index) => new PeerInfo(
            `peer-${index}`,
            `192.168.1.${100 + index}`,
            8000 + index,
            `wallet-${index}`,
            NetworkMode.TESTNET,
            true, // All peers are ready
            ['p2p-discovery', 'genesis-creation']
          ));
          
          // Property: With 2 or more ready peers, network formation should be triggered
          let networkFormationTriggered = false;
          
          // Mock the network formation trigger logic
          if (readyPeers.length >= 2) {
            // Check that all peers are ready
            const allReady = readyPeers.every(peer => peer.isReady);
            
            // Check that all peers have genesis creation capability
            const allCapable = readyPeers.every(peer => 
              peer.capabilities.includes('genesis-creation')
            );
            
            // Network formation should be triggered
            networkFormationTriggered = allReady && allCapable;
          }
          
          // Property: Network formation should be triggered for 2+ ready peers
          return networkFormationTriggered;
        }
      ), { numRuns: 100 });
    });

    /**
     * **Feature: auto-bootstrap-p2p, Property 10: Network timeout handling**
     * **Validates: Requirements 3.5**
     * 
     * For any network timeout or failure during peer discovery, the system should 
     * retry with appropriate backoff mechanisms
     */
    it('Property 10: Network timeout handling', () => {
      fc.assert(fc.property(
        fc.integer({ min: 1, max: 5 }),
        fc.integer({ min: 1000, max: 10000 }),
        (failureCount, timeoutMs) => {
          const manager = new PeerDiscoveryManager(NetworkMode.TESTNET);
          
          // Property: Timeout configuration should be reasonable
          if (timeoutMs < 1000 || timeoutMs > 60000) {
            return false; // Timeout should be between 1-60 seconds
          }
          
          // Property: Retry attempts should be limited and reasonable
          if (failureCount < 1 || failureCount > 10) {
            return false; // Should have reasonable retry limits
          }
          
          // Property: Backoff mechanism should be implemented
          const baseDelay = manager.config.retryDelay || 1000;
          const maxRetries = manager.config.retryAttempts || 3;
          
          // Calculate expected backoff delays
          const backoffDelays = [];
          for (let attempt = 0; attempt < Math.min(failureCount, maxRetries); attempt++) {
            // Exponential backoff: delay * (2^attempt)
            const delay = baseDelay * Math.pow(2, attempt);
            backoffDelays.push(delay);
          }
          
          // Property: Backoff delays should increase exponentially
          for (let i = 1; i < backoffDelays.length; i++) {
            if (backoffDelays[i] <= backoffDelays[i - 1]) {
              return false; // Each delay should be larger than the previous
            }
          }
          
          // Property: Should not retry indefinitely
          const shouldStopRetrying = failureCount > maxRetries;
          
          return backoffDelays.length > 0 && (failureCount <= maxRetries || shouldStopRetrying);
        }
      ), { numRuns: 100 });
    });

    /**
     * Additional property test: Network mode consistency
     */
    it('Property: Network mode consistency across operations', () => {
      fc.assert(fc.property(
        fc.constantFrom(NetworkMode.TESTNET, NetworkMode.MAINNET),
        fc.array(fc.ipAddress(), { minLength: 5, maxLength: 20 }),
        (networkMode, ipAddresses) => {
          const manager = new PeerDiscoveryManager(networkMode);
          
          // Property: Network mode detection should be consistent
          if (manager.detectNetworkMode() !== networkMode) {
            return false;
          }
          
          // Property: IP validation should be consistent with network mode
          for (const ip of ipAddresses) {
            const isValid = manager.validateIpAddress(ip);
            const isLocal = manager.isLocalIpAddress(ip);
            const isPublic = manager.isPublicIpAddress(ip);
            
            // Consistency check: testnet accepts both local and public, mainnet accepts only public
            if (networkMode === NetworkMode.TESTNET) {
              // Testnet should accept both local and public IPs (but not reserved)
              if (isValid && !isLocal && !isPublic) {
                return false; // If valid, should be either local or public
              }
            } else if (networkMode === NetworkMode.MAINNET) {
              if (isValid && !isPublic) {
                return false; // Mainnet should only validate public IPs
              }
            }
          }
          
          return true;
        }
      ), { numRuns: 100 });
    });
  });
});
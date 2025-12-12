/**
 * Tests for UserFeedbackManager - Real-time status updates for auto-bootstrap
 * Includes both unit tests and property-based tests
 */

// Mock fast-check for property-based testing
const fc = {
  assert: (property, options) => {
    // Run the property multiple times with generated data
    for (let i = 0; i < (options?.numRuns || 100); i++) {
      try {
        const testData = property.generator();
        property.predicate(testData);
      } catch (error) {
        throw new Error(`Property failed on run ${i + 1}: ${error.message}`);
      }
    }
  },
  property: (generator, predicate) => ({ generator, predicate }),
  record: (obj) => () => {
    const result = {};
    for (const [key, gen] of Object.entries(obj)) {
      result[key] = typeof gen === 'function' ? gen() : gen;
    }
    return result;
  },
  integer: (opts = {}) => () => {
    const min = opts.min || 0;
    const max = opts.max || 100;
    return Math.floor(Math.random() * (max - min + 1)) + min;
  },
  string: (opts = {}) => () => {
    const length = opts.minLength || 5;
    return 'test-' + Math.random().toString(36).substring(2, 2 + length);
  },
  array: (gen, opts = {}) => () => {
    const length = Math.max(opts.minLength || 0, Math.floor(Math.random() * (opts.maxLength || 5)));
    return Array(length).fill().map(() => typeof gen === 'function' ? gen() : gen);
  },
  constantFrom: (...values) => () => values[Math.floor(Math.random() * values.length)]
};

const { UserFeedbackManager, ProgressType, AnimationState } = require('../UserFeedbackManager');

describe('UserFeedbackManager', () => {
  let feedbackManager;

  beforeEach(() => {
    feedbackManager = new UserFeedbackManager();
  });

  afterEach(() => {
    if (feedbackManager) {
      feedbackManager.removeAllListeners();
      feedbackManager.clearProgress();
    }
  });

  describe('Unit Tests', () => {
    describe('initialization', () => {
      it('should initialize with empty state', () => {
        expect(feedbackManager.getCurrentProgress()).toBeNull();
        expect(feedbackManager.getMessageHistory()).toHaveLength(0);
        expect(feedbackManager.isProgressVisible()).toBe(false);
      });
    });

    describe('scanning progress', () => {
      it('should display scanning progress with valid data', () => {
        const progress = {
          percentage: 50,
          currentRange: '192.168.1.0/24',
          peersFound: 2,
          status: 'Scanning network...'
        };

        feedbackManager.showScanningProgress(progress);

        const currentProgress = feedbackManager.getCurrentProgress();
        expect(currentProgress).toBeTruthy();
        expect(currentProgress.type).toBe(ProgressType.SCANNING);
        expect(currentProgress.percentage).toBe(50);
        expect(currentProgress.currentRange).toBe('192.168.1.0/24');
        expect(currentProgress.peersFound).toBe(2);
      });

      it('should reject invalid scanning progress data', () => {
        const invalidProgress = {
          percentage: 'invalid',
          currentRange: null,
          peersFound: -1,
          status: 123
        };

        feedbackManager.showScanningProgress(invalidProgress);

        // Should not update progress with invalid data
        expect(feedbackManager.getCurrentProgress()).toBeNull();
      });

      it('should clamp percentage values to 0-100 range', () => {
        const progress = {
          percentage: 150, // Over 100
          currentRange: '192.168.1.0/24',
          peersFound: 1,
          status: 'Scanning...'
        };

        feedbackManager.showScanningProgress(progress);

        const currentProgress = feedbackManager.getCurrentProgress();
        expect(currentProgress.percentage).toBe(100);
      });
    });

    describe('peer discovery status', () => {
      it('should display discovery status with valid data', () => {
        const status = {
          phase: 'scanning',
          peers: [{ id: 'peer1' }, { id: 'peer2' }],
          elapsed: 5000,
          message: 'Discovering peers...'
        };

        feedbackManager.displayPeerDiscoveryStatus(status);

        const currentProgress = feedbackManager.getCurrentProgress();
        expect(currentProgress).toBeTruthy();
        expect(currentProgress.type).toBe(ProgressType.DISCOVERY);
        expect(currentProgress.phase).toBe('scanning');
        expect(currentProgress.peers).toHaveLength(2);
      });
    });

    describe('genesis creation progress', () => {
      it('should display genesis progress with valid data', () => {
        const progress = {
          phase: 'creating',
          percentage: 75,
          message: 'Creating genesis block...',
          participants: ['addr1', 'addr2']
        };

        feedbackManager.showGenesisCreationProgress(progress);

        const currentProgress = feedbackManager.getCurrentProgress();
        expect(currentProgress).toBeTruthy();
        expect(currentProgress.type).toBe(ProgressType.GENESIS);
        expect(currentProgress.phase).toBe('creating');
        expect(currentProgress.percentage).toBe(75);
      });
    });

    describe('error messages', () => {
      it('should display error messages with valid data', () => {
        const error = {
          type: 'network_timeout',
          message: 'Network connection failed',
          timestamp: new Date().toISOString(),
          state: 'discovery'
        };

        feedbackManager.displayErrorMessage(error);

        const currentProgress = feedbackManager.getCurrentProgress();
        expect(currentProgress).toBeTruthy();
        expect(currentProgress.type).toBe(ProgressType.ERROR);
        expect(currentProgress.errorType).toBe('network_timeout');
      });
    });

    describe('success messages', () => {
      it('should display success messages', () => {
        const message = 'Network established successfully!';

        feedbackManager.showSuccessMessage(message);

        const currentProgress = feedbackManager.getCurrentProgress();
        expect(currentProgress).toBeTruthy();
        expect(currentProgress.type).toBe(ProgressType.SUCCESS);
        expect(currentProgress.message).toBe(message);
      });
    });

    describe('message history', () => {
      it('should maintain message history', () => {
        const progress = {
          percentage: 25,
          currentRange: '192.168.1.0/24',
          peersFound: 1,
          status: 'Scanning...'
        };

        feedbackManager.showScanningProgress(progress);

        const history = feedbackManager.getMessageHistory();
        expect(history).toHaveLength(1);
        expect(history[0].type).toBe('info');
        expect(history[0].message).toContain('Escaneando');
      });
    });
  });

  describe('Property-Based Tests', () => {
    /**
     * **Feature: auto-bootstrap-p2p, Property 5: Scanning progress feedback**
     * **Validates: Requirements 2.6, 3.6**
     * 
     * For any peer discovery operation in progress, the system should generate 
     * status messages indicating scanning activity
     */
    it('Property 5: Scanning progress feedback', () => {
      fc.assert(fc.property(
        fc.record({
          percentage: fc.integer({ min: 0, max: 100 }),
          currentRange: fc.string({ minLength: 5 }),
          peersFound: fc.integer({ min: 0, max: 10 }),
          status: fc.string({ minLength: 3 })
        }),
        (progress) => {
          // Setup: Create fresh feedback manager
          const manager = new UserFeedbackManager();
          let progressUpdateReceived = false;
          let messageAdded = false;
          
          // Listen for events to verify feedback is generated
          manager.on('progressUpdate', (data) => {
            progressUpdateReceived = true;
          });
          
          manager.on('messageAdded', (message) => {
            messageAdded = true;
          });
          
          // Action: Show scanning progress (simulating peer discovery operation)
          manager.showScanningProgress(progress);
          
          // Property: System should generate status messages for scanning activity
          const currentProgress = manager.getCurrentProgress();
          const messageHistory = manager.getMessageHistory();
          
          // Verify progress update was generated
          expect(progressUpdateReceived).toBe(true);
          
          // Verify status message was added to history
          expect(messageAdded).toBe(true);
          expect(messageHistory.length).toBeGreaterThan(0);
          
          // Verify progress data is properly stored and accessible
          expect(currentProgress).toBeTruthy();
          expect(currentProgress.type).toBe(ProgressType.SCANNING);
          expect(currentProgress.percentage).toBe(progress.percentage);
          expect(currentProgress.currentRange).toBe(progress.currentRange);
          expect(currentProgress.peersFound).toBe(progress.peersFound);
          
          // Verify message contains scanning activity information
          const latestMessage = messageHistory[messageHistory.length - 1];
          expect(latestMessage.type).toBe('info');
          expect(latestMessage.message).toContain('Escaneando');
          expect(latestMessage.message).toContain(progress.currentRange);
          expect(latestMessage.message).toContain(progress.peersFound.toString());
          
          // Verify progress is visible when scanning is active
          expect(manager.isProgressVisible()).toBe(true);
          
          // Cleanup
          manager.removeAllListeners();
        }
      ), { numRuns: 100 });
    });

    /**
     * Additional property test: Progress data consistency
     */
    it('Property: Progress data consistency across updates', () => {
      fc.assert(fc.property(
        fc.array(fc.record({
          percentage: fc.integer({ min: 0, max: 100 }),
          currentRange: fc.string({ minLength: 5 }),
          peersFound: fc.integer({ min: 0, max: 10 }),
          status: fc.string({ minLength: 3 })
        }), { minLength: 1, maxLength: 5 }),
        (progressUpdates) => {
          const manager = new UserFeedbackManager();
          
          // Apply all progress updates
          progressUpdates.forEach(progress => {
            manager.showScanningProgress(progress);
          });
          
          // Property: Latest progress should match the last update
          const currentProgress = manager.getCurrentProgress();
          const lastUpdate = progressUpdates[progressUpdates.length - 1];
          
          expect(currentProgress.percentage).toBe(lastUpdate.percentage);
          expect(currentProgress.currentRange).toBe(lastUpdate.currentRange);
          expect(currentProgress.peersFound).toBe(lastUpdate.peersFound);
          
          // Property: Message history should contain all updates
          const messageHistory = manager.getMessageHistory();
          expect(messageHistory.length).toBe(progressUpdates.length);
          
          // Property: All messages should be info type for scanning
          messageHistory.forEach(message => {
            expect(message.type).toBe('info');
            expect(message.message).toContain('Escaneando');
          });
          
          manager.removeAllListeners();
        }
      ), { numRuns: 50 });
    });

    /**
     * Property test: Animation state consistency
     */
    it('Property: Animation states are consistent with progress', () => {
      fc.assert(fc.property(
        fc.record({
          percentage: fc.integer({ min: 0, max: 100 }),
          currentRange: fc.string({ minLength: 5 }),
          peersFound: fc.integer({ min: 0, max: 10 }),
          status: fc.string({ minLength: 3 })
        }),
        (progress) => {
          const manager = new UserFeedbackManager();
          let animationStarted = false;
          
          manager.on('animationStart', (data) => {
            animationStarted = true;
            expect(data.elementId).toBe('scanning');
            expect(data.animationState).toBe(AnimationState.ACTIVE);
          });
          
          manager.showScanningProgress(progress);
          
          // Property: Scanning progress should trigger scanning animation
          expect(animationStarted).toBe(true);
          
          const currentProgress = manager.getCurrentProgress();
          
          // Property: Animation state should match progress state
          if (progress.percentage === 0) {
            expect(currentProgress.animation).toBe(AnimationState.IDLE);
          } else if (progress.percentage === 100) {
            expect(currentProgress.animation).toBe(AnimationState.COMPLETE);
          } else {
            expect(currentProgress.animation).toBe(AnimationState.ACTIVE);
          }
          
          manager.removeAllListeners();
        }
      ), { numRuns: 50 });
    });
  });
});
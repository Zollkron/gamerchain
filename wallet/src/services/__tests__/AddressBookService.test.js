import { AddressBookService } from '../AddressBookService';

// Mock electron-store
jest.mock('electron-store', () => {
  const mockStore = {
    get: jest.fn(),
    set: jest.fn(),
    delete: jest.fn(),
    clear: jest.fn()
  };
  
  return jest.fn(() => mockStore);
});

describe('AddressBookService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    AddressBookService.store.clear();
  });

  describe('Address Management', () => {
    test('should add new address successfully', async () => {
      AddressBookService.store.get.mockReturnValue([]);
      
      const addressData = {
        address: 'PG1234567890abcdef1234567890abcdef123456',
        label: 'Test Address',
        category: 'friends',
        notes: 'Test notes'
      };
      
      const result = await AddressBookService.addAddress(addressData);
      
      expect(result.success).toBe(true);
      expect(result.address).toMatchObject({
        id: expect.any(String),
        address: addressData.address,
        label: addressData.label,
        category: addressData.category,
        notes: addressData.notes,
        createdAt: expect.any(String),
        lastUsed: null,
        usageCount: 0
      });
      
      expect(AddressBookService.store.set).toHaveBeenCalledWith('addresses', 
        expect.arrayContaining([result.address])
      );
    });

    test('should reject invalid address format', async () => {
      const addressData = {
        address: 'invalid-address',
        label: 'Test Address'
      };
      
      const result = await AddressBookService.addAddress(addressData);
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Formato de dirección inválido');
    });

    test('should reject duplicate address', async () => {
      const existingAddress = {
        id: '1',
        address: 'PG1234567890abcdef1234567890abcdef123456',
        label: 'Existing'
      };
      AddressBookService.store.get.mockReturnValue([existingAddress]);
      
      const addressData = {
        address: 'PG1234567890abcdef1234567890abcdef123456',
        label: 'Duplicate'
      };
      
      const result = await AddressBookService.addAddress(addressData);
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Esta dirección ya existe en la libreta');
    });

    test('should reject duplicate label', async () => {
      const existingAddress = {
        id: '1',
        address: 'PG1111111111111111111111111111111111111111',
        label: 'Test Label'
      };
      AddressBookService.store.get.mockReturnValue([existingAddress]);
      
      const addressData = {
        address: 'PG2222222222222222222222222222222222222222',
        label: 'Test Label' // Same label
      };
      
      const result = await AddressBookService.addAddress(addressData);
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Ya existe una dirección con esta etiqueta');
    });

    test('should update existing address', async () => {
      const existingAddresses = [{
        id: 'test-id',
        address: 'PG1234567890abcdef1234567890abcdef123456',
        label: 'Old Label',
        category: 'general',
        notes: 'Old notes'
      }];
      AddressBookService.store.get.mockReturnValue(existingAddresses);
      
      const updateData = {
        label: 'New Label',
        category: 'friends',
        notes: 'New notes'
      };
      
      const result = await AddressBookService.updateAddress('test-id', updateData);
      
      expect(result.success).toBe(true);
      expect(result.address.label).toBe('New Label');
      expect(result.address.category).toBe('friends');
      expect(result.address.notes).toBe('New notes');
      expect(result.address.updatedAt).toBeDefined();
    });

    test('should delete address', async () => {
      const existingAddresses = [
        { id: 'keep-id', address: 'PG1111', label: 'Keep' },
        { id: 'delete-id', address: 'PG2222', label: 'Delete' }
      ];
      AddressBookService.store.get.mockReturnValue(existingAddresses);
      
      const result = await AddressBookService.deleteAddress('delete-id');
      
      expect(result.success).toBe(true);
      expect(AddressBookService.store.set).toHaveBeenCalledWith('addresses', 
        [{ id: 'keep-id', address: 'PG1111', label: 'Keep' }]
      );
    });
  });

  describe('Address Retrieval', () => {
    test('should get all addresses sorted correctly', async () => {
      const addresses = [
        { 
          id: '1', 
          label: 'B Address', 
          lastUsed: null,
          category: 'general'
        },
        { 
          id: '2', 
          label: 'A Address', 
          lastUsed: '2023-01-02T00:00:00.000Z',
          category: 'general'
        },
        { 
          id: '3', 
          label: 'C Address', 
          lastUsed: '2023-01-01T00:00:00.000Z',
          category: 'general'
        }
      ];
      AddressBookService.store.get.mockReturnValue(addresses);
      
      const result = await AddressBookService.getAddresses();
      
      expect(result.success).toBe(true);
      // Should be sorted by most recently used first, then alphabetically
      expect(result.addresses[0].id).toBe('2'); // Most recent
      expect(result.addresses[1].id).toBe('3'); // Second most recent
      expect(result.addresses[2].id).toBe('1'); // Never used, alphabetical
    });

    test('should filter addresses by category', async () => {
      const addresses = [
        { id: '1', category: 'friends', label: 'Friend' },
        { id: '2', category: 'business', label: 'Business' },
        { id: '3', category: 'friends', label: 'Another Friend' }
      ];
      AddressBookService.store.get.mockReturnValue(addresses);
      
      const result = await AddressBookService.getAddresses('friends');
      
      expect(result.success).toBe(true);
      expect(result.addresses).toHaveLength(2);
      expect(result.addresses.every(addr => addr.category === 'friends')).toBe(true);
    });

    test('should search addresses by query', async () => {
      const addresses = [
        { 
          id: '1', 
          label: 'John Doe', 
          address: 'PG1111111111111111111111111111111111111111',
          notes: 'Friend from work'
        },
        { 
          id: '2', 
          label: 'Jane Smith', 
          address: 'PG2222222222222222222222222222222222222222',
          notes: 'Business contact'
        }
      ];
      AddressBookService.store.get.mockReturnValue(addresses);
      
      const result = await AddressBookService.searchAddresses('john');
      
      expect(result.success).toBe(true);
      expect(result.addresses).toHaveLength(1);
      expect(result.addresses[0].label).toBe('John Doe');
    });

    test('should get frequently used addresses', async () => {
      const addresses = [
        { id: '1', label: 'Rarely Used', usageCount: 1 },
        { id: '2', label: 'Never Used', usageCount: 0 },
        { id: '3', label: 'Most Used', usageCount: 10 },
        { id: '4', label: 'Sometimes Used', usageCount: 5 }
      ];
      AddressBookService.store.get.mockReturnValue(addresses);
      
      const result = await AddressBookService.getFrequentlyUsed(2);
      
      expect(result.success).toBe(true);
      expect(result.addresses).toHaveLength(2);
      expect(result.addresses[0].label).toBe('Most Used');
      expect(result.addresses[1].label).toBe('Sometimes Used');
    });
  });

  describe('Usage Tracking', () => {
    test('should mark address as used', async () => {
      const addresses = [{
        id: '1',
        address: 'PG1234567890abcdef1234567890abcdef123456',
        label: 'Test',
        usageCount: 5,
        lastUsed: null
      }];
      AddressBookService.store.get.mockReturnValue(addresses);
      
      const result = await AddressBookService.markAddressAsUsed('PG1234567890abcdef1234567890abcdef123456');
      
      expect(result.success).toBe(true);
      expect(AddressBookService.store.set).toHaveBeenCalledWith('addresses', 
        expect.arrayContaining([
          expect.objectContaining({
            usageCount: 6,
            lastUsed: expect.any(String)
          })
        ])
      );
    });

    test('should handle marking non-existent address as used', async () => {
      AddressBookService.store.get.mockReturnValue([]);
      
      const result = await AddressBookService.markAddressAsUsed('PG9999999999999999999999999999999999999999');
      
      expect(result.success).toBe(true);
      // Should not throw error, just silently handle
    });
  });

  describe('Import/Export', () => {
    test('should export address book', async () => {
      const addresses = [
        {
          id: '1',
          address: 'PG1111111111111111111111111111111111111111',
          label: 'Test Address',
          category: 'friends',
          notes: 'Test notes',
          createdAt: '2023-01-01T00:00:00.000Z',
          usageCount: 5
        }
      ];
      AddressBookService.store.get.mockReturnValue(addresses);
      
      const result = await AddressBookService.exportAddressBook();
      
      expect(result.success).toBe(true);
      
      const exportData = JSON.parse(result.data);
      expect(exportData.version).toBe('1.0');
      expect(exportData.addresses).toHaveLength(1);
      expect(exportData.addresses[0]).toMatchObject({
        address: 'PG1111111111111111111111111111111111111111',
        label: 'Test Address',
        category: 'friends',
        notes: 'Test notes',
        createdAt: '2023-01-01T00:00:00.000Z'
      });
      // Should not include sensitive data like id, usageCount
      expect(exportData.addresses[0].id).toBeUndefined();
      expect(exportData.addresses[0].usageCount).toBeUndefined();
    });

    test('should import address book with merge', async () => {
      const existingAddresses = [{
        id: 'existing',
        address: 'PG0000000000000000000000000000000000000000',
        label: 'Existing'
      }];
      AddressBookService.store.get.mockReturnValue(existingAddresses);
      
      const importData = {
        version: '1.0',
        addresses: [
          {
            address: 'PG1111111111111111111111111111111111111111',
            label: 'Imported Address',
            category: 'general',
            notes: 'Imported'
          }
        ]
      };
      
      const result = await AddressBookService.importAddressBook(JSON.stringify(importData), true);
      
      expect(result.success).toBe(true);
      expect(result.imported).toBe(1);
      expect(result.skipped).toBe(0);
      
      expect(AddressBookService.store.set).toHaveBeenCalledWith('addresses', 
        expect.arrayContaining([
          expect.objectContaining({ label: 'Existing' }),
          expect.objectContaining({ 
            label: 'Imported Address',
            imported: true
          })
        ])
      );
    });

    test('should skip duplicate addresses during import', async () => {
      const existingAddresses = [{
        id: 'existing',
        address: 'PG1111111111111111111111111111111111111111',
        label: 'Existing'
      }];
      AddressBookService.store.get.mockReturnValue(existingAddresses);
      
      const importData = {
        version: '1.0',
        addresses: [
          {
            address: 'PG1111111111111111111111111111111111111111', // Duplicate address
            label: 'Duplicate Address',
            category: 'general'
          },
          {
            address: 'PG2222222222222222222222222222222222222222',
            label: 'Existing', // Duplicate label
            category: 'general'
          }
        ]
      };
      
      const result = await AddressBookService.importAddressBook(JSON.stringify(importData), true);
      
      expect(result.success).toBe(true);
      expect(result.imported).toBe(0);
      expect(result.skipped).toBe(2);
    });
  });

  describe('Validation', () => {
    test('should validate correct PlayerGold address format', () => {
      const validAddress = 'PG1234567890abcdef1234567890abcdef123456';
      
      const isValid = AddressBookService.isValidAddress(validAddress);
      
      expect(isValid).toBe(true);
    });

    test('should reject invalid address formats', () => {
      const invalidAddresses = [
        'invalid-address',
        'PG123', // Too short
        'BTC1234567890abcdef1234567890abcdef123456', // Wrong prefix
        'PG1234567890abcdef1234567890abcdef12345g', // Invalid character
        'PG1234567890abcdef1234567890abcdef1234567' // Too long
      ];
      
      invalidAddresses.forEach(address => {
        expect(AddressBookService.isValidAddress(address)).toBe(false);
      });
    });
  });

  describe('Statistics', () => {
    test('should calculate address book statistics', () => {
      const weekAgo = new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString();
      const addresses = [
        { 
          id: '1', 
          category: 'friends', 
          usageCount: 10,
          createdAt: weekAgo
        },
        { 
          id: '2', 
          category: 'friends', 
          usageCount: 5,
          createdAt: '2023-01-01T00:00:00.000Z'
        },
        { 
          id: '3', 
          category: 'business', 
          usageCount: 15,
          createdAt: weekAgo
        }
      ];
      AddressBookService.store.get.mockReturnValue(addresses);
      
      const stats = AddressBookService.getStatistics();
      
      expect(stats.totalAddresses).toBe(3);
      expect(stats.categoryCounts.friends).toBe(2);
      expect(stats.categoryCounts.business).toBe(1);
      expect(stats.mostUsedAddress.usageCount).toBe(15);
      expect(stats.recentlyAdded).toBe(2); // Added in last 7 days
    });
  });

  describe('Categories', () => {
    test('should return predefined categories', () => {
      const categories = AddressBookService.getCategories();
      
      expect(categories).toEqual(expect.arrayContaining([
        { value: 'general', label: 'General' },
        { value: 'friends', label: 'Amigos' },
        { value: 'family', label: 'Familia' },
        { value: 'business', label: 'Negocios' },
        { value: 'gaming', label: 'Gaming' },
        { value: 'exchanges', label: 'Exchanges' },
        { value: 'services', label: 'Servicios' },
        { value: 'other', label: 'Otros' }
      ]));
    });
  });
});
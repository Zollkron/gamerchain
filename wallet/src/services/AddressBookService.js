import crypto from 'crypto';
import Store from 'electron-store';

class AddressBookService {
  constructor() {
    this.store = new Store({
      name: 'playergold-addressbook',
      encryptionKey: 'playergold-addressbook-key'
    });
  }

  /**
   * Add new address to address book
   * @param {Object} addressData - Address information
   * @returns {Object} Add result
   */
  async addAddress(addressData) {
    try {
      const { address, label, category = 'general', notes = '' } = addressData;

      if (!address || !label) {
        throw new Error('Dirección y etiqueta son requeridas');
      }

      // Validate address format (simplified validation)
      if (!this.isValidAddress(address)) {
        throw new Error('Formato de dirección inválido');
      }

      const addresses = this.store.get('addresses', []);
      
      // Check if address already exists
      const existingAddress = addresses.find(addr => addr.address === address);
      if (existingAddress) {
        throw new Error('Esta dirección ya existe en la libreta');
      }

      // Check if label already exists
      const existingLabel = addresses.find(addr => addr.label.toLowerCase() === label.toLowerCase());
      if (existingLabel) {
        throw new Error('Ya existe una dirección con esta etiqueta');
      }

      const newAddress = {
        id: crypto.randomUUID(),
        address: address,
        label: label.trim(),
        category: category,
        notes: notes.trim(),
        createdAt: new Date().toISOString(),
        lastUsed: null,
        usageCount: 0
      };

      addresses.push(newAddress);
      this.store.set('addresses', addresses);

      return {
        success: true,
        address: newAddress
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Update existing address
   * @param {string} addressId - Address ID
   * @param {Object} updateData - Updated address data
   * @returns {Object} Update result
   */
  async updateAddress(addressId, updateData) {
    try {
      const addresses = this.store.get('addresses', []);
      const addressIndex = addresses.findIndex(addr => addr.id === addressId);

      if (addressIndex === -1) {
        throw new Error('Dirección no encontrada');
      }

      const { label, category, notes } = updateData;

      // Check if new label conflicts with existing ones (excluding current)
      if (label) {
        const existingLabel = addresses.find(
          (addr, index) => index !== addressIndex && addr.label.toLowerCase() === label.toLowerCase()
        );
        if (existingLabel) {
          throw new Error('Ya existe una dirección con esta etiqueta');
        }
      }

      // Update address
      addresses[addressIndex] = {
        ...addresses[addressIndex],
        ...(label && { label: label.trim() }),
        ...(category && { category }),
        ...(notes !== undefined && { notes: notes.trim() }),
        updatedAt: new Date().toISOString()
      };

      this.store.set('addresses', addresses);

      return {
        success: true,
        address: addresses[addressIndex]
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Delete address from address book
   * @param {string} addressId - Address ID
   * @returns {Object} Delete result
   */
  async deleteAddress(addressId) {
    try {
      const addresses = this.store.get('addresses', []);
      const filteredAddresses = addresses.filter(addr => addr.id !== addressId);

      if (addresses.length === filteredAddresses.length) {
        throw new Error('Dirección no encontrada');
      }

      this.store.set('addresses', filteredAddresses);

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get all addresses from address book
   * @param {string} category - Filter by category (optional)
   * @returns {Object} Addresses list
   */
  async getAddresses(category = null) {
    try {
      let addresses = this.store.get('addresses', []);

      if (category) {
        addresses = addresses.filter(addr => addr.category === category);
      }

      // Sort by most recently used, then by label
      addresses.sort((a, b) => {
        if (a.lastUsed && b.lastUsed) {
          return new Date(b.lastUsed) - new Date(a.lastUsed);
        }
        if (a.lastUsed && !b.lastUsed) return -1;
        if (!a.lastUsed && b.lastUsed) return 1;
        return a.label.localeCompare(b.label);
      });

      return {
        success: true,
        addresses: addresses
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        addresses: []
      };
    }
  }

  /**
   * Search addresses by label or address
   * @param {string} query - Search query
   * @returns {Object} Search results
   */
  async searchAddresses(query) {
    try {
      const addresses = this.store.get('addresses', []);
      const searchQuery = query.toLowerCase().trim();

      const filteredAddresses = addresses.filter(addr => 
        addr.label.toLowerCase().includes(searchQuery) ||
        addr.address.toLowerCase().includes(searchQuery) ||
        addr.notes.toLowerCase().includes(searchQuery)
      );

      return {
        success: true,
        addresses: filteredAddresses
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        addresses: []
      };
    }
  }

  /**
   * Get address by ID
   * @param {string} addressId - Address ID
   * @returns {Object} Address data
   */
  async getAddressById(addressId) {
    try {
      const addresses = this.store.get('addresses', []);
      const address = addresses.find(addr => addr.id === addressId);

      if (!address) {
        throw new Error('Dirección no encontrada');
      }

      return {
        success: true,
        address: address
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get address by address string
   * @param {string} addressString - Address string
   * @returns {Object} Address data
   */
  async getAddressByString(addressString) {
    try {
      const addresses = this.store.get('addresses', []);
      const address = addresses.find(addr => addr.address === addressString);

      return {
        success: true,
        address: address || null
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Mark address as used (for usage tracking)
   * @param {string} addressString - Address that was used
   * @returns {Object} Update result
   */
  async markAddressAsUsed(addressString) {
    try {
      const addresses = this.store.get('addresses', []);
      const addressIndex = addresses.findIndex(addr => addr.address === addressString);

      if (addressIndex !== -1) {
        addresses[addressIndex].lastUsed = new Date().toISOString();
        addresses[addressIndex].usageCount = (addresses[addressIndex].usageCount || 0) + 1;
        this.store.set('addresses', addresses);
      }

      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get available categories
   * @returns {Array} List of categories
   */
  getCategories() {
    return [
      { value: 'general', label: 'General' },
      { value: 'friends', label: 'Amigos' },
      { value: 'family', label: 'Familia' },
      { value: 'business', label: 'Negocios' },
      { value: 'gaming', label: 'Gaming' },
      { value: 'exchanges', label: 'Exchanges' },
      { value: 'services', label: 'Servicios' },
      { value: 'other', label: 'Otros' }
    ];
  }

  /**
   * Get frequently used addresses
   * @param {number} limit - Number of addresses to return
   * @returns {Object} Frequently used addresses
   */
  async getFrequentlyUsed(limit = 10) {
    try {
      const addresses = this.store.get('addresses', []);
      
      const frequentAddresses = addresses
        .filter(addr => addr.usageCount > 0)
        .sort((a, b) => b.usageCount - a.usageCount)
        .slice(0, limit);

      return {
        success: true,
        addresses: frequentAddresses
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        addresses: []
      };
    }
  }

  /**
   * Export address book to JSON
   * @returns {Object} Export result
   */
  async exportAddressBook() {
    try {
      const addresses = this.store.get('addresses', []);
      
      const exportData = {
        version: '1.0',
        exportedAt: new Date().toISOString(),
        addresses: addresses.map(addr => ({
          address: addr.address,
          label: addr.label,
          category: addr.category,
          notes: addr.notes,
          createdAt: addr.createdAt
        }))
      };

      return {
        success: true,
        data: JSON.stringify(exportData, null, 2)
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Import address book from JSON
   * @param {string} jsonData - JSON data to import
   * @param {boolean} merge - Whether to merge with existing addresses
   * @returns {Object} Import result
   */
  async importAddressBook(jsonData, merge = true) {
    try {
      const importData = JSON.parse(jsonData);
      
      if (!importData.addresses || !Array.isArray(importData.addresses)) {
        throw new Error('Formato de datos inválido');
      }

      let existingAddresses = merge ? this.store.get('addresses', []) : [];
      let importedCount = 0;
      let skippedCount = 0;

      for (const importAddr of importData.addresses) {
        // Validate required fields
        if (!importAddr.address || !importAddr.label) {
          skippedCount++;
          continue;
        }

        // Check for duplicates
        const existingAddr = existingAddresses.find(
          addr => addr.address === importAddr.address || 
                  addr.label.toLowerCase() === importAddr.label.toLowerCase()
        );

        if (existingAddr) {
          skippedCount++;
          continue;
        }

        // Add new address
        const newAddress = {
          id: crypto.randomUUID(),
          address: importAddr.address,
          label: importAddr.label,
          category: importAddr.category || 'general',
          notes: importAddr.notes || '',
          createdAt: importAddr.createdAt || new Date().toISOString(),
          lastUsed: null,
          usageCount: 0,
          imported: true
        };

        existingAddresses.push(newAddress);
        importedCount++;
      }

      this.store.set('addresses', existingAddresses);

      return {
        success: true,
        imported: importedCount,
        skipped: skippedCount,
        total: importData.addresses.length
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Validate address format
   * @param {string} address - Address to validate
   * @returns {boolean} Validation result
   */
  isValidAddress(address) {
    // PlayerGold address format: PG + 38 hex characters
    const addressRegex = /^PG[0-9a-fA-F]{38}$/;
    return addressRegex.test(address);
  }

  /**
   * Get address book statistics
   * @returns {Object} Statistics
   */
  getStatistics() {
    const addresses = this.store.get('addresses', []);
    
    const stats = {
      totalAddresses: addresses.length,
      categoryCounts: {},
      mostUsedAddress: null,
      recentlyAdded: 0
    };

    // Count by category
    addresses.forEach(addr => {
      stats.categoryCounts[addr.category] = (stats.categoryCounts[addr.category] || 0) + 1;
    });

    // Find most used address
    const mostUsed = addresses.reduce((max, addr) => 
      (addr.usageCount || 0) > (max.usageCount || 0) ? addr : max, 
      addresses[0] || null
    );
    stats.mostUsedAddress = mostUsed;

    // Count recently added (last 7 days)
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    stats.recentlyAdded = addresses.filter(
      addr => new Date(addr.createdAt) > weekAgo
    ).length;

    return stats;
  }
}

export default new AddressBookService();
import React, { useState, useEffect } from 'react';
import AddressBookService from '../services/AddressBookService';

const AddressBook = ({ onAddressSelect }) => {
  const [addresses, setAddresses] = useState([]);
  const [filteredAddresses, setFilteredAddresses] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  
  const [formData, setFormData] = useState({
    address: '',
    label: '',
    category: 'general',
    notes: ''
  });

  const categories = AddressBookService.getCategories();

  useEffect(() => {
    loadAddresses();
  }, []);

  useEffect(() => {
    filterAddresses();
  }, [addresses, searchQuery, selectedCategory]);

  const loadAddresses = async () => {
    setLoading(true);
    const result = await AddressBookService.getAddresses();
    setLoading(false);

    if (result.success) {
      setAddresses(result.addresses);
    } else {
      showMessage(result.error, 'error');
    }
  };

  const filterAddresses = () => {
    let filtered = [...addresses];

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(addr => addr.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(addr =>
        addr.label.toLowerCase().includes(query) ||
        addr.address.toLowerCase().includes(query) ||
        addr.notes.toLowerCase().includes(query)
      );
    }

    setFilteredAddresses(filtered);
  };

  const showMessage = (text, type = 'info') => {
    setMessage(text);
    setMessageType(type);
    setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
  };

  const resetForm = () => {
    setFormData({
      address: '',
      label: '',
      category: 'general',
      notes: ''
    });
    setEditingAddress(null);
    setShowAddForm(false);
  };

  const handleAddAddress = async () => {
    if (!formData.address || !formData.label) {
      showMessage('Dirección y etiqueta son requeridas', 'error');
      return;
    }

    setLoading(true);
    const result = await AddressBookService.addAddress(formData);
    setLoading(false);

    if (result.success) {
      showMessage('Dirección agregada exitosamente', 'success');
      resetForm();
      loadAddresses();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleEditAddress = (address) => {
    setFormData({
      address: address.address,
      label: address.label,
      category: address.category,
      notes: address.notes
    });
    setEditingAddress(address);
    setShowAddForm(true);
  };

  const handleUpdateAddress = async () => {
    if (!formData.label) {
      showMessage('La etiqueta es requerida', 'error');
      return;
    }

    setLoading(true);
    const result = await AddressBookService.updateAddress(editingAddress.id, {
      label: formData.label,
      category: formData.category,
      notes: formData.notes
    });
    setLoading(false);

    if (result.success) {
      showMessage('Dirección actualizada exitosamente', 'success');
      resetForm();
      loadAddresses();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleDeleteAddress = async (addressId) => {
    if (!confirm('¿Estás seguro de que quieres eliminar esta dirección?')) {
      return;
    }

    setLoading(true);
    const result = await AddressBookService.deleteAddress(addressId);
    setLoading(false);

    if (result.success) {
      showMessage('Dirección eliminada exitosamente', 'success');
      loadAddresses();
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleSelectAddress = (address) => {
    if (onAddressSelect) {
      onAddressSelect(address);
    }
    // Mark as used for tracking
    AddressBookService.markAddressAsUsed(address.address);
  };

  const handleExportAddressBook = async () => {
    const result = await AddressBookService.exportAddressBook();
    
    if (result.success) {
      // Create download link
      const blob = new Blob([result.data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `playergold-addressbook-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showMessage('Libreta de direcciones exportada', 'success');
    } else {
      showMessage(result.error, 'error');
    }
  };

  const handleImportAddressBook = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const text = await file.text();
      const result = await AddressBookService.importAddressBook(text, true);
      
      if (result.success) {
        showMessage(`Importadas ${result.imported} direcciones, ${result.skipped} omitidas`, 'success');
        loadAddresses();
      } else {
        showMessage(result.error, 'error');
      }
    } catch (error) {
      showMessage('Error al leer el archivo', 'error');
    }
    
    // Reset file input
    event.target.value = '';
  };

  const getCategoryLabel = (categoryValue) => {
    const category = categories.find(cat => cat.value === categoryValue);
    return category ? category.label : categoryValue;
  };

  const getUsageInfo = (address) => {
    if (address.usageCount > 0) {
      return `Usado ${address.usageCount} veces`;
    }
    return 'Nunca usado';
  };

  return (
    <div className="address-book">
      <div className="address-book-header">
        <h2>Libreta de Direcciones</h2>
        <div className="header-actions">
          <button 
            className="btn-primary"
            onClick={() => setShowAddForm(true)}
          >
            + Agregar Dirección
          </button>
          <div className="import-export">
            <button 
              className="btn-secondary"
              onClick={handleExportAddressBook}
            >
              📤 Exportar
            </button>
            <label className="btn-secondary">
              📥 Importar
              <input
                type="file"
                accept=".json"
                onChange={handleImportAddressBook}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        </div>
      </div>

      {message && (
        <div className={`message ${messageType}`}>
          {message}
        </div>
      )}

      {/* Search and Filter */}
      <div className="search-filters">
        <div className="search-box">
          <input
            type="text"
            placeholder="Buscar por etiqueta, dirección o notas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="category-filter">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">Todas las categorías</option>
            {categories.map(category => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Address List */}
      <div className="addresses-list">
        {loading ? (
          <div className="loading">Cargando direcciones...</div>
        ) : filteredAddresses.length > 0 ? (
          filteredAddresses.map(address => (
            <div key={address.id} className="address-item">
              <div className="address-info">
                <div className="address-header">
                  <h4>{address.label}</h4>
                  <span className="category-badge">
                    {getCategoryLabel(address.category)}
                  </span>
                </div>
                <div className="address-details">
                  <div className="address-string">
                    {address.address}
                  </div>
                  {address.notes && (
                    <div className="address-notes">
                      {address.notes}
                    </div>
                  )}
                  <div className="address-meta">
                    <span className="usage-info">
                      {getUsageInfo(address)}
                    </span>
                    <span className="created-date">
                      Agregada: {new Date(address.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>
              <div className="address-actions">
                <button
                  className="btn-action"
                  onClick={() => handleSelectAddress(address)}
                  title="Usar esta dirección"
                >
                  ✓
                </button>
                <button
                  className="btn-action"
                  onClick={() => handleEditAddress(address)}
                  title="Editar"
                >
                  ✏️
                </button>
                <button
                  className="btn-action danger"
                  onClick={() => handleDeleteAddress(address.id)}
                  title="Eliminar"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <p>No se encontraron direcciones</p>
            {!searchQuery && !selectedCategory && (
              <button 
                className="btn-primary"
                onClick={() => setShowAddForm(true)}
              >
                Agregar primera dirección
              </button>
            )}
          </div>
        )}
      </div>

      {/* Add/Edit Address Modal */}
      {showAddForm && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>
                {editingAddress ? 'Editar Dirección' : 'Agregar Nueva Dirección'}
              </h3>
              <button 
                className="close-btn"
                onClick={resetForm}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>Dirección *</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  placeholder="PG..."
                  disabled={editingAddress !== null}
                />
              </div>
              <div className="form-group">
                <label>Etiqueta *</label>
                <input
                  type="text"
                  value={formData.label}
                  onChange={(e) => setFormData({...formData, label: e.target.value})}
                  placeholder="Nombre descriptivo"
                />
              </div>
              <div className="form-group">
                <label>Categoría</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                >
                  {categories.map(category => (
                    <option key={category.value} value={category.value}>
                      {category.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Notas</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  placeholder="Notas adicionales (opcional)"
                  rows="3"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="btn-secondary"
                onClick={resetForm}
              >
                Cancelar
              </button>
              <button 
                className="btn-primary"
                onClick={editingAddress ? handleUpdateAddress : handleAddAddress}
                disabled={loading}
              >
                {loading ? 'Guardando...' : (editingAddress ? 'Actualizar' : 'Agregar')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AddressBook;